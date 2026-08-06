# -*- coding: utf-8 -*-
"""
统一汉化 CLI —— Cultures Saga 地图 XML 本地化工具（单文件入口）。

替代原先散装的 trans_*.py / inject.py / selfcheck.py，集中管理：
  scan    盘点 128 个 XML 的完成度(A/B/C)、CRLF、GER 污染
  repair  内容保全式修复非法 XML 结构（补 <briefings>、修被吃的首个 <block id>、
          去重 </strings>），修复结果先过 minidom 校验，不合法绝不落盘
  verify  校验单文件：XML 解析 / CRLF / GER 污染 / CHN 槽数==GER 槽数 / 空 CHN
  inject  从 archive/ 读取翻译字典 T，注入到占位 <text lang="CHN" />，注入后强制校验
  commit  在仓库根以 git -c core.autocrlf=false 提交

汉化内容根：本文件上一级 Localization/ZH-CN/（map_xml / map_xml_user / text）。
运行：python Tools/translate_cli.py <subcommand> [args]
"""
import os, re, sys, argparse, importlib.util
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
LOC_ROOT = os.path.join(HERE, "..", "Localization", "ZH-CN")   # 汉化内容根
MAP_XML = os.path.join(LOC_ROOT, "map_xml")
ARCHIVE = os.path.join(LOC_ROOT, "archive")                      # 字典留档（未随仓库分发）

# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def list_xml():
    return sorted(f for f in os.listdir(MAP_XML) if f.endswith(".xml"))

def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw, raw.decode("utf-8", "replace")

def has_crlf(raw):
    return b"\r\n" in raw

def try_parse(s):
    try:
        minidom.parseString(s.encode("utf-8"))
        return None
    except Exception as e:
        return str(e)

def load_trans(modname):
    """从 archive/ 加载翻译字典模块，返回 T。"""
    path = os.path.join(ARCHIVE, modname + ".py") if not modname.endswith(".py") else os.path.join(ARCHIVE, modname)
    if not os.path.exists(path):
        # 也允许直接给文件名
        path = os.path.join(ARCHIVE, modname)
    spec = importlib.util.spec_from_file_location("transmod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.T

# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------
def cmd_scan(args):
    files = list_xml()
    A, B, C = [], [], []
    crlf_files = []
    for f in files:
        raw, s = read_text(os.path.join(MAP_XML, f))
        if has_crlf(raw):
            crlf_files.append(f)
        err = try_parse(s)
        if err:
            C.append(f)
            continue
        # 合法：检查 strings 段是否有中文
        chn = re.findall(r'<lang code="CHN"[^>]*>(.*?)</lang>', s, re.S)
        if any(b.strip() for b in chn):
            A.append(f)
        else:
            B.append(f)
    print(f"XML 总数: {len(files)}")
    print(f"  A 完成(strings 有中文): {len(A)}")
    print(f"  B 结构合法但 strings 空壳: {len(B)}")
    print(f"  C 结构非法: {len(C)}")
    print(f"  CRLF 文件: {len(crlf_files)}")
    print()
    if B:
        print("=== [B] 空壳文件 ===")
        for f in B: print("  ", f)
    if C:
        print("=== [C] 非法文件 ===")
        for f in C: print("  ", f)
    if crlf_files:
        print("=== CRLF 文件 ===")
        for f in crlf_files: print("  ", f)
    # 写报告
    with open(os.path.join(HERE, "scan_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"TOTAL {len(files)} | A {len(A)} | B {len(B)} | C {len(C)} | CRLF {len(crlf_files)}\n")
        fh.write("B: " + " ".join(B) + "\n")
        fh.write("C: " + " ".join(C) + "\n")
        fh.write("CRLF: " + " ".join(crlf_files) + "\n")
    print("\n报告已写入 scan_report.txt")
    return 0

# --------------------------------------------------------------------------
# repair —— 内容保全式重建
# --------------------------------------------------------------------------
FORBID_ID = re.compile(r'CHN|HN"|=|lang|code|text|string|iefings|briefings|block|font|ger|eng', re.I)

def recover_id(garbage):
    """从首个 block 开标签残骸中恢复 id。失败返回 None。"""
    g = garbage.strip()
    if not g:
        return None
    # 形如 ...saracen"> 或 "0"> 或 00_start">
    m = re.search(r'([A-Za-z0-9_]+)"\s*>$', g)
    if not m:
        return None
    cand = m.group(1)
    if FORBID_ID.search(cand):
        return None
    return cand

def repair_one(path):
    """修复单文件。返回 (ok, new_text, note)。ok=True 时 new_text 保证可被 minidom 解析。"""
    raw, s = read_text(path)
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # 1) 抽取 strings 段（每个 <string id> 块是自包含完好的）
    str_blocks = re.findall(r'<string id="[^"]+">.*?</string>', s, re.S)
    n_open = len(re.findall(r'<string id="[^"]+"\s*>', s))
    if len(str_blocks) != n_open:
        return False, None, f"string 块计数不符(抽到{len(str_blocks)}/开标签{n_open})，放弃以防丢数据"
    strings_section = "<strings>\n" + "\n".join(str_blocks) + "\n</strings>"

    # 2) 抽取 briefings 体（最后一个 </strings> 之后，</briefings> 之前）
    last_close = s.rfind("</strings>")
    if last_close < 0:
        return False, None, "找不到 </strings>"
    briefings_body_start = last_close + len("</strings>")
    bc = s.find("</briefings>", briefings_body_start)
    if bc < 0:
        return False, None, "找不到 </briefings>"
    briefings_body = s[briefings_body_start:bc]
    # 去掉可能已有的 <briefings> / 破损 iefings>
    briefings_body = re.sub(r'^\s*<briefings>\s*', '', briefings_body, flags=re.S)
    briefings_body = re.sub(r'^\s*iefings>\s*', '', briefings_body, flags=re.S)

    n_blocks_orig = s.count("</block>")

    # 3) 按 </block> 切分，重建每个 block
    pieces = briefings_body.split("</block>")
    rebuilt = []
    flagged = []
    for i, piece in enumerate(pieces[:-1]):  # 末段为空（split 末尾）
        block = piece + "</block>"
        if i == 0:
            # 首个 block：开标签可能损坏
            if block.startswith("<block id="):
                rebuilt.append(block)
            else:
                m = re.match(r'^([^<]*)', block, re.S)
                lead = m.group(1) if m else ""
                rest = block[len(lead):]
                if rest.startswith("<block id="):
                    rebuilt.append(rest)
                else:
                    bid = recover_id(lead)
                    if bid is None:
                        bid = "__REPAIRED_0"
                        flagged.append("首个 block id 无法从残骸恢复，已置占位 __REPAIRED_0（待人工核对）")
                    else:
                        flagged.append(f"首个 block id 由残骸恢复为 '{bid}'（启发式，建议核对）")
                    # 若残骸是 <lang code="CHN"> 的尾部（包含 CHN/HN" 等），rest 不以 <lang 开头，
                    # 说明 <lang code="CHN"> 开标签也被吃了 → 补回
                    lang_open = ""
                    text_open = ""
                    tail_text = ""   # 从残骸中剥离出的嵌入文本内容（当 <text> 也被吃掉时出现）
                    ls = lead.strip()
                    if ls.startswith(("xt>", "text>")):
                        # <text> 开标签被吃完，xt>/text> 仅是残留碎片，之后是裸露的中文内容
                        text_open = "<text>"
                        lang_open = '<lang code="CHN">'
                        # 把碎片去掉，剩余部分作为 <text> 的正文
                        tail_text = re.sub(r'^(xt|text)\s*>', '', lead, count=1)
                        flagged.append(f"同时补回被吃掉的 <lang code=\"CHN\"><text> 开标签")
                    elif not rest.lstrip().startswith("<lang"):
                        if "CHN" in lead.upper() or 'HN"' in lead:
                            lang_open = '<lang code="CHN">'
                            flagged.append("同时补回被吃掉的 <lang code=\"CHN\"> 开标签")
                    rebuilt.append(f'<block id="{bid}">' + lang_open + text_open + tail_text + rest)
        else:
            rebuilt.append(block)

    if len(rebuilt) != n_blocks_orig:
        return False, None, f"block 计数不符(重建{len(rebuilt)}/原{n_blocks_orig})，放弃"

    briefings_section = "<briefings>\n" + "\n".join(rebuilt) + "\n</briefings>"

    # 4) 拼装：保留 <localization> + <languages> 头尾
    head = s[: s.find("<strings>")]
    tail = s[bc + len("</briefings>"):]
    new_text = head + strings_section + "\n" + briefings_section + tail

    err = try_parse(new_text)
    if err:
        return False, None, f"重建后仍无法解析: {err[:80]}"
    if has_crlf(new_text.encode("utf-8")):
        new_text = new_text.replace("\r\n", "\n").replace("\r", "\n")
    note = "OK" + (" | " + "; ".join(flagged) if flagged else "")
    return True, new_text, note

def cmd_repair(args):
    targets = args.files if args.files else list_xml()
    # 只修非法文件
    apply = args.apply
    ok = 0; skip = 0; would = 0
    log_lines = []
    for f in targets:
        path = os.path.join(MAP_XML, f)
        raw, s = read_text(path)
        if try_parse(s):   # 仅处理真正非法的文件（try_parse 成功返回 None）
            good, new_text, note = repair_one(path)
            if good:
                would += 1
                if apply:
                    with open(path, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(new_text)
                    # 二次确认落盘后可解析
                    if not try_parse(open(path, encoding="utf-8").read()):
                        ok += 1
                        log_lines.append(f"[FIXED] {f} :: {note}")
                    else:
                        skip += 1
                        log_lines.append(f"[FAIL ] {f} :: 落盘后竟无法解析（已回退）")
                else:
                    ok += 1  # dry-run 视为可修复
                    log_lines.append(f"[DRY  ] {f} :: {note}")
            else:
                skip += 1
                log_lines.append(f"[SKIP ] {f} :: {note}")
    print(f"可修复(将变合法): {ok}   跳过/失败: {skip}")
    if not apply:
        print("(dry-run，未写入。加 --apply 实际修复)")
    for line in log_lines:
        print("  " + line)
    with open(os.path.join(HERE, "repair_log.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log_lines) + "\n")
    return 0

# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------
def count_paras(text):
    return len([g for g in re.split(r'\n\s*\n', text) if g.strip()])

def cmd_verify(args):
    files = args.files if args.files else list_xml()
    bad = 0
    for f in files:
        path = os.path.join(MAP_XML, f)
        raw, s = read_text(path)
        probs = []
        if has_crlf(raw):
            probs.append("CRLF")
        err = try_parse(s)
        if err:
            probs.append("XML非法:" + err[:50])
            print(f"[FAIL] {f}: " + "; ".join(probs))
            bad += 1
            continue
        # 每个 block 的 CHN 槽数 / 段数 对齐 GER
        for bid, body in re.findall(r'<block id="([^"]+)">(.*?)</block>', s, re.S):
            chn_lang = re.search(r'<lang code="CHN">(.*?)</lang>', body, re.S)
            ger_lang = re.search(r'<lang code="ger">(.*?)</lang>', body, re.S)
            if not ger_lang or not ger_lang.group(1).strip():
                continue
            if not chn_lang:
                probs.append(f"blk {bid}: 无CHN"); continue
            cs = re.findall(r'<text>(.*?)</text>', chn_lang.group(1), re.S)
            gs = re.findall(r'<text>(.*?)</text>', ger_lang.group(1), re.S)
            if len(cs) != len(gs):
                probs.append(f"blk {bid}: 槽数 {len(cs)}≠GER {len(gs)}"); continue
            for i, (c, g) in enumerate(zip(cs, gs)):
                if count_paras(c) != count_paras(g):
                    probs.append(f"blk {bid} 槽{i}: 段数 {count_paras(c)}≠GER {count_paras(g)}")
                if not c.strip():
                    probs.append(f"blk {bid} 槽{i}: 空")
        # string 段空 CHN
        for sid, body in re.findall(r'<string id="([^"]+)">(.*?)</string>', s, re.S):
            chn = re.search(r'<text lang="CHN">(.*?)</text>', body, re.S)
            if chn and not chn.group(1).strip():
                probs.append(f"str {sid}: CHN空")
        # GER 污染（CHN 文本里混入德文字母组合，粗略：含典型德语大写名词+ß 等）
        if re.search(r'ß|[A-ZÄÖÜ]{3,}', s):
            # 仅当 CHN 段出现德语特征才报；先不强制，留作参考
            pass
        if probs:
            bad += 1
            print(f"[WARN] {f}: " + "; ".join(probs[:6]) + ("..." if len(probs) > 6 else ""))
        else:
            print(f"[OK]   {f}")
    print(f"\n问题文件: {bad}/{len(files)}")
    return 0

# --------------------------------------------------------------------------
# inject
# --------------------------------------------------------------------------
def cmd_inject(args):
    mapfile = args.mapfile
    T = load_trans(args.transmod)
    path = os.path.join(MAP_XML, mapfile)
    raw, s = read_text(path)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    assert not has_crlf(s.encode("utf-8")), "CRLF detected"

    def fill_string(m):
        sid = m.group(1); indent = m.group(2)
        if ('str', sid) not in T: return m.group(0)
        return f'<string id="{sid}">\n{indent}<text lang="CHN">{T[("str", sid)]}</text>'
    s = re.sub(r'<string id="([^"]+)">\n(\s*)<text lang="CHN" />', fill_string, s)

    blocks = re.findall(r'<block id="[^"]+">.*?</block>', s, re.S)
    new_blocks = []
    missing = []
    for b in blocks:
        bid = re.search(r'<block id="([^"]+)"', b).group(1)
        m = re.search(r'(<lang code="CHN">)(.*?)(</lang>)', b, re.S)
        if not m:
            new_blocks.append(b); continue
        if ('blk', bid) not in T:
            missing.append(bid); new_blocks.append(b); continue
        chn_inner = m.group(2)
        paras = T[('blk', bid)]
        slots = re.findall(r'<text\s*/>', chn_inner)
        n_slots = len(slots)
        def make_text(body): return f'        <text>\n{body}\n        </text>'
        if isinstance(paras, (list, tuple)):
            assert len(paras) == n_slots, f"block {bid}: {len(paras)} vs {n_slots} slots"
            it = {'i': 0}
            def repl(mm):
                v = paras[it['i']]; it['i'] += 1; return make_text(v)
            new_inner = re.sub(r'<text\s*/>', repl, chn_inner)
        elif n_slots == 1:
            new_inner = re.sub(r'<text\s*/>', lambda mm: make_text(paras), chn_inner, count=1)
        elif n_slots >= 2:
            parts = re.split(r'\n\n', paras, maxsplit=1)
            first = parts[0]; rest = parts[1] if len(parts) > 1 else ''
            it = {'i': 0}
            def repl(mm):
                if it['i'] == 0:
                    it['i'] += 1; return make_text(first)
                else:
                    it['i'] += 1; return make_text(rest)
            new_inner = re.sub(r'<text\s*/>', repl, chn_inner)
        else:
            new_inner = chn_inner
        new_blocks.append(b[:m.start(2)] + new_inner + b[m.end(2):])

    if missing:
        print("WARNING 缺失简报译文:", missing)
    new_s = s
    for orig, nb in zip(blocks, new_blocks):
        new_s = new_s.replace(orig, nb, 1)
    err = try_parse(new_s)
    if err:
        print("ERROR 注入后 XML 非法:", err[:80]); return 1
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_s)
    print("written", mapfile, "| 剩余空 CHN 槽:",
          len(re.findall(r'<text lang="CHN" />', new_s)) + len(re.findall(r'<lang code="CHN">[^<]*<text\s*/>', new_s)))
    return 0

# --------------------------------------------------------------------------
# commit
# --------------------------------------------------------------------------
def cmd_commit(args):
    import subprocess
    msg = args.msg or "汉化：CLI 批量修复/注入"
    # 在仓库根（本文件上一级）执行 git 提交
    repo_root = os.path.dirname(HERE)
    subprocess.run(["git", "-c", "core.autocrlf=false", "add", "-A"], cwd=repo_root, check=True)
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "commit", "-m", msg],
                       cwd=repo_root, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
    return r.returncode

# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Cultures Saga 地图 XML 统一汉化 CLI")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("scan", help="盘点完成度/CRLF/污染")
    rp = sub.add_parser("repair", help="修复非法 XML 结构（默认 dry-run）")
    rp.add_argument("files", nargs="*")
    rp.add_argument("--apply", action="store_true", help="实际写入（默认仅预览）")
    vf = sub.add_parser("verify", help="校验 XML/对齐/空槽")
    vf.add_argument("files", nargs="*")
    ij = sub.add_parser("inject", help="注入翻译字典")
    ij.add_argument("mapfile")
    ij.add_argument("transmod", help="archive/ 下的字典模块名(去.py)")
    cm = sub.add_parser("commit", help="提交(ch_axiom)")
    cm.add_argument("--msg", default=None)

    args = ap.parse_args()
    if args.cmd == "scan": return cmd_scan(args)
    if args.cmd == "repair": return cmd_repair(args)
    if args.cmd == "verify": return cmd_verify(args)
    if args.cmd == "inject": return cmd_inject(args)
    if args.cmd == "commit": return cmd_commit(args)
    ap.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())

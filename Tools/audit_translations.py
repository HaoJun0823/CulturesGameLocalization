# -*- coding: utf-8 -*-
"""
以 ger 为基准，对 Localization/map_xml (+ map_xml_user) 的 XML 做翻译质量审计。

只报告三类明确问题（口径已对真实数据校准，避免噪声）：
  1. 空翻 (empty)      : 语言节点存在，但文本为空/纯空白。    -> 明确缺陷
  2. 漏翻 (missing)    : (a) 整文件未声明该语言；(b) 文件声明了语言但该 key 无条目。 -> 明确缺陷
  3. 错行 (line_mismatch): ger 与译文的非空行数不一致。        -> 待核对（差>=3 标为疑似截断）

注意：
  - 语言码大小写不敏感（XML 里是 "CHN"，脚本内部统一小写比对）。
  - briefing 的每语言是一组 {type,value} 节点列表；strings 的每语言是纯文本。
  - 行数 = 按 \\n 切分后去空白的非空行数（忽略首尾空白/空行差异）。
  - 这是"翻译质量"检查，不是结构校验（结构校验用 `loc_tools.py validate`）。
"""
import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loc_tools import parse_xml_file


def nset(ls):
    return {l.lower() for l in ls}


def text_of(val):
    """briefings: list of nodes -> 拼接 text 节点; strings: str."""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return "\n".join(
            n.get("value", "") or ""
            for n in val
            if isinstance(n, dict) and n.get("type") == "text"
        )
    return str(val)


def lines_of(s):
    return [ln for ln in s.split("\n") if ln.strip()]


def collect_xmls(dirs):
    out = []
    for d in dirs:
        out += glob.glob(str(Path(d) / "*.xml"), recursive=True)
        # map_xml_user 里 XML 在子目录，需递归
        out += glob.glob(str(Path(d) / "**" / "*.xml"), recursive=True)
    # 去重（上面两种 glob 可能重叠）
    return sorted(set(out))


def audit(xml_paths, base, langs):
    report = {
        "base": base,
        "langs": langs,
        "total_files": len(xml_paths),
        "per_lang": {},
    }
    for L in langs:
        report["per_lang"][L] = {
            "files_declaring": 0,
            "files_missing_lang": [],
            "missing_key": [],     # (file, loc)
            "empty": [],           # (file, loc)
            "line_mismatch": [],   # (file, loc, ger_lines, lang_lines, truncation_suspect)
        }

    for xp in xml_paths:
        d = parse_xml_file(Path(xp))
        file_langs = nset(d["languages"])
        fn = Path(xp).name
        if base not in file_langs:
            continue
        for L in langs:
            rec = report["per_lang"][L]
            if L not in file_langs:
                rec["files_missing_lang"].append(fn)
                continue
            rec["files_declaring"] += 1
            for cat, store in (("strings", d["strings"]), ("briefings", d.get("briefings", {}))):
                prefix = "s" if cat == "strings" else "b"
                for key, lm in store.items():
                    lm2 = {k.lower(): v for k, v in lm.items()}
                    if base not in lm2:
                        continue
                    loc = f"{prefix}:{key}"
                    ger_lines = len(lines_of(text_of(lm2[base])))
                    if L not in lm2:
                        rec["missing_key"].append((fn, loc))
                        continue
                    t = text_of(lm2[L])
                    if not t.strip():
                        rec["empty"].append((fn, loc))
                        continue
                    ll = len(lines_of(t))
                    if ger_lines != ll:
                        suspect = abs(ger_lines - ll) >= 3
                        rec["line_mismatch"].append((fn, loc, ger_lines, ll, suspect))
    return report


def write_markdown(rep, out_path):
    lines = []
    a = lines.append
    a(f"# 翻译质量审计（基准 `{rep['base']}`）\n")
    a(f"- 扫描文件总数: **{rep['total_files']}**\n")
    a("\n> **口径说明**\n")
    a("- **空翻 / 漏翻** 是明确缺陷，直接定位去填即可。\n")
    a("- **错行（行数不一致）**：经抽样核实，CHN 的错行几乎都是中文正常换行压缩（译文内容完整），")
    a("并非截断，**无需逐条修改**。如需严格校验需加入字符数/语义比对，行数启发式对中文是伪信号。\n")
    a("- 整文件缺语言 = 该文件未在 `<languages>` 声明此语言（覆盖缺口，是否补译由你决定）。\n")
    for L in rep["langs"]:
        r = rep["per_lang"][L]
        a(f"\n## 语言 `{L}`\n")
        a(f"- 声明该语言的文件: **{r['files_declaring']}/{rep['total_files']}**")
        a(f"（整文件缺失: {len(r['files_missing_lang'])}）")
        a(f"- 单 key 漏翻: **{len(r['missing_key'])}**")
        a(f"- 空翻(空值): **{len(r['empty'])}**")
        a(f"- 错行(行数不一致): **{len(r['line_mismatch'])}**")
        sus = [x for x in r["line_mismatch"] if x[4]]
        a(f"  - 其中疑似截断(差≥3): **{len(sus)}**\n")

        if r["files_missing_lang"]:
            a(f"\n### `{L}` 整文件缺失语言（{len(r['files_missing_lang'])} 个）\n")
            a("```")
            for fn in r["files_missing_lang"]:
                a(f"  {fn}")
            a("```")

        if r["empty"]:
            a(f"\n### `{L}` 空翻（{len(r['empty'])} 处，明确缺陷，优先修）\n")
            a("| 文件 | 位置 |")
            a("|---|---|")
            for fn, loc in r["empty"]:
                a(f"| {fn} | {loc} |")

        if r["missing_key"]:
            a(f"\n### `{L}` 单 key 漏翻（{len(r['missing_key'])} 处）\n")
            a("| 文件 | 位置 |")
            a("|---|---|")
            for fn, loc in r["missing_key"]:
                a(f"| {fn} | {loc} |")

        if r["line_mismatch"]:
            a(f"\n### `{L}` 错行（{len(r['line_mismatch'])} 处，待人工核对）\n")
            a("| 文件 | 位置 | ger行 | 译文行 | 疑似截断 |")
            a("|---|---|---|---|---|")
            # 疑似截断排前面
            for fn, loc, g, l, s in sorted(r["line_mismatch"], key=lambda x: (not x[4], x[2] - x[3])):
                a(f"| {fn} | {loc} | {g} | {l} | {'⚠️' if s else ''} |")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="以 ger 为基准审计翻译质量（空翻/漏翻/错行）")
    ap.add_argument("--xml-dirs", nargs="+",
                    default=["Localization/map_xml", "Localization/map_xml_user"],
                    help="要扫描的目录（默认含 map_xml 与 map_xml_user）")
    ap.add_argument("--base", default="ger")
    ap.add_argument("--langs", nargs="+", default=["eng", "chn"])
    ap.add_argument("--out", default="translation_audit.md", help="markdown 报告路径")
    ap.add_argument("--json", default=None, help="可选 JSON 明细路径")
    args = ap.parse_args()

    xmls = collect_xmls(args.xml_dirs)
    rep = audit(xmls, args.base, args.langs)
    write_markdown(rep, args.out)
    if args.json:
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    # 控制台摘要
    print(f"扫描文件: {rep['total_files']}")
    for L in args.langs:
        r = rep["per_lang"][L]
        sus = sum(1 for x in r["line_mismatch"] if x[4])
        print(f"  [{L}] 声明 {r['files_declaring']}/{rep['total_files']} | "
              f"空翻 {len(r['empty'])} | 漏翻(key) {len(r['missing_key'])} | "
              f"错行 {len(r['line_mismatch'])} (截断 {sus}) | 整文件缺 {len(r['files_missing_lang'])}")
    print(f"报告已写入: {args.out}")


if __name__ == "__main__":
    main()

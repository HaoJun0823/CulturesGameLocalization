# -*- coding: utf-8 -*-
"""
map_xml 汉化一致性检查器
========================
以德语(ger)为基准, 逐个检查 map_xml / map_xml_user 下所有 XML:
  [结构检查] string id 集合 / block id 集合 / lang 覆盖 / text 数量 / 子元素序列
  [内容检查] 启发式: CHN 与 ger 文本长度比异常(疑似张冠李戴)、CHN 残留德语字符(漏翻)

用法: python check_map_xml_consistency.py [--dir map_xml|map_xml_user] [--json out.json]
"""
import os
import re
import sys
import json
import argparse
import xml.etree.ElementTree as ET

ROOT = r"G:/Projects/CulturesGameLocalization/Localization"
DIRS = ["map_xml", "map_xml_user"]

TEXT_TAGS = {"text"}
BLOCK_TAGS = {"text", "font", "picture", "usericon", "usericon2", "icon"}

GER_UMLAUT = re.compile(r"[äöüÄÖÜß]")
# 常见德语功能词, 用于检测 CHN 文本里残留德语(漏翻)
GER_WORDS = re.compile(
    r"\b(der|die|das|und|ist|nicht|ein|eine|einer|dem|den|des|mit|von|für|zu|im|in|"
    r"als|auf|wenn|wie|nach|bei|dann|nun|hast|haben|kann|musst|werden|wird|sich|"
    r"aus|um|über|unter|vor|zwischen|durch|ohne|gegen|für|TIPP|WICHTIG|MISSION|"
    r"KRIEG|ERFOLG|VERLOREN|GEWONNEN|HERVORRAGEND)\b",
    re.IGNORECASE,
)


def parse_file(path):
    """容错解析 XML, 返回 (root, encoding) 或 (None, error)。"""
    raw = open(path, "rb").read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")
    try:
        root = ET.fromstring(text)
        return root, None
    except ET.ParseError as e:
        return None, "XML解析失败: %s" % e


def norm(s):
    """规范化文本用于统计(去空白)。"""
    return re.sub(r"\s+", "", s or "")


def extract(root):
    """把 XML 根元素提取为结构化 dict。"""
    doc = {
        "languages": [],
        "strings": {},   # id -> {lang: text}
        "blocks": {},    # block_id -> {lang: [(type, text), ...]}
    }
    for lang_el in root.findall("./languages/language"):
        doc["languages"].append({
            "code": lang_el.get("code", ""),
            "alias": lang_el.get("alias", ""),
            "encoding": lang_el.get("encoding", ""),
        })
    for s_el in root.findall("./strings/string"):
        sid = s_el.get("id", "")
        texts = {}
        for t_el in s_el.findall("text"):
            lang = t_el.get("lang", "")
            texts[lang] = t_el.text or ""
        doc["strings"][sid] = texts
    for b_el in root.findall("./briefings/block"):
        bid = b_el.get("id", "")
        langs = {}
        for l_el in b_el.findall("lang"):
            code = l_el.get("code", "")
            seq = []
            for child in l_el:
                tag = child.tag
                if tag in BLOCK_TAGS:
                    seq.append((tag, child.text or ""))
                else:
                    seq.append((tag, child.text or ""))
            langs[code] = seq
        doc["blocks"][bid] = langs
    return doc


def check_doc(doc, issues):
    """以 ger 为基准做结构+内容检查, 结果写入 issues 列表。"""
    strings, blocks = doc["strings"], doc["blocks"]

    # ---------- 1. strings ----------
    ger_ids = {i for i, t in strings.items() if "ger" in t}
    chn_ids = {i for i, t in strings.items() if "CHN" in t}
    for i in sorted(ger_ids - chn_ids):
        issues.append({"kind": "string", "id": i, "type": "缺CHN"})
    for i in sorted(chn_ids - ger_ids):
        issues.append({"kind": "string", "id": i, "type": "CHN多余(ger缺失)"})
    # string 内容启发式: 长度比异常
    for i in sorted(ger_ids & chn_ids):
        cn = norm(strings[i].get("CHN", ""))
        ge = norm(strings[i].get("ger", ""))
        _length_check(issues, "string", i, cn, ge)

    # ---------- 2. briefings ----------
    ger_b = {i for i, t in blocks.items() if "ger" in t}
    chn_b = {i for i, t in blocks.items() if "CHN" in t}
    for i in sorted(ger_b - chn_b):
        issues.append({"kind": "block", "id": i, "type": "缺CHN"})
    for i in sorted(chn_b - ger_b):
        issues.append({"kind": "block", "id": i, "type": "CHN多余(ger缺失)"})

    for bid in sorted(blocks):
        b = blocks[bid]
        if "CHN" not in b or "ger" not in b:
            continue
        chn_seq, ger_seq = b["CHN"], b["ger"]
        cn_types = [tp for tp, _ in chn_seq]
        ge_types = [tp for tp, _ in ger_seq]
        cn_texts = [t for tp, t in chn_seq if tp == "text"]
        ge_texts = [t for tp, t in ger_seq if tp == "text"]

        # text 数量
        if len(cn_texts) != len(ge_texts):
            issues.append({
                "kind": "block", "id": bid, "type": "text数量不一致",
                "detail": "CHN=%d ger=%d" % (len(cn_texts), len(ge_texts)),
            })
        # 子元素序列
        if cn_types != ge_types:
            issues.append({
                "kind": "block", "id": bid, "type": "子元素序列不一致",
                "detail": "CHN=%s ger=%s" % (cn_types, ge_types),
            })
        # 内容启发式
        n = min(len(cn_texts), len(ge_texts))
        for k in range(n):
            _length_check(issues, "block", bid, cn_texts[k], ge_texts[k], idx=k)
        # 多出来的 text(数量不一致时也要逐个看)
        if len(cn_texts) > len(ge_texts):
            for k in range(len(ge_texts), len(cn_texts)):
                _length_check(issues, "block", bid, cn_texts[k], "", idx=k)
        elif len(ge_texts) > len(cn_texts):
            for k in range(len(cn_texts), len(ge_texts)):
                _length_check(issues, "block", bid, "", ge_texts[k], idx=k)


def _length_check(issues, kind, id_, cn, ge, idx=None):
    """内容错位启发式:
       - CHN 文本残留德语字符/德语功能词 → 漏翻
       - 长度比异常(错位粘贴) → 可疑
    """
    label = "text[%d]" % idx if idx is not None else ""
    cn_n, ge_n = norm(cn), norm(ge)
    # 漏翻检测
    if cn_n and GER_UMLAUT.search(cn_n):
        issues.append({"kind": kind, "id": id_, "idx": idx, "type": "CHN疑似漏翻(含德文字符)",
                       "detail": "CHN=「%s」" % cn_n[:40]})
    if cn_n and GER_WORDS.search(cn_n) and len(GER_WORDS.findall(cn_n)) >= 2:
        issues.append({"kind": kind, "id": id_, "idx": idx, "type": "CHN疑似漏翻(含德语词)",
                       "detail": "CHN=「%s」" % cn_n[:40]})
    # 长度比: 双方都有内容且都非纯标记
    if cn_n and ge_n:
        ratio = len(cn_n) / len(ge_n)
        if ratio < 0.20 or ratio > 1.10:
            issues.append({
                "kind": kind, "id": id_, "idx": idx, "type": "长度比异常(疑似内容错位)",
                "detail": "CHN=%d字 ger=%d字 ratio=%.2f CHN=「%s」 ger=「%s」"
                          % (len(cn_n), len(ge_n), ratio, cn_n[:30], ge_n[:50]),
            })
    # 一方为空
    elif bool(cn_n) != bool(ge_n):
        issues.append({"kind": kind, "id": id_, "idx": idx, "type": "文本为空",
                       "detail": "CHN=「%s」 ger=「%s」" % (cn_n[:30], ge_n[:50])})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="只检查指定子目录(map_xml/map_xml_user)")
    ap.add_argument("--json", default=None, help="输出完整 JSON 结果路径")
    ap.add_argument("--report", default=None, help="输出文本报告路径")
    args = ap.parse_args()

    dirs = [args.dir] if args.dir else DIRS
    all_result = {}
    for d in dirs:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            print("[!] 目录不存在:", base)
            continue
        # 递归收集 XML(兼容 map_xml_user/Campaign00 这类子目录)
        xml_files = []
        for cur, _sub, files in os.walk(base):
            for fn in files:
                if fn.lower().endswith(".xml"):
                    xml_files.append(os.path.join(cur, fn))
        xml_files.sort()
        all_result[d] = {}
        for path in xml_files:
            fn = os.path.relpath(path, base).replace("\\", "/")
            root, err = parse_file(path)
            path = os.path.join(base, fn)
            root, err = parse_file(path)
            if err:
                all_result[d][fn] = {"error": err}
                continue
            doc = extract(root)
            issues = []
            check_doc(doc, issues)
            all_result[d][fn] = {
                "languages": doc["languages"],
                "n_strings": len(doc["strings"]),
                "n_blocks": len(doc["blocks"]),
                "issues": issues,
            }

    # ---------- 输出 ----------
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(all_result, f, ensure_ascii=False, indent=1)

    lines = []
    total_files = total_issues = 0
    for d in dirs:
        if d not in all_result:
            continue
        lines.append("=" * 90)
        lines.append("目录: %s" % d)
        lines.append("=" * 90)
        for fn, res in all_result[d].items():
            if "error" in res:
                lines.append("  [%s] 解析失败: %s" % (fn, res["error"]))
                total_files += 1
                continue
            iss = res["issues"]
            total_files += 1
            total_issues += len(iss)
            status = "OK" if not iss else "✗ %d 处问题" % len(iss)
            lines.append("\n[%s]  %s  (strings=%d blocks=%d langs=%s)"
                         % (status, fn, res["n_strings"], res["n_blocks"],
                            [l["code"] for l in res["languages"]]))
            for it in iss:
                loc = "%s %s" % (it["kind"], it["id"])
                if it.get("idx") is not None:
                    loc += " text[%d]" % it["idx"]
                lines.append("    - %-28s %s" % (it["type"], loc))
                if it.get("detail"):
                    lines.append("        %s" % it["detail"])

    report_txt = "\n".join(lines)
    print(report_txt)
    print("\n==== 汇总: %d 个文件, %d 处问题 ====" % (total_files, total_issues))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_txt + "\n")
        print("文本报告已写:", args.report)


if __name__ == "__main__":
    main()

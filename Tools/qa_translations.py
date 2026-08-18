# -*- coding: utf-8 -*-
"""
以 ger 为基准的【翻译质量复核】工具（非结构错误检查；用户说的"检查 XML 错误"指的是 loc_tools.py validate，不是本工具）。

检查项（按严重度）：
  ERROR 缺失(missing)    : ger 有某 string id / briefing block，但目标语言无对应键。
  ERROR 空翻(empty)      : ger 非空而目标语言为空。
  ERROR 乱码(mojibake)   : 目标语言含 cp1252 误读痕迹字符（¹ºêœ¿¯³）。
  ERROR 占位符(placeholder): ger 中的 {0}/{1}/%s/<i>/<b> 等占位符/标签在目标语言缺失或多余。
  WARN  段落错位(para)   : 目标语言与 ger 段落数不一致（换行差异，非结构错误，需人工确认）。

用法：
  python Tools/qa_translations.py --base ger
  python Tools/qa_translations.py --base ger --out qa_report.md
  python Tools/qa_translations.py --base ger --langs CHN,eng,pol
  python Tools/qa_translations.py --base ger --json qa.json --out qa.md
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from loc_tools import parse_xml_file

MOJI = set("¹ºêœ¿¯³")  # cp1252 误读痕迹（cp1250 字节被当 cp1252 读）
PLACEHOLDER_RE = re.compile(r"\{[^}]*\}|%[sd]|</?[a-zA-Z][^>]*>")


def para_count(text: str) -> int:
    """统计"非空段落"数（按换行切分，忽略纯空白段）。"""
    if not text:
        return 0
    return len([p for p in text.split("\n") if p.strip()])


def joined_text(nodes) -> str:
    if not nodes:
        return ""
    if isinstance(nodes, str):
        return nodes
    return "\n".join(n.get("value", "") for n in nodes if isinstance(n, dict) and n.get("type") == "text")


def extract_placeholders(text: str) -> Counter:
    return Counter(m.group(0) for m in PLACEHOLDER_RE.finditer(text))


def has_moji(s: str) -> bool:
    return any(c in MOJI for c in s)


def check_one(xml_path: Path, base: str, langs, term_map):
    data = parse_xml_file(xml_path)
    issues = []  # (severity, type, loc, detail)

    # strings
    for sid, lang_map in data.get("strings", {}).items():
        braw = lang_map.get(base) or ""
        btext = braw.strip()
        bph = extract_placeholders(braw)
        for l in langs:
            if l not in lang_map:
                if btext:
                    issues.append(("ERROR", "missing", f"strings#{sid}", f"{l} 缺失键（ger={braw[:30]!r}）"))
                continue
            t = lang_map.get(l) or ""
            ttext = t.strip()
            if btext and not ttext:
                issues.append(("ERROR", "empty", f"strings#{sid}", f"{l} 空翻（ger={braw[:30]!r}）"))
                continue
            if ttext:
                if has_moji(t):
                    issues.append(("ERROR", "mojibake", f"strings#{sid}", f"{l} 含乱码痕迹 {[c for c in t if c in MOJI]}"))
                tph = extract_placeholders(t)
                if bph != tph:
                    only_ger = list((bph - tph).elements())
                    only_tgt = list((tph - bph).elements())
                    issues.append(("ERROR", "placeholder", f"strings#{sid}",
                                   f"{l} 占位符/标签不匹配 ger={bph} {l}={tph}"
                                   + (f" 仅ger有:{only_ger}" if only_ger else "")
                                   + (f" 仅{l}有:{only_tgt}" if only_tgt else "")))
                if para_count(braw) != para_count(t):
                    sev = "WARN"
                    issues.append((sev, "para", f"strings#{sid}",
                                   f"{l} 段落数 ger={para_count(braw)} {l}={para_count(t)}"))

    # briefings
    for bid, lang_map in data.get("briefings", {}).items():
        bj = joined_text(lang_map.get(base))
        btext = bj.strip()
        bph = extract_placeholders(bj)
        for l in langs:
            if l not in lang_map:
                if btext:
                    issues.append(("ERROR", "missing", f"briefing:{bid}", f"{l} 缺失块（ger 有值）"))
                continue
            lj = joined_text(lang_map.get(l))
            lt = lj.strip()
            if btext and not lt:
                issues.append(("ERROR", "empty", f"briefing:{bid}", f"{l} 空翻（ger 有值）"))
                continue
            if lt:
                if has_moji(lj):
                    issues.append(("ERROR", "mojibake", f"briefing:{bid}", f"{l} 含乱码痕迹"))
                tph = extract_placeholders(lj)
                if bph != tph:
                    issues.append(("ERROR", "placeholder", f"briefing:{bid}",
                                   f"{l} 占位符/标签不匹配 ger={bph} {l}={tph}"))
                if para_count(bj) != para_count(lj):
                    sev = "WARN"
                    issues.append((sev, "para", f"briefing:{bid}",
                                   f"{l} 段落数 ger={para_count(bj)} {l}={para_count(lj)}"))

    # 术语一致（仅对 CHN）
    if term_map and "CHN" in langs:
        for sid, lang_map in data.get("strings", {}).items():
            t = (lang_map.get("CHN") or "").strip()
            if not t:
                continue
            for ger_term, chn_term in term_map.items():
                if ger_term in (lang_map.get(base) or "") and chn_term and chn_term not in t:
                    issues.append(("WARN", "term", f"strings#{sid}",
                                   f"术语「{ger_term}」应译为「{chn_term}」未命中"))

    return issues


def main():
    ap = argparse.ArgumentParser(description="以 ger 为基准校验 XML 内翻译")
    ap.add_argument("--xml-dir", default=str(HERE.parent / "Localization" / "map_xml"))
    ap.add_argument("--base", default="ger", help="基准语言（默认 ger）")
    ap.add_argument("--langs", default=None, help="逗号分隔；默认=除 base 外的所有语言（大小写不敏感匹配）")
    ap.add_argument("--terms", default=None, help="language_union.csv 路径（可选术语校验）")
    ap.add_argument("--out", default=None, help="写出 markdown 报告路径")
    ap.add_argument("--json", default=None, help="写出 JSON 明细路径（供子代理消费）")
    args = ap.parse_args()

    xml_dir = Path(args.xml_dir)
    if not xml_dir.exists():
        print(f"XML 目录不存在: {xml_dir}")
        sys.exit(1)

    term_map = {}
    if args.terms:
        tp = Path(args.terms)
        if tp.exists():
            with open(tp, encoding="utf-8", errors="ignore", newline="") as f:
                for row in csv.reader(f):
                    if len(row) >= 2 and row[0].strip():
                        term_map[row[0].strip()] = row[1].strip()

    xml_files = sorted(xml_dir.glob("*.xml"))
    all_issues = []  # per file
    total_by_sev = Counter()
    total_by_type = Counter()

    for xml_path in xml_files:
        data = parse_xml_file(xml_path)
        present = set(data["languages"])
        if args.langs:
            wanted = [x.strip() for x in args.langs.split(",") if x.strip()]
        else:
            wanted = [l for l in present if l != args.base]
        # 大小写不敏感匹配：把 wanted 映射到实际存在的 code
        lower_map = {l.lower(): l for l in present}
        langs = [lower_map.get(w.lower(), w) for w in wanted]
        langs = [l for l in langs if l in present and l != args.base]
        issues = check_one(xml_path, args.base, langs, term_map)
        if issues:
            all_issues.append({"file": xml_path.name, "langs": langs, "issues": issues})
            for sev, typ, _, _ in issues:
                total_by_sev[sev] += 1
                total_by_type[f"{sev}:{typ}"] += 1

    # markdown
    lines = [f"# 翻译校验报告（基准={args.base}）\n", f"XML 文件数: {len(xml_files)}　问题文件数: {len(all_issues)}\n"]
    for sev, typ in sorted(total_by_type.items()):
        lines.append(f"- {sev}: {typ} → {total_by_type[sev+':'+typ] if False else ''}")
    lines.append("\n## 按严重度汇总")
    for sev in ("ERROR", "WARN"):
        lines.append(f"- {sev}: {total_by_sev.get(sev,0)}")
    lines.append("\n## 按文件明细")
    for entry in all_issues:
        lines.append(f"\n### {entry['file']}  ({len(entry['issues'])} 问题)")
        for sev, typ, loc, detail in entry["issues"]:
            lines.append(f"- [{sev}] {typ} {loc}: {detail}")

    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8", newline="\n")
        print(f"\n报告已写出: {args.out}")
    if args.json:
        Path(args.json).write_text(json.dumps(all_issues, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(f"JSON 明细已写出: {args.json}")


if __name__ == "__main__":
    main()

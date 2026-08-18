# -*- coding: utf-8 -*-
"""严格比对 XML 的 ger 与 GAME_2/3/4/5_MAP(+USER) 源地图数据"""
import sys, os, csv, glob, hashlib
sys.path.insert(0, "Tools")
from pathlib import Path
from loc_tools import parse_xml_file, StringsParser, BriefingsParser, fix_1251_chars

G = "G:/Projects/Cultures_Saga_CN"

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

# ---------- 1) 源索引 ----------
src_index = []
def add_source(ver, d, ger_dir, mdat_path):
    ini = os.path.join(ger_dir, "strings.ini")
    cif = os.path.join(ger_dir, "strings.cif")
    btxt = os.path.join(ger_dir, "briefings", "briefings.txt")
    src_index.append({
        "md5": md5(mdat_path) if os.path.exists(mdat_path) else "",
        "version": ver,
        "dirname": os.path.basename(d), "ger": ger_dir,
        "ini": ini, "cif": cif, "btxt": btxt,
    })
def index_dir(ver, d, ger_dir, mdat_path):
    if os.path.isdir(ger_dir) and (os.path.exists(os.path.join(ger_dir, "strings.ini"))
                                   or os.path.exists(os.path.join(ger_dir, "strings.cif"))
                                   or os.path.exists(os.path.join(ger_dir, "briefings", "briefings.txt"))):
        add_source(ver, d, ger_dir, mdat_path)
for ver in ("GAME_2_MAP", "GAME_3_MAP", "GAME_4_MAP", "GAME_5_MAP"):
    base = os.path.join(G, ver, "GER")
    if not os.path.isdir(base):
        continue
    for d in sorted(os.listdir(base)):
        dp = os.path.join(base, d)
        if os.path.isdir(dp):
            index_dir(ver, dp, os.path.join(dp, "text", "ger"), os.path.join(dp, "map.dat"))
for camp in ("Campaign00", "Campaign01"):
    base = os.path.join(G, "GAME_5_MAP_USER", "GER", camp)
    if not os.path.isdir(base):
        continue
    for d in sorted(os.listdir(base)):
        dp = os.path.join(base, d)
        if not os.path.isdir(dp):
            continue
        cum = os.path.join(dp, "currentusermap")
        mdat = os.path.join(cum, "map.dat") if os.path.exists(os.path.join(cum, "map.dat")) else os.path.join(dp, "map.dat")
        ger_dir = os.path.join(cum, "text", "ger") if os.path.isdir(os.path.join(cum, "text", "ger")) else os.path.join(dp, "text", "ger")
        index_dir("GAME_5_MAP_USER", dp, ger_dir, mdat)

by_md5 = {}
for s in src_index:
    if s["md5"]:
        by_md5.setdefault(s["md5"], []).append(s)

# ---------- 2) XML 载入 ----------
xmls = []
for f in sorted(glob.glob("Localization/map_xml/*.xml")):
    xmls.append((f, parse_xml_file(f)))
for f in sorted(glob.glob("Localization/map_xml_user/Campaign0[01]/*.xml")):
    xmls.append((f, parse_xml_file(f)))

# ---------- 3) 版本映射 ----------
version_of = {}
try:
    with open("archives/translation_version_choose.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            version_of[row["map_id"].strip()] = row["version_choose"].strip()
except Exception:
    pass

def norm(s):
    return fix_1251_chars(s.lower())

def match_source(data, fname):
    vid = version_of.get(data["map_id"])
    want_ver = ("GAME_%s_MAP" % vid) if vid else None
    mid, exid = norm(data["map_id"]), norm(data.get("export_map_id") or "")
    base = norm(os.path.basename(fname)[:-4])
    def pick(cands):
        if want_ver:
            for s in cands:
                if s["version"] == want_ver:
                    return s
        return cands[0] if cands else None
    cands = [s for s in src_index if norm(s["dirname"]) == mid]
    if not cands and exid:
        cands = [s for s in src_index if norm(s["dirname"]) == exid]
    if not cands:
        cands = [s for s in src_index if norm(s["dirname"]) == base]
    src = pick(cands)
    if src is None:
        if data["map_md5"] and data["map_md5"] in by_md5 and len(by_md5[data["map_md5"]]) == 1:
            return by_md5[data["map_md5"]][0], "md5-uniq"
        return None, None
    how = "name"
    if data["map_md5"] and src["md5"] and data["map_md5"] != src["md5"]:
        how = "name(md5交叉不符)"
    return src, how

# ---------- 4) 源 ger 解析 ----------
def source_ger(src):
    strings = StringsParser.parse(Path(src["ini"])) if os.path.exists(src["ini"]) else {}
    brief = BriefingsParser.parse(Path(src["btxt"])) if os.path.exists(src["btxt"]) else {}
    return strings, brief

# ---------- 5) 比对 ----------
issues = []      # 全部问题
summary = []     # 每 XML 一行
for f, data in xmls:
    src, how = match_source(data, f)
    base = os.path.basename(f)
    if src is None:
        amb = ""
        if data["map_md5"] and data["map_md5"] in by_md5:
            amb = " (md5命中%d个源但名称都不匹配)" % len(by_md5[data["map_md5"]])
        summary.append((base, "NO_SOURCE", "map_id=%s md5=%s%s" % (data["map_id"], (data["map_md5"] or "")[:12], amb)))
        continue
    s_str, s_br = source_ger(src)
    g_str = {sid: (d.get("ger") or "") for sid, d in data["strings"].items()}
    g_br = {bid: (d.get("ger") or []) for bid, d in data["briefings"].items()}

    probs = []
    # strings
    for sid, st in s_str.items():
        if sid not in g_str:
            probs.append("STR_MISSING_XML:%s" % sid)
        elif g_str[sid] != st:
            probs.append("STR_DIFF:%s" % sid)
    for sid in g_str:
        if sid not in s_str:
            probs.append("STR_EXTRA_XML:%s" % sid)
    # briefings
    for bid, snodes in s_br.items():
        if bid not in g_br:
            probs.append("BRIEF_MISSING_XML:%s" % bid)
        else:
            gnodes = g_br[bid]
            if not gnodes and snodes:
                probs.append("BRIEF_EMPTY_XML:%s(源有%d节点)" % (bid, len(snodes)))
            elif gnodes != snodes:
                # 分类：纯空白差异 vs 内容差异
                def stripws(nodes):
                    return [(n["type"], n["value"].strip()) for n in nodes]
                if stripws(gnodes) == stripws(snodes):
                    probs.append("BRIEF_WS_ONLY:%s" % bid)
                else:
                    probs.append("BRIEF_DIFF:%s" % bid)
    for bid in g_br:
        if bid not in s_br:
            probs.append("BRIEF_EXTRA_XML:%s" % bid)
        elif not s_br[bid] and g_br[bid]:
            probs.append("BRIEF_EMPTY_SRC:%s(XML有内容)" % bid)

    if probs:
        summary.append((base, "ISSUES(%d)" % len(probs), "how=%s ver=%s" % (how, src["version"])))
        issues.append({"file": base, "map_id": data["map_id"], "how": how,
                       "src_version": src["version"], "src_dir": src["dirname"],
                       "problems": probs})
    else:
        summary.append((base, "OK", "how=%s ver=%s" % (how, src["version"])))

# ---------- 6) 输出 ----------
ok = sum(1 for _, st, _ in summary if st == "OK")
nosrc = sum(1 for _, st, _ in summary if st == "NO_SOURCE")
bad = sum(1 for _, st, _ in summary if st.startswith("ISSUES"))
print("XML 总数: %d | OK: %d | 有问题: %d | 无源: %d" % (len(summary), ok, bad, nosrc))

from collections import Counter
cat_counter = Counter()
for it in issues:
    for p in it["problems"]:
        cat_counter[p.split(":")[0]] += 1
print("\n问题分类统计:")
for k, v in cat_counter.most_common():
    print("  %-22s %d" % (k, v))

with open("ger_audit_report.md", "w", encoding="utf-8") as fh:
    fh.write("# GER 严格一致性审计（XML vs GAME_2/3/4/5_MAP 源）\n\n")
    fh.write("XML 总数 %d | OK %d | 有问题 %d | 无源 %d\n\n" % (len(summary), ok, bad, nosrc))
    fh.write("## 问题分类\n\n")
    for k, v in cat_counter.most_common():
        fh.write("- %s: %d\n" % (k, v))
    fh.write("\n## 无源 XML\n\n")
    for b, st, det in summary:
        if st == "NO_SOURCE":
            fh.write("- %s: %s\n" % (b, det))
    fh.write("\n## 有问题的 XML 明细\n\n")
    for it in issues:
        fh.write("### %s (map_id=%s, 匹配=%s, 源=%s/%s)\n" % (
            it["file"], it["map_id"], it["how"], it["src_version"], it["src_dir"]))
        for p in it["problems"]:
            fh.write("- %s\n" % p)
        fh.write("\n")
print("\n报告已写入 ger_audit_report.md")

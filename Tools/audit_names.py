#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人名/专名一致性全量自检（锚点法）。

方法：
  1) 以 language_union.csv 中“专名类”(人名/神名/怪物/地名/部族/生物/物品/事件/奇迹)
     的中文写法作为【规范形 C】。
  2) 扫描 map_xml + map_xml_user 所有 XML 的中文文本，抽出 2~4 字汉字片段(含音译特征字) 作为语料 token。
  3) 对每个规范形 C，找语料中与其【等长、仅一字之差(Hamming=1)】且真实出现的片段 T，
     即为该专名的异体。仅报告真实存在的 (C, T) 对，避免全局连锁噪声。
  4) 同时做：词典内部 同一 GER/ENG -> 多个不同 CHN 的检查。

仅读不改。
"""
import os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "Localization", "ZH-CN")   # 汉化内容根（本仓库内）
CSV  = os.path.join(HERE, "..", "language_union.csv")
sys.path.insert(0, HERE)                     # loc_tools 在本仓库 tools/ 下
from loc_tools import parse_xml_file

TRANSLIT = set("拉尔克斯德里瑞特克布佛西罗得岛尼曼加古洛基索戈梅迪司昂纳维格兰布鲁尤姆伦弗海姆尔萨瓦尔哈托辛赫约耶梦加芬里昂")

# 视为“专名类”的 category（META_TYPE 列，索引 4）
NAME_CATS = {"人名", "神名", "怪物", "神话怪物", "神话地点", "地名", "部族", "生物", "物品", "事件", "奇迹", "其他"}

def cjk_runs(text):
    return re.findall(r'[一-鿿]{2,4}', text)

def tokens_of(text):
    out = set()
    for run in cjk_runs(text):
        for L in (2, 3, 4):
            for i in range(len(run) - L + 1):
                t = run[i:i+L]
                if any(c in TRANSLIT for c in t):
                    out.add(t)
    return out

def hamming1(a, b):
    if len(a) != len(b):
        return False
    return sum(1 for x, y in zip(a, b) if x != y) == 1

# ---------- 1. 规范形 C：来自词典专名类 ----------
canonical = {}  # chn -> (ger, eng, cat)
try:
    with open(CSV, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 5:
                continue
            eng, ger, chn, cat = parts[0], parts[1], parts[3], parts[4]
            if cat in NAME_CATS and chn and any(c in TRANSLIT for c in chn) and 2 <= len(chn) <= 4:
                canonical[chn] = (ger, eng, cat)
except Exception as e:
    print(f"[WARN] csv read fail: {e}")

# ---------- 2. 收集所有 XML 的中文 token ----------
map_dirs = [os.path.join(ROOT, "map_xml"), os.path.join(ROOT, "map_xml_user")]
tok_files = defaultdict(set)   # token -> {filenames}
file_texts = {}
label_values = set()       # 作为“完整字符串值”出现过的 2~4 字中文（名字标签候选）

for md in map_dirs:
    if not os.path.isdir(md):
        continue
    for fn in sorted(os.listdir(md)):
        if not fn.endswith(".xml"):
            continue
        fp = os.path.join(md, fn)
        try:
            d = parse_xml_file(fp)
        except Exception as e:
            print(f"[WARN] parse fail {fn}: {e}")
            continue
        chn = []
        for sid, langmap in d.get("strings", {}).items():
            t = langmap.get("CHN")
            if t:
                chn.append(t)
                label_values.add(t)   # 完整字符串值（名字标签候选）
        for bid, langmap in d.get("briefings", {}).items():
            for node in (langmap.get("CHN") or []):
                if isinstance(node, dict) and node.get("type") == "text" and node.get("value"):
                    chn.append(node["value"])
        text = "\n".join(chn)
        file_texts[fn] = text
        for t in tokens_of(text):
            tok_files[t].add(fn)

# ---------- 3. 锚点比对：规范形 C -> 异体 T ----------
# 过滤：变体 T 仅当 (a) 本身作为“完整字符串标签”出现过，
# 或 (b) 与规范形 C 在同一文件内共存（最可能是同一实体的两种写法）。
pairs = []  # (C, cat, T, files(T), cooccur)
for C, (ger, eng, cat) in canonical.items():
    L = len(C)
    for T, files in tok_files.items():
        if T == C:
            continue
        if len(T) != L:
            continue
        if not hamming1(C, T):
            continue
        co = any(C in file_texts[fn] and T in file_texts[fn] for fn in files)
        # 准入：变体 T 必须是“完整字符串标签”(某处曾以 T 作为整段 CHN 文本)，
        # 以排除仅是长词子串/散文偶现的普通词。
        if T in label_values:
            pairs.append((C, cat, T, sorted(files), co))

# ---------- 4. 词典内部 GER/ENG -> 多 CHN ----------
ger_map = defaultdict(set)
eng_map = defaultdict(set)
try:
    with open(CSV, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 5:
                continue
            eng, ger, chn = parts[0], parts[1], parts[3]
            if ger:
                ger_map[ger].add(chn)
            if eng:
                eng_map[eng].add(chn)
except Exception:
    pass

# ---------- 5. 输出 ----------
print("=" * 72)
print("一、词典内部：同一 GER/ENG 映射到多个不同 CHN（实体被拆译）")
print("=" * 72)
any_ger = False
for ger, chns in sorted(ger_map.items()):
    if len(chns) > 1:
        print(f"  GER[{ger}] -> {sorted(chns)}"); any_ger = True
for eng, chns in sorted(eng_map.items()):
    if len(chns) > 1:
        print(f"  ENG[{eng}] -> {sorted(chns)}"); any_ger = True
if not any_ger:
    print("  （无）")

print()
print("=" * 72)
print("二、专名异体：规范形 C 在 XML 中出现等长仅一字之差的写法 T")
print("=" * 72)
if not pairs:
    print("  （未发现异体）")
else:
    pairs.sort(key=lambda p: (p[1], p[0], p[2]))
    # 统计每个 C 的异体
    by_c = defaultdict(list)
    for C, cat, T, files, co in pairs:
        by_c[C].append((T, files))
    for C, (ger, eng, cat) in canonical.items():
        if C not in by_c:
            continue
        print(f"\n[规范] {C}  ({cat} | GER={ger or '-'} ENG={eng or '-'})")
        for T, files in sorted(by_c[C], key=lambda x: -len(x[1])):
            conflict = [fn for fn in file_texts if C in file_texts[fn] and T in file_texts[fn]]
            flag = "  ⚠ 同文件混用!" if conflict else ""
            print(f"    异体 {T}  -> {len(files)} 文件{flag}")
            for fn in files[:15]:
                print(f"        {fn}")
            if len(files) > 15:
                print(f"        ... 共 {len(files)} 个")
            if conflict:
                print(f"        混用文件: {sorted(conflict)}")

print()
print(f"规范形总数: {len(canonical)} | 发现异体对: {len(pairs)}")

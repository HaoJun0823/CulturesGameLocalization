# -*- coding: utf-8 -*-
"""对比四个同引擎游戏(GAME_2/3/4/5)的 logic 逻辑数据配置，输出结构化报告。

对每个 .ini 文件，按 [section] 块解析出 {(section,key): value}。
差异分三类汇总：
  1) 行结构差异（块/键存在与否）
  2) 数值/文本差异（同一键的值不同）
同时给出 "四份一致" / "谁与谁一致" 的聚类，便于看清游戏间血缘。

用法: python compare_games.py
输出: Logic/compare_report.md
"""
import os
import io
import sys
import itertools
from collections import defaultdict, OrderedDict

ROOT = os.path.dirname(os.path.abspath(__file__))
GAMES = ["GAME_2", "GAME_3", "GAME_4", "GAME_5"]

OUT = os.path.join(ROOT, "compare_report.md")

def collect_ini_files(game):
    base = os.path.join(ROOT, game, "logic")
    found = []
    for dirpath, _, files in os.walk(base):
        for f in files:
            if f.lower().endswith(".ini"):
                rel = os.path.relpath(os.path.join(dirpath, f), base)
                found.append(rel)
    return sorted(found)

def read_lines(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fp:
        return [ln.rstrip("\r\n") for ln in fp]

def parse_ini(lines):
    """解析 ini 为 { (section, index, key): value }。
    同一 section 名会重复出现(每条记录一个块)，用 index 区分第几次出现。
    返回 data(有序 dict) 与 records: list of (section, index)
    """
    data = OrderedDict()
    cur = "__NONE__"
    cur_index = -1
    records = []
    seen = OrderedDict()
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith(";") or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            sec = s[1:-1].strip()
            cur = sec
            seen[sec] = seen.get(sec, 0) + 1
            cur_index = seen[sec]
            records.append((sec, cur_index))
            continue
        if "=" in ln:
            k, v = ln.split("=", 1)
            key = (cur, cur_index, k.strip())
            data[key] = v.strip()
        elif " " in ln:
            # 有的 key 与值以空格分隔, 但 .ini 这里主要用 '='
            k, v = ln.split(None, 1)
            key = (cur, cur_index, k.strip())
            data[key] = v.strip()
    return data, records

def summarize(file_results):
    """汇总所有文件差异,输出 markdown。file_results: list of (rel, data_map)
    data_map: { game: (data, records) }，data 键为 (section,index,key)。
    """
    md = []
    md.append("# 四游戏 Logic 配置对比报告\n")
    md.append("> 对比对象：GAME_2 / GAME_3 / GAME_4 / GAME_5 的 `logic\\*.ini`（含子目录）。\n")
    md.append("> 对比方式：每条记录（同 section 第 N 次出现）按 `[section]#记录序号` 对齐，逐 `key` 比较。\n")
    md.append("> 生成时间：由 compare_games.py 自动生成。\n")
    md.append("")

    # 聚类：按内容完全相同的游戏分组
    md.append("## 0. 文件内容聚类（谁与谁一致）\n")
    md.append("| 文件 | 内容相同的游戏组 | 说明 |")
    md.append("|---|---|---|")
    for rel, data_map in file_results:
        groups = defaultdict(list)
        for g in GAMES:
            if g in data_map:
                groups[tuple(data_map[g][0].items())].append(g)
        if len(groups) == 1:
            cluster = " / ".join(next(iter(groups.values())))
            md.append(f"| `{rel}` | {cluster} | 四份完全一致 |")
        else:
            parts = []
            for content, games in groups.items():
                parts.append("、".join(games))
            md.append(f"| `{rel}` | {' / '.join(parts)} | 存在差异 |")
    md.append("")

    # 逐文件详细差异
    md.append("## 1. 逐文件详细差异\n")
    any_diff = False
    for rel, data_map in file_results:
        games_present = [g for g in GAMES if g in data_map]
        if len(games_present) < len(GAMES):
            md.append(f"### `{rel}`\n")
            md.append("> ⚠️ 部分游戏缺失该文件：" + ", ".join(set(GAMES) - set(games_present)) + "\n")
            any_diff = True
            continue
        all_same = all(data_map[g][0] == data_map[GAMES[0]][0] for g in GAMES)
        if all_same:
            continue
        any_diff = True
        md.append(f"### `{rel}`\n")

        # 记录对齐：按 (section, index) 对齐
        record_sets = {}
        for g in GAMES:
            recs = defaultdict(dict)
            for (sec, idx, key), val in data_map[g][0].items():
                recs[(sec, idx)][key] = val
            record_sets[g] = recs

        all_records = set()
        for g in GAMES:
            all_records |= set(record_sets[g].keys())

        md.append("#### 1. 记录存在性差异（某游戏缺整条记录）\n")
        rec_struct = False
        for rec in sorted(all_records, key=lambda r: (r[0], r[1])):
            present = [g for g in GAMES if rec in record_sets[g]]
            if len(present) < len(GAMES):
                rec_struct = True
                missing = [g for g in GAMES if rec not in record_sets[g]]
                sec, idx = rec
                md.append(f"- `[{sec}]` 第 {idx} 条：存在 [{', '.join(present)}]，缺失 [{', '.join(missing)}]")
        if not rec_struct:
            md.append("- （无）四份记录数相同\n")

        md.append("#### 2. 键值差异\n")
        total_key_diff = 0
        diff_rows = []
        # 每条记录内逐 key 比较
        for rec in sorted(all_records, key=lambda r: (r[0], r[1])):
            sec, idx = rec
            present = [g for g in GAMES if rec in record_sets[g]]
            if len(present) < len(GAMES):
                continue  # 已在上面记录
            # 收集该记录内所有键
            keys_in_rec = set()
            for g in present:
                keys_in_rec |= set(record_sets[g][rec].keys())
            for key in sorted(keys_in_rec):
                distinct = {}
                for g in present:
                    v = record_sets[g][rec].get(key, "<缺失>")
                    distinct.setdefault(v, []).append(g)
                if len(distinct) > 1:
                    total_key_diff += 1
                    row = f"- `[{sec}]` 第{idx}条 · `{key}`：" + \
                          " | ".join(f"{g}={{`{record_sets[g][rec].get(key,'<缺失>')}`}}" for g in GAMES)
                    diff_rows.append(row)
        if total_key_diff == 0:
            md.append("- （无）\n")
        else:
            md.append(f"- 共 {total_key_diff} 个键值存在差异：\n")
            for row in diff_rows:
                md.append(row)
            md.append("")

    if not any_diff:
        md.append("所有文件四份完全一致。\n")

    return "\n".join(md)

def main():
    ref_files = collect_ini_files(GAMES[0])
    file_results = []
    for rel in ref_files:
        data_map = {}
        for g in GAMES:
            p = os.path.join(ROOT, g, "logic", rel)
            if os.path.exists(p):
                data_map[g] = parse_ini(read_lines(p))
        file_results.append((rel, data_map))

    report = summarize(file_results)
    with open(OUT, "w", encoding="utf-8") as fp:
        fp.write(report)
    print("报告已生成:", OUT)

if __name__ == "__main__":
    main()

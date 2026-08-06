# -*- coding: utf-8 -*-
"""
scan_map_dat.py —— 递归搜索目录下所有 map.dat，计算 MD5，输出 CSV。

用途：
  * 建立地图数据索引：map_id / MD5 / 路径，供 build_maps_from_csv.py 按 MD5 关联
    源地图数据（提取自哪个版本、数据目录在哪）。
  * 可指定多输入目录（如 GAME_5_MAP/GER 与 GAME_2_MAP/GER 一起扫）。

用法：
  python Tools/scan_map_dat.py <输入目录> [更多目录...] --output map_index.csv

输出 CSV 列：
  map_id,md5,map_path,lang_root
  例: campaign_01_01,8cef8a0d...,G:/Projects/Cultures_Saga_CN/GAME_2_MAP/GER/campaign_01_01,GAME_2_MAP/GER
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from loc_tools import md5_file  # noqa: E402


def scan_dir(root: Path) -> list:
    """递归搜索 root 下所有 map.dat，返回 [(map_id, md5, map_dir, lang_root)]

    map_id 取地图真实 ID：map.dat 所在目录名；若该目录名为 currentusermap
    （C2M 解包态），则取上一级目录名（如 01_Ein_neuer_Anfang）。
    """
    results = []
    for map_dat in sorted(root.rglob("map.dat")):
        map_dir = map_dat.parent
        map_id = map_dir.name
        if map_id == "currentusermap":
            map_id = map_dir.parent.name
        md5 = md5_file(map_dat)
        # lang_root：输入根到 map_dir 之间的路径段（如 GAME_5_MAP/GER）
        try:
            rel = map_dir.relative_to(root).parts
        except ValueError:
            rel = ()
        lang_root = "/".join(rel[:-1]) if len(rel) > 1 else ""
        results.append((map_id, md5, str(map_dir), lang_root))
    return results


def main():
    ap = argparse.ArgumentParser(description="递归搜索 map.dat，计算 MD5，输出 CSV")
    ap.add_argument("dirs", nargs="+", help="一个或多个输入目录")
    ap.add_argument("--output", default="map_index.csv", help="输出 CSV 路径（默认 map_index.csv）")
    ap.add_argument("--no-lang-root", action="store_true",
                    help="不输出 lang_root 列（兼容简单场景）")
    args = ap.parse_args()

    rows = []
    for d in args.dirs:
        root = Path(d)
        if not root.is_dir():
            print(f"[WARN] 目录不存在: {root}")
            continue
        found = scan_dir(root)
        print(f"[OK] {root}: {len(found)} 个 map.dat")
        rows.extend(found)

    if not rows:
        print("未找到任何 map.dat，退出")
        sys.exit(1)

    # 按 map_id 排序，重复 map_id 保留（不同版本/语言根）
    rows.sort(key=lambda r: (r[0], r[2]))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if args.no_lang_root:
            w.writerow(["map_id", "md5", "map_path"])
            for r in rows:
                w.writerow([r[0], r[1], r[2]])
        else:
            w.writerow(["map_id", "md5", "map_path", "lang_root"])
            for r in rows:
                w.writerow(list(r))
    print(f"\n完成：{len(rows)} 条 -> {out.resolve()}")


if __name__ == "__main__":
    main()

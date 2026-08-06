# -*- coding: utf-8 -*-
"""
build_maps_from_csv.py —— 按 CSV 索引整合输出完整地图（数据 + 中文 l10）。

输入：
  * XML 目录或单个 XML（汉化内容，如 Localization/ZH-CN/map_xml）
  * CSV 索引（scan_map_dat.py 生成：map_id,md5,map_path[,lang_root]）

流程：
  1) 读 CSV 建立 {md5: map_path} 索引。
  2) 遍历输入 XML，取每个文件的 map_md5，在索引中找到源地图目录。
  3) 调用 loc_tools.build_map(map_data_dir=源目录) —— 复制源地图数据（map.cif/dat/ini
     等，排除 text/）+ 写入中文 text/l10/。
  4) 若 XML 标记 IsC2M=true：把产物整理为 currentusermap/ 结构，并打包为 .c2m
     （主战役则保留目录形态）。

用法：
  python Tools/build_maps_from_csv.py \
      --input Localization/ZH-CN/map_xml \
      --csv map_index.csv \
      --output Output \
      [--lang CHN] [--keep-c2m-dir]

C2M 打包说明：
  产物先落盘为 <out>/<map_id>/（含 text/l10/），随后打包为 <out>/<map_id>.c2m
  （归档内路径带 currentusermap\\ 前缀）。加 --keep-c2m-dir 保留中间目录。
"""
import argparse
import csv
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import loc_tools
from cultures2_converter import C2MLibrary  # noqa: E402


def load_md5_index(csv_path: Path):
    """读 CSV，返回 {md5: map_path}。CSV 列: map_id,md5,map_path[,lang_root]"""
    idx = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 3 or row[0].strip() == "map_id":
                continue
            md5, path = row[1].strip(), row[2].strip()
            if md5 and path:
                idx.setdefault(md5, path)  # 首个出现优先
    return idx


def pack_c2m(map_dir: Path, out_c2m: Path):
    """把含 currentusermap/ 的地图目录打包为 .c2m。"""
    lib = C2MLibrary()
    lib.pack_directory(str(map_dir))
    lib.save(str(out_c2m))


def main():
    ap = argparse.ArgumentParser(description="按 CSV 索引整合输出完整地图")
    ap.add_argument("--input", required=True, help="XML 目录或单个 XML 文件")
    ap.add_argument("--csv", required=True, help="map 索引 CSV（scan_map_dat.py 生成）")
    ap.add_argument("--output", default="Output", help="输出目录（默认 Output/）")
    ap.add_argument("--lang", default="CHN", help="构建语言（默认 CHN）")
    ap.add_argument("--keep-c2m-dir", action="store_true", help="C2M 打包后保留中间目录")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.output)
    csv_path = Path(args.csv)

    if in_path.is_file() and in_path.suffix == ".xml":
        xml_files = [in_path]
    elif in_path.is_dir():
        xml_files = sorted(in_path.rglob("*.xml"))
    else:
        print(f"Error: 输入不存在: {in_path}")
        sys.exit(1)

    if not csv_path.exists():
        print(f"Error: CSV 不存在: {csv_path}")
        sys.exit(1)

    idx = load_md5_index(csv_path)
    print(f"XML 文件: {len(xml_files)} | CSV 索引: {len(idx)} 条")

    out_dir.mkdir(parents=True, exist_ok=True)
    ok, missing_data, failed = 0, [], []

    for xf in xml_files:
        try:
            data = loc_tools.parse_xml_file(xf)
            map_md5 = data.get("map_md5", "")
            is_c2m = data.get("IsC2M", False)

            src_map_dir = None
            if map_md5 in idx:
                src_map_dir = Path(idx[map_md5])

            # 用 map_data_dir 触发 build_map 复制源数据（C2M 源目录含 currentusermap/
            # 时，build_map 会复制到 <out>/<map_id>/ 顶层——需后续整理）
            loc_tools.build_map(xf, out_dir, args.lang,
                                map_data_dir=src_map_dir if src_map_dir else None)

            if is_c2m:
                map_dir = out_dir / (data.get("export_map_id") or data.get("map_id") or xf.stem)
                # C2M 打包要求目录含 currentusermap/ 且归档内路径带此前缀。
                # build_map 复制的 map.cif/dat/ini 在 map_dir 顶层；这里统一重排为
                # <map_dir>/currentusermap/，并把源 text/（ger 原文等，build_map 会排除）
                # 一并复制进去——C2M 是自包含地图，无游戏本体 ger 兜底。
                cu = map_dir / "currentusermap"
                if not cu.exists():
                    cu.mkdir(parents=True)
                    for item in list(map_dir.iterdir()):
                        if item.name in ("currentusermap", "text"):
                            continue
                        shutil.move(str(item), str(cu / item.name))
                    # 源地图完整 text/ 复制（含 ger 原文 hlt/fnt/pcx）
                    if src_map_dir is not None:
                        src_text = src_map_dir / "text"
                        if src_text.is_dir():
                            dst_text = cu / "text"
                            dst_text.mkdir(parents=True, exist_ok=True)
                            for item in src_text.iterdir():
                                dst_item = dst_text / item.name
                                if dst_item.exists():
                                    if dst_item.is_dir() and item.is_dir():
                                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                                else:
                                    if item.is_dir():
                                        shutil.copytree(item, dst_item)
                                    else:
                                        shutil.copy2(item, dst_item)
                    # 中文 text/l10 合并进 currentusermap/text/
                    src_text = map_dir / "text"
                    if src_text.exists():
                        dst_text = cu / "text"
                        dst_text.mkdir(parents=True, exist_ok=True)
                        for item in src_text.iterdir():
                            dst_item = dst_text / item.name
                            if dst_item.exists() and dst_item.is_dir() and item.is_dir():
                                shutil.copytree(item, dst_item, dirs_exist_ok=True)
                            elif dst_item.exists():
                                pass
                            else:
                                shutil.move(str(item), str(dst_item))
                        shutil.rmtree(src_text)
                out_c2m = out_dir / f"{map_dir.name}.c2m"
                pack_c2m(map_dir, out_c2m)
                if not args.keep_c2m_dir:
                    shutil.rmtree(map_dir)
                print(f"  [C2M] {map_dir.name} -> {out_c2m.name}")
            else:
                print(f"  [OK] {xf.stem} -> {out_dir.name}/{xf.stem}/")
            ok += 1
        except Exception as e:
            failed.append((xf.name, str(e)[:70]))

    print(f"\n完成: {ok}/{len(xml_files)} 成功")
    if missing_data:
        print(f"无源数据(仅文本): {len(missing_data)} -> {missing_data[:5]}")
    if failed:
        print(f"失败: {len(failed)}")
        for n, e in failed[:8]:
            print(f"  ! {n}: {e}")


if __name__ == "__main__":
    main()

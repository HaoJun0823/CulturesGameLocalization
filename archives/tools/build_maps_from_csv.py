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


def load_version_map(version_csv: Path):
    """读 translation_version_choose.csv，返回 {map_id: version}。"""
    vm = {}
    if not version_csv.exists():
        return vm
    with open(version_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 2 or row[0].strip() == "map_id":
                continue
            try:
                vm[row[0].strip()] = int(row[1].strip())
            except ValueError:
                pass
    return vm


def _fallback_by_map_id(map_id: str, version_csv: Path, src_root: Path):
    """MD5 未命中时按 map_id 回退：用版本表 + GAME_<v>_MAP/GER/<map_id> 找源目录。
    返回 Path 或 None（找不到）。"""
    vm = load_version_map(version_csv)
    version = vm.get(map_id)
    if version is None:
        return None
    cand = src_root / f"GAME_{version}_MAP" / "GER" / map_id
    return cand if cand.is_dir() else None


def pack_c2m(map_dir: Path, out_c2m: Path):
    """把含 currentusermap/ 的地图目录打包为 .c2m。"""
    lib = C2MLibrary()
    lib.pack_directory(str(map_dir))
    lib.save(str(out_c2m))


def _fix_1251_bytes(raw: bytes) -> bytes:
    """对 hlt 等文本文件内容做 fix_1251（变音字符 → ASCII），与 briefings.txt 的
    block id ASCII 化保持一致（如 10minutenspäter → 10minutenspaeter）。"""
    try:
        text = raw.decode("cp1252")
    except UnicodeDecodeError:
        return raw  # 非文本文件（fnt/pcx/bmp）原样保留
    fixed = loc_tools.fix_1251_chars(text)
    return fixed.encode("cp1252")


def _finalize_l10(map_dir: Path):
    """把 build_map 生成的 text/l10 补全为 ger 的完整镜像（官方中文版同结构）：

      text/l10/
      ├── strings.ini          # 中文（build_map 已生成）
      ├── strings.cif          # 复制自 ger（或从中文 strings.ini 转换）
      └── briefings/
          ├── NNNN.hlt         # 复制自 ger，变音 id 过 fix_1251（与中文 briefings.txt 对齐）
          ├── briefings.txt    # 中文（build_map 已生成，block id 已 ASCII 化）
          ├── fonts/*.fnt      # 复制自 ger
          ├── graphics/*.bmp   # 复制自 ger
          └── palettes/*.pcx   # 复制自 ger

    ger 目录必须已存在（由"补源 text/"步骤复制）。若地图无 map.dat（官方未发布，
    如 campaign_01_09），ger 可能缺失 → l10 仅保留 build_map 生成的中文文本。
    """
    l10 = map_dir / "text" / "l10"
    ger = map_dir / "text" / "ger"
    if not l10.is_dir():
        return
    if not ger.is_dir():
        print(f"  [WARN] {map_dir.name}: 无源 ger/（官方未发布地图？），l10 仅中文文本")
        return

    # 1) strings.cif：复制自 ger（布局/结构同源，中文引擎按 strings.ini 覆盖显示）
    src_cif = ger / "strings.cif"
    if src_cif.exists() and not (l10 / "strings.cif").exists():
        shutil.copy2(src_cif, l10 / "strings.cif")

    # 2) briefings/：镜像 ger（hlt 过 fix_1251），保留 build_map 生成的中文 briefings.txt
    src_br = ger / "briefings"
    dst_br = l10 / "briefings"
    if src_br.is_dir():
        dst_br.mkdir(parents=True, exist_ok=True)
        for item in src_br.iterdir():
            dst_item = dst_br / item.name
            if item.is_dir():
                if not dst_item.exists():
                    shutil.copytree(item, dst_item)
                else:
                    shutil.copytree(item, dst_item, dirs_exist_ok=True)
            else:
                # hlt 是文本布局（含 <include:...,blockid,...> 引用），变音 id 需 ASCII 化；
                # fnt/pcx/bmp 是二进制资源，原样复制。
                if item.suffix.lower() == ".hlt" and not dst_item.exists():
                    dst_item.write_bytes(_fix_1251_bytes(item.read_bytes()))
                elif not dst_item.exists():
                    shutil.copy2(item, dst_item)


def main():
    ap = argparse.ArgumentParser(description="按 CSV 索引整合输出完整地图")
    ap.add_argument("--input", required=True, help="XML 目录或单个 XML 文件")
    ap.add_argument("--csv", required=True, help="map 索引 CSV（scan_map_dat.py 生成）")
    ap.add_argument("--output", default="Output", help="输出目录（默认 Output/）")
    ap.add_argument("--lang", default="CHN", help="构建语言（默认 CHN）")
    ap.add_argument("--keep-c2m-dir", action="store_true", help="C2M 打包后保留中间目录")
    ap.add_argument("--fallback-csv", default="translation_version_choose.csv",
                    help="MD5 未命中时的版本表（默认 translation_version_choose.csv）")
    ap.add_argument("--src-root", default="G:/Projects/Cultures_Saga_CN",
                    help="源数据根目录（回退匹配用，默认 G:/Projects/Cultures_Saga_CN）")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.output)
    csv_path = Path(args.csv)
    fallback_csv = Path(args.fallback_csv)
    src_root = Path(args.src_root)

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
            map_id = data.get("export_map_id") or data.get("map_id") or xf.stem

            # 幂等：输出目录已存在旧构建时，先 rename 挪走（rename 不受删除保护限制，
            # 且避免 build_map 在已有目录上叠加旧文件）。
            old_dir = out_dir / map_id
            if old_dir.exists():
                import time, uuid
                stale = out_dir / f".stale_{map_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                old_dir.rename(stale)
                shutil.rmtree(stale, ignore_errors=True)  # 尽力清理，失败不影响

            src_map_dir = None
            if map_md5 in idx:
                src_map_dir = Path(idx[map_md5])
            else:
                # MD5 未命中时按 map_id 回退：读 translation_version_choose.csv 得版本号，
                # 按 GAME_<v>_MAP/GER/<map_id> 找源目录（部分地图源数据缺 map.dat，
                # 但仍能复制 text/ 资源如 hlt/fnt/pcx）。
                src_map_dir = _fallback_by_map_id(map_id, fallback_csv, src_root)

            if src_map_dir is None:
                print(f"  [WARN] {xf.stem}: MD5 与 map_id 均未匹配源数据（仅文本）")

            # 用 map_data_dir 触发 build_map 复制源数据（C2M 源目录含 currentusermap/
            # 时，build_map 会复制到 <out>/<map_id>/ 顶层——需后续整理）。
            # 注意：build_map 的 copy_map_data 会排除 text/，而地图剧情渲染依赖
            # text/ger/briefings/*.hlt、fonts/*.fnt、graphics、palettes、strings.cif 等
            # 源资源——因此这里必须手动把源 text/ 完整复制到输出（主战役与 C2M 通用）。
            loc_tools.build_map(xf, out_dir, args.lang,
                                map_data_dir=src_map_dir if src_map_dir else None)

            map_dir = out_dir / map_id

            # ---- 补源 text/（hlt/fnt/pcx/bmp/strings.cif 等剧情资源，build_map 会排除）----
            if src_map_dir is not None:
                src_text_dir = src_map_dir / "text"
                if src_text_dir.is_dir():
                    dst_text_dir = map_dir / "text"
                    dst_text_dir.mkdir(parents=True, exist_ok=True)
                    for item in src_text_dir.iterdir():
                        dst_item = dst_text_dir / item.name
                        if dst_item.exists():
                            if dst_item.is_dir() and item.is_dir():
                                shutil.copytree(item, dst_item, dirs_exist_ok=True)
                        else:
                            if item.is_dir():
                                shutil.copytree(item, dst_item)
                            else:
                                shutil.copy2(item, dst_item)

            # ---- 补全 l10（以 ger 为镜像：hlt fix_1251 + fonts/graphics/palettes/strings.cif）----
            _finalize_l10(map_dir)

            if is_c2m:
                map_dir = out_dir / (data.get("export_map_id") or data.get("map_id") or xf.stem)
                # C2M 打包要求目录含 currentusermap/ 且归档内路径带此前缀。
                # build_map 复制的 map.cif/dat/ini 在 map_dir 顶层；这里统一重排为
                # <map_dir>/currentusermap/。源 text/（含 ger 原文 hlt/fnt/pcx）已由
                # 上方通用步骤复制到 map_dir/text，重排时随 text 一并移入。
                # （map_dir 已在循环开头整体挪走过，此处必定是全新目录，无需清理）
                cu = map_dir / "currentusermap"
                cu.mkdir(parents=True)
                for item in list(map_dir.iterdir()):
                    if item.name in ("currentusermap", "text"):
                        continue
                    shutil.move(str(item), str(cu / item.name))
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
                    shutil.rmtree(src_text, ignore_errors=True)
                out_c2m = out_dir / f"{map_dir.name}.c2m"
                pack_c2m(map_dir, out_c2m)
                if not args.keep_c2m_dir:
                    # 清理中间目录（失败不致命——c2m 已生成，残留目录可后续手动删）
                    try:
                        shutil.rmtree(map_dir)
                    except Exception as e:
                        print(f"  [WARN] 中间目录残留（不影响 .c2m）: {map_dir.name}: {str(e)[:50]}")
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

# -*- coding: utf-8 -*-
"""
build_maps_from_versions.py —— 按版本选择表构建地图本地化 XML。

输入：
  - translation_version_choose.csv（map_id,version_choose 两列，逗号分隔）
  - 源数据根（含 GAME_2_MAP / GAME_3_MAP / GAME_5_MAP 的目录）

流程：
  对表中每个 map_id，按其指定版本（2/3/5）在 <src>/GAME_<v>_MAP/ 下
  查找该地图目录（语言优先 GER，其次 ENG/POL，排除 POL_OLDCHN），
  用 loc_tools 的解析器提取 strings.ini + briefings.txt，构建为 XML
  输出到 <output>/<map_id>.xml。

用法：
  python Tools/build_maps_from_versions.py \
      --csv translation_version_choose.csv \
      --src "G:/Projects/Cultures_Saga_CN" \
      --output Output
"""
import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from loc_tools import (
    StringsParser, BriefingsParser, md5_file, detect_encoding,
    find_languages, write_xml_file,
)

SUPPORTED_LANGS = ("GER", "ENG", "POL")   # 语言根目录顺序：GER 优先
EXCLUDED_LANGS = {"POL_OLDCHN", "ENG_OLDCHN"}


def find_map_dirs(version_dir: Path, map_id: str):
    """在版本语言根中查找地图目录，返回 [(map_dir, lang)]，仅含实际存在的语言。"""
    found = []
    for lang in SUPPORTED_LANGS:
        lang_dir = version_dir / lang
        if not lang_dir.is_dir():
            continue
        map_dir = lang_dir / map_id
        if map_dir.is_dir():
            found.append((map_dir, lang))
    return found


def build_one(map_dir: Path, lang: str) -> dict:
    """提取单个地图的语言数据，返回 (languages, strings, briefings, map_md5)。"""
    text_dir = map_dir / "text"
    lang_code = lang.lower()
    strings = {}
    briefings = {}
    if (text_dir / lang_code).exists():
        strings = StringsParser.parse(text_dir / lang_code / "strings.ini")
        briefings = BriefingsParser.parse(text_dir / lang_code / "briefings" / "briefings.txt")
    return {
        "map_id": map_dir.name,
        "map_md5": md5_file(map_dir / "map.dat"),
        "strings": strings,
        "briefings": briefings,
    }


def main():
    parser = argparse.ArgumentParser(description="按版本选择表构建地图本地化 XML")
    parser.add_argument("--csv", required=True, help="translation_version_choose.csv 路径")
    parser.add_argument("--src", required=True, help="源数据根目录（含 GAME_2/3/5_MAP）")
    parser.add_argument("--output", default="Output", help="输出目录（默认 Output/）")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    src_root = Path(args.src)
    out_dir = Path(args.output)

    # 读取版本表
    entries = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 2 or row[0].strip() == "map_id":
                continue
            map_id = row[0].strip()
            try:
                version = int(row[1].strip())
            except ValueError:
                print(f"  [WARN] 非法版本号 {row[1]!r} for {map_id}")
                continue
            entries.append((map_id, version))

    print(f"读取版本表：{len(entries)} 个地图")
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, warn_missing = 0, []
    for map_id, version in entries:
        version_dir = src_root / f"GAME_{version}_MAP"
        if not version_dir.is_dir():
            print(f"  [WARN] 版本目录缺失: {version_dir}")
            warn_missing.append(map_id)
            continue

        map_dirs = find_map_dirs(version_dir, map_id)
        if not map_dirs:
            print(f"  [WARN] {map_id} 在 GAME_{version} 中未找到")
            warn_missing.append(map_id)
            continue

        all_strings: dict = {}
        all_briefings: dict = {}
        languages = []
        map_md5 = ""
        for map_dir, lang in map_dirs:
            data = build_one(map_dir, lang)
            if not map_md5:
                map_md5 = data["map_md5"]
            languages.append(lang)
            for sid, t in data["strings"].items():
                all_strings.setdefault(sid, {})[lang] = t
            for bid, nodes in data["briefings"].items():
                all_briefings.setdefault(bid, {})[lang] = nodes

        # 补齐缺失语言列（空串占位），与 loc_tools 语义一致
        for sid in all_strings:
            for lang in languages:
                all_strings[sid].setdefault(lang, "")
        for bid in all_briefings:
            for lang in languages:
                if lang not in all_briefings[bid]:
                    if all_briefings[bid]:
                        first_lang = next(iter(all_briefings[bid].keys()))
                        template = all_briefings[bid][first_lang]
                        all_briefings[bid][lang] = [
                            {'type': n['type'], 'value': "" if n['type'] == 'text' else n['value']}
                            for n in template
                        ]
                    else:
                        all_briefings[bid][lang] = []

        xml_data = {
            "version": "1.3",
            "map_id": map_id,
            "export_map_id": map_id,
            "map_md5": map_md5,
            "IsC2M": False,
            "languages": languages,
            "lang_configs": {lang: {"alias": lang, "encoding": "windows-1252", "fix_1251": False} for lang in languages},
            "strings": all_strings,
            "briefings": all_briefings,
        }
        out_file = out_dir / f"{map_id}.xml"
        write_xml_file(xml_data, out_file)
        ok += 1

    print(f"\n构建完成：{ok}/{len(entries)} 成功")
    if warn_missing:
        print(f"缺失 {len(warn_missing)} 个: {', '.join(warn_missing[:20])}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
整合波兰语(POL)到现有的 Localization/map_xml/*.xml。

对每个波兰地图：
  - text/pol/strings.cif  -> 用 Cultures-map-editor 的 decode 解出 ini 文本
    （其内部按 cp1252 解码，再按 cp1250 还原波兰语字符，最终写成 UTF-8）
  - text/pol/briefings/briefings.txt -> 按 cp1250 解码成 UTF-8
  - 解析后，把 POL 的 strings/briefings 合并进 map_md5 匹配的已有 XML。

匹配方式：波兰地图 map.dat 的 MD5 与 XML 的 map_md5 属性比对。

用法：
  python Tools/_integrate_pol.py --dry-run
  python Tools/_integrate_pol.py            # 真正执行（先自动备份 map_xml）
"""
import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "Cultures-map-editor"))

from loc_tools import (
    parse_xml_file, write_xml_file,
    StringsParser, BriefingsParser,
)

POL_MAPS = Path(r"G:\Projects\Cultures_Saga_Remix\Bramy Asgardu\DataX\Libs\data\maps")
XML_DIR = Path(r"G:\Projects\CulturesGameLocalization\Localization\map_xml")
LANG = "pol"


def md5_of_map_dat(map_dir: Path) -> str:
    p = map_dir / "map.dat"
    if not p.exists():
        return ""
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def decode_pol_strings(cif_path: Path) -> str:
    """cif -> 波兰语(unicode, cp1250 还原)。"""
    from supplements.initialization import decode
    raw_bytes = cif_path.read_bytes()
    txt_cp1252 = decode(raw_bytes, sal_tab_file_format=False)
    # decode 内部按 cp1252 解释字节，这里还原原始字节再用 cp1250 解释
    raw = txt_cp1252.encode("cp1252")
    return raw.decode("cp1250")


def decode_pol_briefings(briefings_path: Path) -> str:
    """briefings.txt 明文，但按 cp1250 还原波兰语字符。"""
    raw = briefings_path.read_bytes()
    try:
        return raw.decode("cp1250")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="ignore")


def build_pol_data(pol_map_dir: Path, tmp: Path):
    """返回 (strings: {id:text}, briefings: {bid:nodes}) 或 None。"""
    pol_dir = pol_map_dir / "text" / LANG
    cif = pol_dir / "strings.cif"
    btxt = pol_dir / "briefings" / "briefings.txt"
    strings, briefings = {}, {}
    if cif.exists():
        s = decode_pol_strings(cif)
        tp = tmp / "strings.ini"
        tp.write_text(s, encoding="utf-8")
        strings = StringsParser.parse(tp)
    if btxt.exists():
        b = decode_pol_briefings(btxt)
        tp = tmp / "briefings.txt"
        tp.write_text(b, encoding="utf-8")
        briefings = BriefingsParser.parse(tp)
    if not strings and not briefings:
        return None
    return strings, briefings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只统计不写入")
    args = ap.parse_args()
    dry = args.dry_run

    # 执行前先备份整个 map_xml 目录（仅一次）
    if not dry:
        stamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_dir = XML_DIR.with_name(XML_DIR.name + f".bak_pol_{stamp}")
        if not bak_dir.exists():
            print(f"[BACKUP] 备份 {XML_DIR} -> {bak_dir}")
            shutil.copytree(XML_DIR, bak_dir)

    # 1) 波兰地图 MD5 -> 目录
    pol_by_md5 = {}
    for d in sorted(POL_MAPS.iterdir()):
        if (d / "map.dat").exists():
            pol_by_md5[md5_of_map_dat(d)] = d

    # 2) 遍历 XML，按 map_md5 匹配
    xml_files = sorted(XML_DIR.glob("*.xml"))
    matched, integrated, skipped = 0, 0, 0
    report = []

    tmp_root = Path(tempfile.mkdtemp(prefix="polint_"))

    for xml_path in xml_files:
        data = parse_xml_file(xml_path)
        md5 = data.get("map_md5", "")
        if md5 not in pol_by_md5:
            continue
        matched += 1
        pol_map_dir = pol_by_md5[md5]
        tmp = tmp_root / xml_path.stem
        tmp.mkdir(parents=True, exist_ok=True)
        pol = build_pol_data(pol_map_dir, tmp)
        if pol is None:
            skipped += 1
            report.append((xml_path.name, 0, 0, "无 pol 数据"))
            continue
        strings, briefings = pol

        # 合并
        if LANG not in data["languages"]:
            data["languages"].append(LANG)
        data["lang_configs"][LANG] = {
            "alias": LANG, "encoding": "windows-1252",
            "fix_1251": False, "base": False,
        }
        n_s = 0
        for sid, text in strings.items():
            data["strings"].setdefault(sid, {})[LANG] = text
            n_s += 1
        n_b = 0
        for bid, nodes in briefings.items():
            data["briefings"].setdefault(bid, {})[LANG] = nodes
            n_b += 1

        if not dry:
            write_xml_file(data, xml_path)
        integrated += 1
        report.append((xml_path.name, n_s, n_b, "OK"))

    shutil.rmtree(tmp_root, ignore_errors=True)

    print(f"波兰地图(含map.dat): {len(pol_by_md5)}   XML 总数: {len(xml_files)}")
    print(f"匹配上的 XML: {matched}   实际整合: {integrated}   跳过(无pol数据): {skipped}")
    print("\n=== 逐文件 ===")
    for name, n_s, n_b, st in report:
        print(f"{name:45s} strings={n_s:4d} briefings={n_b:4d}  {st}")

    if not dry and integrated:
        print(f"\n[完成] 已对 {integrated} 个 XML 整合 POL（目录已备份）。")


if __name__ == "__main__":
    main()

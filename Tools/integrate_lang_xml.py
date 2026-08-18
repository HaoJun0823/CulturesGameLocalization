# -*- coding: utf-8 -*-
"""
合并"其他语言"（POL / RU / CZ / ENG / ...）到 Localization/map_xml/*.xml。

匹配方式（按谨慎程度排序）：
  1) 首选：源地图 map.dat 的 MD5 与 XML 的 map_md5 属性比对（高置信）。
  2) 回退：当 MD5 对不上时（不同游戏版本常见），用"目录名 ↔ XML 的 map_id / export_map_id"
     做名称匹配。
  3) 无论哪种匹配，只要不是 MD5 命中，写入前都必须通过 **id 一致性校验**：
     源语言 strings 的 id 须覆盖目标 XML 已有 id 的 ≥90%，否则视为"疑似错误地图"，
     **跳过并告警**，绝不盲合。这是避免把 A 图的翻译塞进 B 图的关键闸门。

cif 处理：cif 只是 ini 的序列化格式。优先用已解好的 ini；若源只给 cif，则调用
  G:/Projects/Cultures_Saga_CN/cif2ini.py 的 cif2ini_content() 解成 ini 字节流，
  再用 loc_tools.detect_encoding 自动判定编码（utf-8 / cp1252 / cp1250 …），不再手动 hack。

用法（先 dry-run 看匹配与 id 校验情况，再真正写入；写入前自动备份整个 map_xml）：
  python Tools/integrate_lang_xml.py --lang pol \
      --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps" --dry-run
  python Tools/integrate_lang_xml.py --lang pol \
      --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps"
"""
import argparse
import datetime
import hashlib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from loc_tools import (
    parse_xml_file,
    write_xml_file,
    StringsParser,
    BriefingsParser,
)

DEFAULT_XML_DIR = HERE.parent / "Localization" / "map_xml"
DEFAULT_CIF2INI = Path(r"G:/Projects/Cultures_Saga_CN/cif2ini.py")

# 非 MD5 命中时，id 重叠率必须 ≥ 该阈值才允许合并（防止错图盲合）
ID_OVERLAP_MIN = 0.90


def load_cif2ini(path: Path):
    """从任意路径加载 cif2ini.py 模块，返回含 cif2ini_content 的模块。"""
    path = Path(path)
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("cif2ini_user", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def md5_of_map_dat(map_dir: Path) -> str:
    p = map_dir / "map.dat"
    if not p.exists():
        return ""
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def detect_lang_dir(map_dir: Path, lang: str) -> Path | None:
    d = map_dir / "text" / lang
    return d if d.is_dir() else None


# 源语言文件常见代码页：波兰/捷克/斯洛伐克等中欧语言用 cp1250，俄/乌等用 cp1251。
# 关键坑：detect_encoding 在 cp1250 字节上会先命中 cp1252（超集），产生乱码
# （Zajmij siê budow¹ → 应为 Zajmij się budową）。因此这里按"语言→代码页"显式优先解码，
# UTF-8 仍最优先（用户通常直接给 UTF-8 ini 时不受影响）。
_CP1250_LANGS = {"pol", "pl", "cz", "cs", "sk", "sl", "si", "hu", "ro", "hr",
                 "sr", "bs", "sq", "et", "lt", "lv"}
_CP1251_LANGS = {"ru", "uk", "be", "bg", "mk", "kk", "az"}


def source_codepage(lang: str) -> str:
    l = (lang or "").lower()
    if l in _CP1250_LANGS:
        return "cp1250"
    if l in _CP1251_LANGS:
        return "cp1251"
    return "cp1252"


def decode_source(raw: bytes, lang: str) -> str:
    """把源语言文件字节解码为 unicode。"""
    # 1) 已是 UTF-8（最常见，用户通常直接提供 UTF-8 ini）-> 直接成功
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # 2) 按语言选代码页（cp1250/cp1251）—— 修掉波兰语乱码的关键
    for enc in (source_codepage(lang), "cp1252", "iso-8859-1", "cp1250", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def decode_cif(cif_path: Path, cif2ini_mod, lang: str):
    """cif -> unicode 文本（经 cif2ini 解出字节流，再按语言代码页解码）。"""
    if cif2ini_mod is None:
        raise RuntimeError(
            "未找到 cif2ini 模块，无法解码 cif。请用 --cif2ini 指向 cif2ini.py，"
            "或直接使用已解好的 ini 版本。"
        )
    raw = cif2ini_mod.cif2ini_content(cif_path.read_bytes())
    return decode_source(raw, lang)


def decode_briefings(btxt_path: Path, lang: str) -> str:
    return decode_source(btxt_path.read_bytes(), lang)


def build_lang_data(lang_dir: Path, lang: str, tmp: Path, cif2ini_mod):
    """返回 (strings: {id:text}, briefings: {bid:nodes}) 或 None。
    源文件先按语言代码页解码为 UTF-8 临时文件，再交给 StringsParser/BriefingsParser
    （它们内部 detect_encoding 此时会正确识别 UTF-8，避免 cp1250 被误读为 cp1252 的乱码）。"""
    cif = lang_dir / "strings.cif"
    ini = lang_dir / "strings.ini"
    btxt = lang_dir / "briefings" / "briefings.txt"
    strings, briefings = {}, {}
    if ini.exists():
        dec = decode_source(ini.read_bytes(), lang)
        tp = tmp / "strings.ini"
        tp.write_text(dec, encoding="utf-8")
        strings = StringsParser.parse(tp)
    elif cif.exists():
        s = decode_cif(cif, cif2ini_mod, lang)
        tp = tmp / "strings.ini"
        tp.write_text(s, encoding="utf-8")
        strings = StringsParser.parse(tp)
    if btxt.exists():
        b = decode_briefings(btxt, lang)
        tp = tmp / "briefings.txt"
        tp.write_text(b, encoding="utf-8")
        briefings = BriefingsParser.parse(tp)
    if not strings and not briefings:
        return None
    return strings, briefings


def verify_id_consistency(strings: dict, briefings: dict, data: dict):
    """
    谨慎闸门：源语言的 strings id 必须覆盖目标 XML 已有 id 的 ≥ID_OVERLAP_MIN。
    覆盖不足 => 疑似地图版本不一致，禁止合并。
    返回 (ok: bool, detail: str)。
    """
    src_ids = set(strings.keys())
    tgt_ids = set(data.get("strings", {}).keys())
    if not tgt_ids:
        return True, "目标 XML 无 strings（放行）"
    if not src_ids:
        return False, "源无 strings，无法核对 id"
    overlap = len(src_ids & tgt_ids)
    ratio = overlap / len(tgt_ids)
    if ratio < ID_OVERLAP_MIN:
        return (
            False,
            f"id 重叠仅 {ratio:.0%}（目标 {len(tgt_ids)} 个 id，源仅匹配 {overlap} 个），"
            f"疑似地图版本不一致，已跳过以防错合",
        )
    return True, f"id 重叠 {ratio:.0%}"


def main():
    ap = argparse.ArgumentParser(description="合并其他语言到地图 XML（MD5 / id 双匹配 + id 一致性闸门）")
    ap.add_argument("--lang", required=True, help="语言代码，如 pol/ru/cz/eng")
    ap.add_argument("--source", required=True,
                    help="含该语言地图的根目录（其下为各 map_dir，含 map.dat 与 text/<lang>/）")
    ap.add_argument("--xml-dir", default=str(DEFAULT_XML_DIR), help="目标 XML 目录")
    ap.add_argument("--cif2ini", default=str(DEFAULT_CIF2INI),
                    help="cif2ini.py 路径（源只给 cif 时用于解码）")
    ap.add_argument("--force-id-mismatch", action="store_true",
                    help="危险：跳过 id 一致性校验（仅当你确定源正确时）")
    ap.add_argument("--dry-run", action="store_true", help="只统计，不写入（不备份）")
    args = ap.parse_args()

    lang = args.lang.strip().lower()
    xml_dir = Path(args.xml_dir)
    src = Path(args.source)
    cif2ini_mod = load_cif2ini(Path(args.cif2ini))
    if not src.exists():
        print(f"源目录不存在: {src}")
        sys.exit(1)
    if not xml_dir.exists():
        print(f"XML 目录不存在: {xml_dir}")
        sys.exit(1)

    if not args.dry_run:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = xml_dir.with_name(xml_dir.name + f".bak_{lang}_{stamp}")
        if not bak.exists():
            print(f"[BACKUP] {xml_dir} -> {bak}")
            shutil.copytree(xml_dir, bak)

    # 收集源地图候选：map_dir -> (md5, dirname)
    src_candidates = []
    for d in sorted(src.iterdir()):
        if (d / "map.dat").exists():
            src_candidates.append({
                "dir": d, "md5": md5_of_map_dat(d), "name": d.name,
            })
    src_by_md5 = {c["md5"]: c for c in src_candidates if c["md5"]}

    xml_files = sorted(xml_dir.glob("*.xml"))
    matched = integrated = skipped = 0
    report = []
    tmp_root = Path(tempfile.mkdtemp(prefix=f"{lang}int_"))

    for xml_path in xml_files:
        data = parse_xml_file(xml_path)
        md5 = data.get("map_md5", "")
        map_id = (data.get("map_id") or "").lower()
        export_id = (data.get("export_map_id") or "").lower()

        candidate = None
        match_reason = ""
        if md5 and md5 in src_by_md5:
            candidate = src_by_md5[md5]
            match_reason = "MD5"
        else:
            for c in src_candidates:
                cn = c["name"].lower()
                if cn == map_id or cn == export_id or map_id in cn or export_id in cn:
                    candidate = c
                    match_reason = "id(name)"
                    break
        if candidate is None:
            continue
        matched += 1

        ld = detect_lang_dir(candidate["dir"], lang)
        if ld is None:
            skipped += 1
            report.append((xml_path.name, match_reason, 0, 0, f"无 text/{lang}/"))
            continue
        tmp = tmp_root / xml_path.stem
        tmp.mkdir(parents=True, exist_ok=True)
        lang_data = build_lang_data(ld, lang, tmp, cif2ini_mod)
        if lang_data is None:
            skipped += 1
            report.append((xml_path.name, match_reason, 0, 0, "无数据(cif/ini/briefings 均缺)"))
            continue
        strings, briefings = lang_data

        # —— 谨慎闸门：非 MD5 命中必须做 id 一致性校验 ——
        verify_detail = ""
        if match_reason != "MD5" and not args.force_id_mismatch:
            ok, verify_detail = verify_id_consistency(strings, briefings, data)
            if not ok:
                skipped += 1
                report.append((xml_path.name, match_reason, 0, 0, f"ID 闸门拒绝: {verify_detail}"))
                continue

        if lang not in data["languages"]:
            data["languages"].append(lang)
            data["lang_configs"][lang] = {
                "alias": lang, "encoding": "UTF-8",
                "fix_1251": False, "base": False,
            }
        n_s = 0
        for sid, text in strings.items():
            data["strings"].setdefault(sid, {})[lang] = text
            n_s += 1
        n_b = 0
        for bid, nodes in briefings.items():
            data["briefings"].setdefault(bid, {})[lang] = nodes
            n_b += 1

        if not args.dry_run:
            write_xml_file(data, xml_path)
        integrated += 1
        report.append((xml_path.name, match_reason, n_s, n_b,
                       f"OK ({verify_detail or 'MD5 命中'})"))

    shutil.rmtree(tmp_root, ignore_errors=True)

    print(f"源地图(含map.dat): {len(src_candidates)}   XML 总数: {len(xml_files)}")
    print(f"匹配上的 XML: {matched}   实际整合: {integrated}   跳过(无数据/无该语言/ID拒绝): {skipped}")
    print("\n=== 逐文件 (匹配方式 | strings | briefings | 状态) ===")
    for name, reason, n_s, n_b, st in report:
        print(f"{name:45s} [{reason:8s}] strings={n_s:4d} briefings={n_b:4d}  {st}")

    if not args.dry_run and integrated:
        print(f"\n[完成] 已对 {integrated} 个 XML 整合 {lang}（目录已备份）。")


if __name__ == "__main__":
    main()

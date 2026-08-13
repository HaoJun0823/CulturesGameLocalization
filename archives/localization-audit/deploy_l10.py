# -*- coding: utf-8 -*-
"""部署 l10 汉化：从修复后的 map_xml / map_xml_user 构建 UTF-8 文本，
覆盖游戏目录 Data/maps 与 DataX/UserCampaigns 的 text/l10/。

覆盖文件（仅两个文本源，其余 hlt/fonts/pcx 等语言无关文件保留）：
  - strings.ini            (UTF-8, CRLF)
  - briefings/briefings.txt (UTF-8, CRLF)
strings.cif 不更新：cif 内部用 cp1252 编码，无法承载中文；游戏实际读取 strings.ini。

用法: python deploy_l10.py [--dry-run] [--backup-dir 路径]
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Tools"))
import loc_tools  # noqa: E402
from loc_tools import fix_1251_chars  # noqa: E402

LOC_ROOT = Path(__file__).resolve().parent
XML_ROOT = LOC_ROOT / "map_xml"
XML_USER_ROOT = LOC_ROOT / "map_xml_user"
GAME_MAPS = Path(r"G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK/Data/maps")
GAME_USER = Path(r"G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK/DataX/UserCampaigns")
TMP = LOC_ROOT / "_tmp_l10_build"


def build_one(xml_file: Path, tmp_sub: str):
    """构建单个 XML -> 临时目录，返回 (export_map_id, built_l10_dir)"""
    out = TMP / tmp_sub
    loc_tools.build_map(xml_file, out, "CHN", force_utf8=True)
    data = loc_tools.parse_xml_file(xml_file)
    eid = data.get("export_map_id") or data.get("map_id") or xml_file.stem
    built_l10 = out / eid / "text" / "l10"
    if not (built_l10 / "strings.ini").exists() or not (built_l10 / "briefings" / "briefings.txt").exists():
        raise RuntimeError(f"构建产物缺失: {xml_file.name}")
    return eid, built_l10


def deploy(xml_file: Path, target_l10: Path, tmp_sub: str, dry_run: bool):
    eid, built_l10 = build_one(xml_file, tmp_sub)
    files = ["strings.ini", Path("briefings") / "briefings.txt"]
    if dry_run:
        print(f"  [DRY] {eid} -> {target_l10}")
        return
    for rel in files:
        src = built_l10 / rel
        dst = target_l10 / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    # 字节级校验
    for rel in files:
        if (built_l10 / rel).read_bytes() != (target_l10 / rel).read_bytes():
            raise RuntimeError(f"校验失败: {target_l10 / rel}")
    print(f"  [OK] {eid} -> {target_l10}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只构建不覆盖")
    ap.add_argument("--backup-dir", default=str(LOC_ROOT / "_backup_game_l10_20260812"))
    ap.add_argument("--skip-backup", action="store_true")
    args = ap.parse_args()

    backup_dir = Path(args.backup_dir)
    if not args.dry_run and not args.skip_backup:
        print(f"[备份] 现有 l10 strings.ini/briefings.txt -> {backup_dir}")
        for d in list(GAME_MAPS.iterdir()) + [
            p for c in GAME_USER.iterdir() if c.is_dir() and c.name.startswith("Campaign")
            for p in c.iterdir() if p.is_dir() and not p.name.startswith("_")
        ]:
            rel_map = d.relative_to(GAME_MAPS) if d.is_relative_to(GAME_MAPS) else None
            if rel_map is not None:
                src = d / "text" / "l10"
                dst = backup_dir / "maps" / rel_map / "text" / "l10"
            else:
                src = d / "currentusermap" / "text" / "l10"
                dst = backup_dir / "usercampaigns" / d.parent.name / d.name / "text" / "l10"
            if not src.exists():
                continue
            for rel in ["strings.ini", Path("briefings") / "briefings.txt"]:
                s = src / rel
                if s.exists():
                    t = dst / rel
                    t.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, t)
        print(f"[备份完成] {sum(1 for _ in backup_dir.rglob('*') if _.is_file())} 个文件")

    # 主战役 128
    print("=== 主战役 map_xml -> Data/maps ===")
    n = 0
    for f in sorted(XML_ROOT.glob("*.xml")):
        eid, _ = build_one(f, "maps")
        target = GAME_MAPS / fix_1251_chars(eid) / "text" / "l10"
        if not target.exists():
            print(f"  [SKIP] 目标目录不存在: {target}")
            continue
        deploy(f, target, "maps", args.dry_run)
        n += 1
    print(f"主战役处理 {n} 个")

    # 用户战役 28
    print("=== 用户战役 map_xml_user -> DataX/UserCampaigns ===")
    n = 0
    for cur in sorted(XML_USER_ROOT.iterdir()):
        if not cur.is_dir():
            continue
        for f in sorted(cur.glob("*.xml")):
            target = GAME_USER / cur.name / f.stem / "currentusermap" / "text" / "l10"
            if not target.exists():
                print(f"  [SKIP] 目标目录不存在: {target}")
                continue
            deploy(f, target, "user", args.dry_run)
            n += 1
    print(f"用户战役处理 {n} 个")

    print("全部完成。")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""部署 UTF-8 多语言地图到游戏目录。

源：
  OfficalMaps/          -> G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK/Data/maps/
  OfficalUserMaps/      -> G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK/DataX/UserCampaigns/

注意：UserCampaigns 的目录结构是 <CampaignXX>/<map_id>/currentusermap/text/<lang>/
      即有一层 currentusermap 包装。

用法：
  python deploy_all.py              # 部署（先备份）
  python deploy_all.py --dry-run    # 只预览，不操作
  python deploy_all.py --skip-backup  # 部署，不备份
"""
import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # Tools/
PROJ_ROOT = HERE.parent                          # CulturesGameLocalization 根
LOC_ROOT = PROJ_ROOT / "Localization"

# 构建产出
SRC_MAIN = PROJ_ROOT / "OfficalMaps"
SRC_USER = PROJ_ROOT / "OfficalUserMaps"

# 游戏目标
GAME_DIR = Path(r"G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK")
DST_MAPS = GAME_DIR / "Data" / "maps"
DST_USER = GAME_DIR / "DataX" / "UserCampaigns"

# 备份目录
BACKUP_ROOT = LOC_ROOT / "_backup_game_deploy"


def backup_game_text(dry_run: bool):
    """备份游戏目录现有的 text/ 目录（只备份即将被覆盖的）"""
    if dry_run:
        print("[DRY-RUN] 跳过备份")
        return

    backup_dir = BACKUP_ROOT
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    # 主战役 map_xml 对应的 text/ 目录
    if SRC_MAIN.exists():
        for map_dir in sorted(SRC_MAIN.iterdir()):
            if not map_dir.is_dir():
                continue
            dst = DST_MAPS / map_dir.name / "text"
            if dst.exists():
                bak = backup_dir / "maps" / map_dir.name / "text"
                shutil.copytree(dst, bak)
                count += 1

    # 用户战役
    if SRC_USER.exists():
        for campaign_dir in sorted(SRC_USER.iterdir()):
            if not campaign_dir.is_dir():
                continue
            for map_dir in sorted(campaign_dir.iterdir()):
                if not map_dir.is_dir():
                    continue
                dst = DST_USER / campaign_dir.name / map_dir.name / "currentusermap" / "text"
                if dst.exists():
                    bak = backup_dir / "UserCampaigns" / campaign_dir.name / map_dir.name / "currentusermap" / "text"
                    shutil.copytree(dst, bak)
                    count += 1

    print(f"[备份] {count} 个 text/ 目录已备份到 {backup_dir}")


def deploy_main_maps(dry_run: bool):
    """部署主战役地图"""
    if not SRC_MAIN.exists():
        print(f"[跳过] 源目录不存在: {SRC_MAIN}")
        return

    maps = sorted([d for d in SRC_MAIN.iterdir() if d.is_dir()])
    print(f"\n=== 主战役 ({len(maps)} 个地图) ===")

    done = 0
    for src_map in maps:
        map_id = src_map.name
        dst_text = DST_MAPS / map_id / "text"

        if not src_map.joinpath("text").exists():
            print(f"  [跳过] {map_id}: text/ 目录不存在")
            continue

        if dry_run:
            lang_dirs = [d.name for d in src_map.joinpath("text").iterdir() if d.is_dir()]
            print(f"  [DRY] {map_id} -> {dst_text}  (语言: {', '.join(lang_dirs)})")
            done += 1
            continue

        # 删除旧 text/ 目录，替换为新版
        if dst_text.exists():
            shutil.rmtree(dst_text)
        shutil.copytree(src_map / "text", dst_text)
        done += 1

    print(f"主战役: {done}/{len(maps)} 个已部署")


def deploy_user_maps(dry_run: bool):
    """部署用户战役地图（注意 currentusermap 包装层）"""
    if not SRC_USER.exists():
        print(f"[跳过] 源目录不存在: {SRC_USER}")
        return

    campaigns = sorted([d for d in SRC_USER.iterdir() if d.is_dir()])
    total = 0
    done = 0

    print(f"\n=== 用户战役 ({len(campaigns)} 个战役组) ===")

    for campaign_dir in campaigns:
        maps = sorted([d for d in campaign_dir.iterdir() if d.is_dir()])
        total += len(maps)

        for src_map in maps:
            map_id = src_map.name
            dst_text = DST_USER / campaign_dir.name / map_id / "currentusermap" / "text"

            if not src_map.joinpath("text").exists():
                print(f"  [跳过] {campaign_dir.name}/{map_id}: text/ 目录不存在")
                continue

            if dry_run:
                lang_dirs = [d.name for d in src_map.joinpath("text").iterdir() if d.is_dir()]
                print(f"  [DRY] {campaign_dir.name}/{map_id} -> {dst_text}  (语言: {', '.join(lang_dirs)})")
                done += 1
                continue

            # 确保 currentusermap 目录存在
            dst_text.parent.mkdir(parents=True, exist_ok=True)
            # 删除旧 text/ 目录
            if dst_text.exists():
                shutil.rmtree(dst_text)
            shutil.copytree(src_map / "text", dst_text)
            done += 1

    print(f"用户战役: {done}/{total} 个已部署")


def main():
    ap = argparse.ArgumentParser(description="部署 UTF-8 多语言地图到游戏目录")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不操作")
    ap.add_argument("--skip-backup", action="store_true", help="跳过备份")
    args = ap.parse_args()

    print("=" * 60)
    print("Cultures Saga — 多语言地图部署")
    print("=" * 60)
    print(f"源:     {SRC_MAIN}, {SRC_USER}")
    print(f"目标:   {DST_MAPS}, {DST_USER}")
    if args.dry_run:
        print("模式:   DRY-RUN (仅预览)")
    print()

    if not args.dry_run and not args.skip_backup:
        backup_game_text(False)
    elif args.dry_run:
        backup_game_text(True)

    deploy_main_maps(args.dry_run)
    deploy_user_maps(args.dry_run)

    print()
    print("=" * 60)
    if args.dry_run:
        print("DRY-RUN 完成，未执行任何实际部署。")
    else:
        print("部署完成！")
        print(f"备份位于: {BACKUP_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
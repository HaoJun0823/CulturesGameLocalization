# -*- coding: utf-8 -*-
"""
Cultures Saga — Simplified-Chinese-Only Map Build Script
=========================================================
Derivative of build_text.py, but builds ONLY the Simplified Chinese
(CHN -> text/l10/) language layer from XML.

Differences vs. build_text.py:
  1. Output root is dist/ (not _build/).
  2. Only the CHN language is built from XML (all other languages are
     skipped entirely — no eng/ger/pol/l11/l12/l13 text dirs are created).
  3. Non-text resources (map.dat, map.ini, logic/, sfx/, ...) are still
     copied from the original game data, and ger resource files (.hlt/.fnt/
     .pcx etc., excluding strings.ini / briefings) are copied into text/l10/
     so the Chinese layer is self-contained and loadable.
  4. copy_additional_assets() only copies Localization/text/l10/ (the
     Simplified-Chinese part of Data/Text) — other languages are dropped.

Usage:
  python build_text_chn.py            # Build Simplified Chinese only
  python build_text_chn.py --clean    # Clean dist/ first, then build
  python build_text_chn.py --dry-run  # Preview only

Output:
  dist/
    Data/maps/<map_id>/text/l10/          → Simplified-Chinese map text
    DataX/UserCampaigns/                  → Simplified-Chinese user maps
    Data/Text/                            → Simplified-Chinese game text
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

# ============================================================
# Path Configuration (modify only these)
# ============================================================

# CulturesGameLocalization project root (parent of this script)
PROJ_ROOT = Path(__file__).resolve().parent

# Game reference directory (source for map.dat/map.ini/text/ger/ resources)
GAME_DIR = Path(r"G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK")
MAPDATA_DIR = PROJ_ROOT / "mapdata"

# XML source
XML_MAIN = PROJ_ROOT / "Localization" / "map_xml"
XML_USER = PROJ_ROOT / "Localization" / "map_xml_user"

# Build output (Simplified-Chinese-only dist)
BUILD_ROOT = PROJ_ROOT / "dist"

# Tools
TOOLS = PROJ_ROOT / "Tools"

# Additional asset sources
LOC_TEXT_SRC = PROJ_ROOT / "Localization" / "text"    # → dist/Data/Text/ (l10 only)

# The ONLY language this script builds: Simplified Chinese.
TARGET_LANG = "CHN"
# Output directory name inside text/ (CHN is aliased to l10 by loc_tools.build_map)
TARGET_TEXT_DIR = "l10"


# ============================================================
# Core Logic
# ============================================================

def copy_chn_assets_only(src_text: Path, dst_text: Path):
    """Copy ONLY the Simplified-Chinese (l10) part of a Data/Text tree.

    Mirrors the structure of Localization/text/l10/ → dist/Data/Text/l10/,
    skipping all other language directories.
    """
    if not src_text.exists():
        return
    chn_src = src_text / TARGET_TEXT_DIR
    if not chn_src.exists():
        return
    dst_text.mkdir(parents=True, exist_ok=True)
    chn_dst = dst_text / TARGET_TEXT_DIR
    if chn_dst.exists():
        shutil.rmtree(chn_dst)
    shutil.copytree(chn_src, chn_dst)
    print(f"  [OK] Localization/text/{TARGET_TEXT_DIR}/ → Data/Text/{TARGET_TEXT_DIR}/")


def copy_additional_assets():
    """Copy supplementary assets (Simplified-Chinese only).

    - Localization/text/l10/ → dist/Data/Text/l10/  (game text resources, CHN only)
    """
    # 1) Localization/text → Data/Text (l10 only)
    text_dst = BUILD_ROOT / "Data" / "Text"
    if LOC_TEXT_SRC.exists():
        copy_chn_assets_only(LOC_TEXT_SRC, text_dst)
    else:
        print(f"  [Skip] Localization/text/ not found")


def copy_ger_resources(ger_text: Path, l10_text: Path):
    """Copy ger non-text resources into the l10 directory (in place, no return).

    Mirrors the original build_text.py behaviour: everything except the two
    text files (strings.ini, briefings/briefings.txt) is copied from
    text/ger/ into text/l10/ — fonts/graphics/palettes subfolders AND the
    .hlt hypertext files inside briefings/ (only briefings.txt itself is
    skipped, since its Chinese content is generated from XML).
    """
    for item in ger_text.iterdir():
        if item.name == "strings.ini":
            continue
        if item.name == "briefings":
            dst_bf = l10_text / "briefings"
            dst_bf.mkdir(parents=True, exist_ok=True)
            for bf in item.iterdir():
                if bf.name == "briefings.txt":
                    continue
                dst_item = dst_bf / bf.name
                if not dst_item.exists():
                    (shutil.copytree if bf.is_dir() else shutil.copy2)(bf, dst_item)
            continue
        dst_item = l10_text / item.name
        if not dst_item.exists():
            (shutil.copytree if item.is_dir() else shutil.copy2)(item, dst_item)


def resolve_map_source(map_id: str) -> Path | None:
    """Find the source map directory for map_id (mapdata/ first, then GAME_DIR)."""
    candidates = [
        MAPDATA_DIR / "Data" / "maps" / map_id,
        GAME_DIR / "Data" / "maps" / map_id,
    ]
    for src in candidates:
        if src.is_dir() and (src / "map.dat").exists():
            return src
        if src.is_dir():
            # Some maps (e.g. campaign_01_09) have no map.dat — text-only
            return src
    return None


def build_chn_only(xml_file, output_dir, loc_tools):
    """Build ONLY the Simplified Chinese (CHN) language from XML.

    Returns the parsed data dict (for map_id lookup) — or None when the
    whole map is marked deprecated.
    """
    data = loc_tools.parse_xml_file(xml_file)
    if data.get("deprecated", False):
        return None
    # loc_tools.build_map handles the CHN special-casing internally:
    #   encoding → GB2312, output dir → text/l10/
    loc_tools.build_map(xml_file, output_dir, TARGET_LANG, force_utf8=True)
    return data


def build_main_maps(loc_tools):
    """Build main campaign maps — Simplified Chinese only (128 maps)"""
    xml_files = sorted(XML_MAIN.glob("*.xml"))
    print(f"\n{'='*60}")
    print(f"  Main Campaign (CHN only): {len(xml_files)} maps")
    print(f"{'='*60}")

    build_maps = BUILD_ROOT / "Data" / "maps"

    ok = skip = dep = 0
    for f in xml_files:
        meta = loc_tools.parse_xml_file(f)
        map_id = meta.get("export_map_id") or meta.get("map_id") or f.stem
        target_dir = build_maps / map_id
        xml_md5 = meta.get("map_md5", "")

        # 0) Deprecated maps: skip entirely
        if meta.get("deprecated", False):
            print(f"  [Skip] {map_id}: deprecated")
            dep += 1
            continue

        # 1) Copy original game data (map.dat, map.ini, logic/, sfx/, ...)
        src_dir = resolve_map_source(map_id)
        if src_dir is not None:
            src_md5 = loc_tools.md5_file(src_dir / "map.dat") if (src_dir / "map.dat").exists() else ""
            if xml_md5 and src_md5 and xml_md5 != src_md5:
                print(f"  [WARN] {map_id}: mapdata MD5 {src_md5[:8]} != XML {xml_md5[:8]}")
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(src_dir, target_dir)
        else:
            print(f"  [Skip] {map_id}: no game data for this map")
            skip += 1
            continue

        # 2) Remove non-CHN language directories copied from the source
        #    (keep ger for reference below; drop eng/pol/l11/l12/l13/…)
        text_dir = target_dir / "text"
        if text_dir.exists():
            for lang_dir in list(text_dir.iterdir()):
                if lang_dir.is_dir() and lang_dir.name not in ("ger", TARGET_TEXT_DIR):
                    shutil.rmtree(lang_dir)

        # 3) Build ONLY Simplified Chinese from XML (overwrites text/l10/strings.ini etc.)
        build_chn_only(f, build_maps, loc_tools)

        # 4) Copy ger non-text resources (fonts/graphics/palettes/hlt) into l10
        ger_text = target_dir / "text" / "ger"
        l10_text = target_dir / "text" / TARGET_TEXT_DIR
        if ger_text.exists() and l10_text.exists():
            copy_ger_resources(ger_text, l10_text)

        # 5) Drop the ger text layer — this is a Chinese-only dist
        if ger_text.exists():
            shutil.rmtree(ger_text)

        print(f"  [OK] {map_id} ({TARGET_TEXT_DIR})")
        ok += 1

    print(f"\n  Main Campaign: {ok} ok, {skip} skipped, {dep} deprecated\n")
    return ok, skip, dep


def build_user_maps(loc_tools):
    """Build user campaign maps — Simplified Chinese only (28 maps)"""
    user_xmls = sorted(
        f for d in sorted(XML_USER.iterdir()) if d.is_dir()
        for f in sorted(d.glob("*.xml"))
    )
    print(f"{'='*60}")
    print(f"  User Campaigns (CHN only): {len(user_xmls)} maps")
    print(f"{'='*60}")

    build_user = BUILD_ROOT / "DataX" / "UserCampaigns"

    ok = skip = dep = 0
    for f in user_xmls:
        campaign = f.parent.name  # Campaign00 / Campaign01
        meta = loc_tools.parse_xml_file(f)
        map_id = meta.get("export_map_id") or meta.get("map_id") or f.stem
        target_dir = build_user / campaign / map_id / "currentusermap"

        # 0) Deprecated maps: skip entirely
        if meta.get("deprecated", False):
            print(f"  [Skip] {campaign}/{map_id}: deprecated")
            dep += 1
            continue

        # 1) Copy original game data (mapdata/ first, then GAME_DIR)
        src_dir = None
        for base in (MAPDATA_DIR, GAME_DIR):
            candidate = base / "DataX" / "UserCampaigns" / campaign / map_id / "currentusermap"
            if candidate.is_dir() and (candidate / "map.dat").exists():
                src_dir = candidate
                break
            elif candidate.is_dir():
                src_dir = candidate
                break
        if src_dir is not None:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(src_dir, target_dir)
        else:
            print(f"  [Skip] {campaign}/{map_id}: no game data")
            skip += 1
            continue

        # 2) Remove non-CHN language directories (keep ger for resource copy)
        text_dir = target_dir / "text"
        if text_dir.exists():
            for lang_dir in list(text_dir.iterdir()):
                if lang_dir.is_dir() and lang_dir.name not in ("ger", TARGET_TEXT_DIR):
                    shutil.rmtree(lang_dir)

        # 3) Build ONLY Simplified Chinese from XML
        build_chn_only(f, build_user / campaign, loc_tools)

        # 4) Copy ger non-text resources into l10
        ger_text = target_dir / "text" / "ger"
        l10_text = target_dir / "text" / TARGET_TEXT_DIR
        if ger_text.exists() and l10_text.exists():
            copy_ger_resources(ger_text, l10_text)

        # 5) Drop the ger text layer — Chinese-only dist
        if ger_text.exists():
            shutil.rmtree(ger_text)

        print(f"  [OK] {campaign}/{map_id} ({TARGET_TEXT_DIR})")
        ok += 1

    print(f"\n  User Campaigns: {ok} ok, {skip} skipped, {dep} deprecated\n")
    return ok, skip, dep


def verify_build():
    """Verify Simplified-Chinese-only build output integrity"""
    print(f"{'='*60}")
    print(f"  Verification (Simplified Chinese only)")
    print(f"{'='*60}")

    build_maps = BUILD_ROOT / "Data" / "maps"
    build_user = BUILD_ROOT / "DataX" / "UserCampaigns"

    issues = []

    def check_map_text_dir(map_root: Path, label: str):
        text_dir = map_root / "text"
        if not text_dir.exists():
            return
        # Only l10 should remain
        for lang_dir in text_dir.iterdir():
            if lang_dir.is_dir() and lang_dir.name != TARGET_TEXT_DIR:
                issues.append(f"{label}: unexpected language dir '{lang_dir.name}'")
        l10_dir = text_dir / TARGET_TEXT_DIR
        if not l10_dir.exists():
            issues.append(f"{label}: missing text/{TARGET_TEXT_DIR}/")
        elif not (l10_dir / "strings.ini").exists():
            issues.append(f"{label}: missing text/{TARGET_TEXT_DIR}/strings.ini")

    # Main campaign
    if build_maps.exists():
        for map_dir in sorted(build_maps.iterdir()):
            if map_dir.is_dir():
                check_map_text_dir(map_dir, map_dir.name)

    # User campaigns
    if build_user.exists():
        for campaign_dir in sorted(build_user.iterdir()):
            if not campaign_dir.is_dir():
                continue
            for map_dir in sorted(campaign_dir.iterdir()):
                if map_dir.is_dir():
                    check_map_text_dir(
                        map_dir / "currentusermap",
                        f"{campaign_dir.name}/{map_dir.name}"
                    )

    # Statistics
    main_strings = len(list(build_maps.rglob("strings.ini"))) if build_maps.exists() else 0
    user_strings = len(list(build_user.rglob("strings.ini"))) if build_user.exists() else 0
    main_files = sum(1 for _ in build_maps.rglob("*") if _.is_file()) if build_maps.exists() else 0
    user_files = sum(1 for _ in build_user.rglob("*") if _.is_file()) if build_user.exists() else 0

    print(f"  Data/maps:  {main_strings} strings.ini, {main_files} total files")
    print(f"  DataX/UserCampaigns: {user_strings} strings.ini, {user_files} total files")

    text_dst = BUILD_ROOT / "Data" / "Text"
    if text_dst.exists():
        text_files = sum(1 for _ in text_dst.rglob("*") if _.is_file())
        text_langs = [d.name for d in text_dst.iterdir() if d.is_dir()]
        print(f"  Data/Text:  {text_files} files, languages: {', '.join(text_langs)}")

    if issues:
        print(f"\n  WARNING: {len(issues)} issues:")
        for i in issues[:10]:
            print(f"    {i}")
    else:
        print(f"\n  All OK: Simplified-Chinese-only build verified")


def build_game_text(loc_tools=None):
    """Build Simplified-Chinese map text to dist/Data/ and dist/DataX/."""
    if loc_tools is None:
        sys.path.insert(0, str(TOOLS))
        import loc_tools as _lt
        loc_tools = _lt

    print(f"{'='*60}")
    print(f"  Cultures Saga Build Map Text — Simplified Chinese Only")
    print(f"  XML source: {XML_MAIN}, {XML_USER}")
    print(f"  Game reference: {GAME_DIR}")
    print(f"  Output: {BUILD_ROOT}")
    print(f"{'='*60}")

    t0 = time.time()

    ok1, skip1, dep1 = build_main_maps(loc_tools)
    ok2, skip2, dep2 = build_user_maps(loc_tools)

    # Copy supplementary assets (Localization/text/l10 → Data/Text/l10)
    print(f"\n{'='*60}")
    print(f"  Supplementary Assets (CHN only)")
    print(f"{'='*60}")
    copy_additional_assets()

    verify_build()

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Build complete! {elapsed:.0f} seconds")
    print(f"  Main campaign: {ok1} ok / {skip1} skipped / {dep1} deprecated")
    print(f"  User campaigns: {ok2} ok / {skip2} skipped / {dep2} deprecated")
    print(f"  Output: {BUILD_ROOT}")
    print(f"{'='*60}")

    return ok1, skip1, ok2, skip2


def main():
    ap = argparse.ArgumentParser(description="Build Simplified-Chinese-only maps (game directory structure)")
    ap.add_argument("--clean", action="store_true", help="Clean dist/ first, then build")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, do not build")
    args = ap.parse_args()

    # Add Tools to sys.path
    sys.path.insert(0, str(TOOLS))

    print(f"{'='*60}")
    print(f"  Cultures Saga Simplified-Chinese Map Build")
    print(f"  Project: {PROJ_ROOT}")
    print(f"  Game reference: {GAME_DIR}")
    print(f"  Output: {BUILD_ROOT}")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n  [DRY-RUN] Preview only\n")
        maps_count = len(list(XML_MAIN.glob("*.xml")))
        user_xmls = sorted(
            f for d in sorted(XML_USER.iterdir()) if d.is_dir()
            for f in sorted(d.glob("*.xml"))
        )
        print(f"  Main campaign XMLs: {maps_count}")
        print(f"  User campaign XMLs: {len(user_xmls)}")
        print(f"  Target language: {TARGET_LANG} -> text/{TARGET_TEXT_DIR}/")
        print(f"  Output directory: {BUILD_ROOT}")
        print(f"\n  Run 'python build_text_chn.py' to build")
        return

    if args.clean and BUILD_ROOT.exists():
        print(f"\n  Cleaning {BUILD_ROOT}...")
        shutil.rmtree(BUILD_ROOT)
        print("  Cleaned\n")

    import loc_tools  # noqa: E402

    build_game_text(loc_tools)


if __name__ == "__main__":
    main()

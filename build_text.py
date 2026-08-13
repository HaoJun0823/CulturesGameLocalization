# -*- coding: utf-8 -*-
"""
Cultures Saga — Multi-language Map Build Script
================================================
Build all languages from XML, output to _build/ directory,
with directory structure fully aligned to the game directory.

Usage:
  python build_text.py           # Full build (default)
  python build_text.py --clean   # Clean _build/ first, then build
  python build_text.py --dry-run # Preview only, no build

Output:
  _build/
    Data/maps/<map_id>/          → Overlay GAME_HACK/Data/maps/
    DataX/UserCampaigns/         → Overlay GAME_HACK/DataX/UserCampaigns/
    Data/Text/                   → Localization/text (game text resources)
    DataX/FMV/                   → Movie (renamed to FMV)
"""
import argparse
import csv
import shutil
import sys
import time
from pathlib import Path

# ============================================================
# Path Configuration (modify only these)
# ============================================================

# CulturesGameLocalization project root (parent of this script)
PROJ_ROOT = Path(__file__).resolve().parent

# Game reference directory (copy map.dat/map.ini/text/ger/ etc.)
GAME_DIR = Path(r"G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK")

# XML source
XML_MAIN = PROJ_ROOT / "Localization" / "map_xml"
XML_USER = PROJ_ROOT / "Localization" / "map_xml_user"

# Build output
BUILD_ROOT = PROJ_ROOT / "_build"

# Tools
TOOLS = PROJ_ROOT / "Tools"

# Additional asset sources
LOC_TEXT_SRC = PROJ_ROOT / "Localization" / "text"    # → _build/Data/Text/
MOVIE_SRC = PROJ_ROOT / "Movie"                        # → _build/DataX/FMV/


# ============================================================
# Core Logic
# ============================================================

def build_all_languages(xml_file, output_dir, loc_tools):
    """Build all languages from XML to output_dir (force_utf8=True)"""
    data = loc_tools.parse_xml_file(xml_file)
    if data.get("deprecated", False):
        return data, 0
    langs = data.get("languages", [])
    for lang in langs:
        loc_tools.build_map(xml_file, output_dir, lang, force_utf8=True)
    return data, len(langs)


def copy_missing_assets(src_text, dst_text, skip_files=None, skip_briefings=None):
    """Copy non-text resources from src_text (ger) to dst_text (other languages)"""
    if skip_files is None:
        skip_files = {"strings.ini"}
    if skip_briefings is None:
        skip_briefings = {"briefings.txt"}

    if not src_text.exists():
        return
    dst_text.mkdir(parents=True, exist_ok=True)

    for item in src_text.iterdir():
        if item.name in skip_files:
            continue
        dst_item = dst_text / item.name

        if item.name == "briefings":
            dst_item.mkdir(parents=True, exist_ok=True)
            for bf in item.iterdir():
                if bf.name in skip_briefings:
                    continue
                dst_bf = dst_item / bf.name
                if not dst_bf.exists():
                    (shutil.copytree if bf.is_dir() else shutil.copy2)(bf, dst_bf)
        elif item.is_dir():
            if not dst_item.exists():
                shutil.copytree(item, dst_item)
        else:
            if not dst_item.exists():
                shutil.copy2(item, dst_item)


def copy_additional_assets():
    """Copy supplementary assets beyond map data.

    - Localization/text/ → _build/Data/Text/  (game text resources)
    - Movie/             → _build/DataX/FMV/  (movie rarely changes, commented out)
    """
    # 1) Localization/text → _build/Data/Text
    text_dst = BUILD_ROOT / "Data" / "Text"
    if LOC_TEXT_SRC.exists():
        if text_dst.exists():
            shutil.rmtree(text_dst)
        shutil.copytree(LOC_TEXT_SRC, text_dst)
        print(f"  [OK] Localization/text → Data/Text/")
    else:
        print(f"  [Skip] Localization/text/ not found")

    # 2) Movie → _build/DataX/FMV (renamed)
    # fmv_dst = BUILD_ROOT / "DataX" / "FMV"
    # if MOVIE_SRC.exists():
    #     if fmv_dst.exists():
    #         shutil.rmtree(fmv_dst)
    #     shutil.copytree(MOVIE_SRC, fmv_dst)
    #     print(f"  [OK] Movie/ → DataX/FMV/")
    # else:
    #     print(f"  [Skip] Movie/ not found")


def build_main_maps(loc_tools):
    """Build main campaign maps (128 maps)"""
    xml_files = sorted(XML_MAIN.glob("*.xml"))
    print(f"\n{'='*60}")
    print(f"  Main Campaign: {len(xml_files)} maps")
    print(f"{'='*60}")

    src_maps = GAME_DIR / "Data" / "maps"
    build_maps = BUILD_ROOT / "Data" / "maps"

    ok = skip = 0
    for f in xml_files:
        data = loc_tools.parse_xml_file(f)
        map_id = data.get("export_map_id") or data.get("map_id") or f.stem
        target_dir = build_maps / map_id

        # 1) Copy original game data (map.dat, map.ini, text/ger/ etc.)
        src_dir = src_maps / map_id
        if src_dir.exists():
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(src_dir, target_dir)
        else:
            print(f"  [Skip] {map_id}: no game data for this map")
            skip += 1
            continue

        # 2) Build all languages from XML (overwrites text/ger/strings.ini etc.)
        data, lang_count = build_all_languages(f, build_maps, loc_tools)

        # 3) Copy ger resources to other language directories
        ger_text = target_dir / "text" / "ger"
        if ger_text.exists():
            for lang_dir in sorted(target_dir.joinpath("text").iterdir()):
                if not lang_dir.is_dir() or lang_dir.name == "ger":
                    continue
                copy_missing_assets(ger_text, lang_dir)

        print(f"  [OK] {map_id} ({lang_count} languages)")
        ok += 1

    print(f"\n  Main Campaign: {ok} ok, {skip} skipped\n")
    return ok, skip


def build_user_maps(loc_tools):
    """Build user campaign maps (28 maps)"""
    user_xmls = sorted(
        f for d in sorted(XML_USER.iterdir()) if d.is_dir()
        for f in sorted(d.glob("*.xml"))
    )
    print(f"{'='*60}")
    print(f"  User Campaigns: {len(user_xmls)} maps")
    print(f"{'='*60}")

    src_user = GAME_DIR / "DataX" / "UserCampaigns"
    build_user = BUILD_ROOT / "DataX" / "UserCampaigns"

    ok = skip = 0
    for f in user_xmls:
        campaign = f.parent.name  # Campaign00 / Campaign01
        data = loc_tools.parse_xml_file(f)
        map_id = data.get("export_map_id") or data.get("map_id") or f.stem
        target_dir = build_user / campaign / map_id / "currentusermap"

        # 1) Copy original game data (including text/ger/ full resources)
        src_dir = src_user / campaign / map_id / "currentusermap"
        if src_dir.exists():
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(src_dir, target_dir)
        else:
            print(f"  [Skip] {campaign}/{map_id}: no game data")
            skip += 1
            continue

        # 2) Build all languages from XML
        data, lang_count = build_all_languages(f, build_user / campaign, loc_tools)

        # 3) Copy ger resources to other languages
        ger_text = target_dir / "text" / "ger"
        if ger_text.exists():
            for lang_dir in sorted(target_dir.joinpath("text").iterdir()):
                if not lang_dir.is_dir() or lang_dir.name == "ger":
                    continue
                copy_missing_assets(ger_text, lang_dir)

        print(f"  [OK] {campaign}/{map_id} ({lang_count} languages)")
        ok += 1

    print(f"\n  User Campaigns: {ok} ok, {skip} skipped\n")
    return ok, skip


def build_game_text(loc_tools=None):
    """Build all language map text to _build/Data/ and _build/DataX/.

    Copies complete map data from GAME_DIR/Data/ (map.dat, map.ini, text/ger/ etc.)
    to _build/Data/, then overlays all language text files (strings.ini, briefings.txt)
    from XML, and copies ger resource files (.hlt/.fnt/.pcx/.bmp) to other language dirs.

    Also copies supplementary assets:
      - Localization/text/  → _build/Data/Text/
      - Movie/              → _build/DataX/FMV/

    Returns (main_ok, main_skip, user_ok, user_skip)
    """
    if loc_tools is None:
        sys.path.insert(0, str(TOOLS))
        import loc_tools as _lt
        loc_tools = _lt

    print(f"{'='*60}")
    print(f"  Cultures Saga Build Map Text")
    print(f"  XML source: {XML_MAIN}, {XML_USER}")
    print(f"  Game reference: {GAME_DIR}")
    print(f"  Output: {BUILD_ROOT}")
    print(f"{'='*60}")

    t0 = time.time()

    ok1, skip1 = build_main_maps(loc_tools)
    ok2, skip2 = build_user_maps(loc_tools)

    # Copy supplementary assets (Localization/text → Data/Text, Movie → DataX/FMV)
    print(f"\n{'='*60}")
    print(f"  Supplementary Assets")
    print(f"{'='*60}")
    copy_additional_assets()

    verify_build()
    generate_languages_csv()

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Build complete! {elapsed:.0f} seconds")
    print(f"  Main campaign: {ok1} ok / {skip1} skipped")
    print(f"  User campaigns: {ok2} ok / {skip2} skipped")
    print(f"  Output: {BUILD_ROOT}")
    print(f"{'='*60}")

    return ok1, skip1, ok2, skip2


def verify_build():
    """Verify build output integrity"""
    print(f"{'='*60}")
    print(f"  Verification")
    print(f"{'='*60}")

    build_maps = BUILD_ROOT / "Data" / "maps"
    build_user = BUILD_ROOT / "DataX" / "UserCampaigns"

    issues = []

    # Main campaign
    if build_maps.exists():
        for map_dir in sorted(build_maps.iterdir()):
            if not map_dir.is_dir():
                continue
            text_dir = map_dir / "text"
            if not text_dir.exists():
                issues.append(f"{map_dir.name}: missing text/ directory")
                continue
            ger_text = text_dir / "ger"
            if not ger_text.exists():
                issues.append(f"{map_dir.name}: missing text/ger/")
                continue
            ger_hlt = len(list(ger_text.rglob("*.hlt")))
            for lang_dir in sorted(text_dir.iterdir()):
                if not lang_dir.is_dir() or lang_dir.name == "ger":
                    continue
                lang_hlt = len(list(lang_dir.rglob("*.hlt")))
                if lang_hlt < ger_hlt:
                    issues.append(
                        f"{map_dir.name}/{lang_dir.name}: "
                        f"ger={ger_hlt}hlt, {lang_dir.name}={lang_hlt}hlt"
                    )

    # User campaigns
    if build_user.exists():
        for campaign_dir in sorted(build_user.iterdir()):
            if not campaign_dir.is_dir():
                continue
            for map_dir in sorted(campaign_dir.iterdir()):
                if not map_dir.is_dir():
                    continue
                text_dir = map_dir / "currentusermap" / "text"
                if not text_dir.exists():
                    continue
                ger_text = text_dir / "ger"
                if not ger_text.exists():
                    continue
                ger_hlt = len(list(ger_text.rglob("*.hlt")))
                for lang_dir in sorted(text_dir.iterdir()):
                    if not lang_dir.is_dir() or lang_dir.name == "ger":
                        continue
                    lang_hlt = len(list(lang_dir.rglob("*.hlt")))
                    if lang_hlt < ger_hlt:
                        issues.append(
                            f"{campaign_dir.name}/{map_dir.name}/{lang_dir.name}: "
                            f"ger={ger_hlt}hlt, {lang_dir.name}={lang_hlt}hlt"
                        )

    # Statistics
    main_strings = len(list(build_maps.rglob("strings.ini")))
    user_strings = len(list(build_user.rglob("strings.ini")))
    main_files = sum(1 for _ in build_maps.rglob("*") if _.is_file())
    user_files = sum(1 for _ in build_user.rglob("*") if _.is_file())

    print(f"  Data/maps:  {main_strings} strings.ini, {main_files} total files")
    print(f"  DataX/UserCampaigns: {user_strings} strings.ini, {user_files} total files")

    # Check supplementary assets
    text_dst = BUILD_ROOT / "Data" / "Text"
    if text_dst.exists():
        text_files = sum(1 for _ in text_dst.rglob("*") if _.is_file())
        print(f"  Data/Text:  {text_files} files")

    fmv_dst = BUILD_ROOT / "DataX" / "FMV"
    if fmv_dst.exists():
        fmv_files = sum(1 for _ in fmv_dst.rglob("*") if _.is_file())
        print(f"  DataX/FMV:  {fmv_files} files")

    if issues:
        print(f"\n  ⚠️ {len(issues)} issues:")
        for i in issues[:10]:
            print(f"    {i}")
    else:
        print(f"\n  ✅ All language resource files complete")


def generate_languages_csv():
    """Scan build output and write a CSV listing languages per map.

    Output: _build/map_languages.csv  (UTF-8 BOM, human/Excel friendly)
    """
    build_maps = BUILD_ROOT / "Data" / "maps"
    build_user = BUILD_ROOT / "DataX" / "UserCampaigns"

    rows = []

    # Main campaign maps
    if build_maps.exists():
        for map_dir in sorted(build_maps.iterdir()):
            if not map_dir.is_dir():
                continue
            text_dir = map_dir / "text"
            if not text_dir.exists():
                rows.append({"type": "main", "map_id": map_dir.name, "languages": ""})
                continue
            langs = sorted(
                d.name for d in text_dir.iterdir()
                if d.is_dir() and d.name != "ger" and (d / "strings.ini").exists()
            )
            all_langs = ["ger"] + langs
            rows.append({"type": "main", "map_id": map_dir.name, "languages": ",".join(all_langs)})

    # User campaign maps
    if build_user.exists():
        for campaign_dir in sorted(build_user.iterdir()):
            if not campaign_dir.is_dir():
                continue
            for map_dir in sorted(campaign_dir.iterdir()):
                if not map_dir.is_dir():
                    continue
                cur = map_dir / "currentusermap"
                text_dir = cur / "text"
                if not text_dir.exists():
                    rows.append({
                        "type": f"user_{campaign_dir.name}",
                        "map_id": map_dir.name,
                        "languages": ""
                    })
                    continue
                langs = sorted(
                    d.name for d in text_dir.iterdir()
                    if d.is_dir() and d.name != "ger" and (d / "strings.ini").exists()
                )
                all_langs = ["ger"] + langs
                rows.append({
                    "type": f"user_{campaign_dir.name}",
                    "map_id": map_dir.name,
                    "languages": ",".join(all_langs)
                })

    # Write CSV (UTF-8 BOM for Excel compat)
    csv_path = BUILD_ROOT / "map_languages.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["type", "map_id", "languages"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Languages CSV: {csv_path} ({len(rows)} maps)")
    return rows


def main():
    ap = argparse.ArgumentParser(description="Build multi-language maps (game directory structure)")
    ap.add_argument("--clean", action="store_true", help="Clean _build/ first, then build")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, do not build")
    ap.add_argument("--no-movies", action="store_true", help="Ignore copy movies.")
    args = ap.parse_args()

    # Add Tools to sys.path
    sys.path.insert(0, str(TOOLS))

    print(f"{'='*60}")
    print(f"  Cultures Saga Multi-language Map Build")
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
        print(f"  Output directory: {BUILD_ROOT}")
        print(f"\n  Run 'python build_text.py' or double-click build_text.bat to build")
        return

    if args.clean and BUILD_ROOT.exists():
        print(f"\n  Cleaning {BUILD_ROOT}...")
        shutil.rmtree(BUILD_ROOT)
        print("  Cleaned\n")

    import loc_tools  # noqa: E402

    build_game_text(loc_tools)


if __name__ == "__main__":
    main()
# Cultures Saga — Simplified Chinese Localization

> **License: GNU General Public License v3.0-or-later (GPL-3.0-or-later)**
> Copyright (C) 2026 CulturesGameExtend & CulturesGameLocalization 贡献者
>
> This project is free software released under the GPL-3.0-or-later. You may
> redistribute and/or modify it under the terms of the GNU General Public License as
> published by the Free Software Foundation. See [`LICENSE`](./LICENSE).
>
> **Upstream / third-party attribution (license retained):**
> - Map format tooling under `Tools/Cultures-map-editor/` is the **Mikulus6/Cultures-map-editor**
>   project (GPL-3.0), derived from the 2010 XeNTaX forums cif research. Its original
>   copyright notice is preserved in that directory.
> - Any content/code added by the contributors of *CulturesGameLocalization* is
>   Copyright (C) 2026 the respective contributors and licensed under GPL-3.0-or-later.

Map and text localization pack for **Cultures: The Gates of Asgard** (2nd generation), translating **German → Simplified Chinese (l10)**.

> Localization sources live under `Localization/map_xml/`, `Localization/map_xml_user/`, and `Localization/text/l10/`. Every map XML contains multi-language strings (CHN/ger/eng/pol) plus briefings. All translations pass zero-empty-slot, structure-validity, and `@`-prefix-balance audits.

## Related Projects / 关联项目

- **CulturesGameExtend** — the community extension DLL that actually loads this
  project's Simplified-Chinese (`l10`) text and map content in-game via a UTF-8
  text engine. The two repos are separate; build/deploy the DLL from that repo
  and drop `CulturesGameExtend.dll` (+ `plugins/`) into the game folder
  (or set `CULTURES_EXTEND_DIR` when running `build_text.py`).
  <https://github.com/HaoJun0823/CulturesGameExtend>

## Installation

1. **Back up** the original `Data/maps/` and `Data/text/` directories in your game folder.
2. Run `build_text.py` in the game directory (see "Build & Deploy" below), or download a pre-built release zip from [Releases](https://github.com/HaoJun0823/CulturesGameLocalization/releases) and extract it into the game folder.
3. Launch the game with language set to **German (GER)** — GER is the alignment anchor, the Chinese (l10) content is loaded by an external hook.

> ⚠️ Keep the directory structure intact. Both `_campaign_04_*` and `campaign_04_*` map files are required.

## Repository Structure

```
CulturesGameLocalization/
├── Localization/            # Localization source files
│   ├── map_xml/             # 128 main-campaign map XMLs (CHN/ger/eng/pol)
│   ├── map_xml_user/        # 28 C2M user-campaign map XMLs
│   └── text/                # Game system text (ger source + l10 Chinese)
├── Tools/                   # Localization toolchain
│   ├── loc_tools.py         # XML parsing core + build tool (primary dependency)
│   ├── deploy_all.py        # Deploy to game directory
│   └── fix_xml_names.py     # Fix umlaut characters in XML filenames
├── archives/                # Archived legacy tools and audit reports
├── build_text.py            # Main build script (multi-language → _build/)
├── convert_text_utf8.py     # Batch convert text files to UTF-8
├── publish_build.py         # Local build + zip + GitHub Release publish
├── Game_FileSystem_Intro.md # Game filesystem structure reference
└── .github/workflows/       # GitHub Actions CI/CD
```

## Supported Languages

| Code | Language | Notes |
|------|----------|-------|
| `ger` | German | Official source language, always present |
| `eng` | English | Extracted and merged from GAME_2/3/4 data |
| `pol` | Polish | Extracted and merged from GAME_2 data |
| `l10` | Chinese (Simplified) | Localization target, loaded by external hook |

## Build & Deploy

### Full Build (Local, Recommended)

```bash
# One-shot build: parse XMLs → generate all languages → package
python build_text.py          # Full build (default)
python build_text.py --clean  # Clean _build/ first, then build
python build_text.py --dry-run # Preview only

# After every build, map_languages.csv is generated automatically
# listing every map and its available languages
```

The `_build/` output mirrors the game directory structure and can be copied directly:

| Build output | Game target |
|-------------|-------------|
| `_build/Data/maps/<map_id>/` | `GAME_DIR/Data/maps/<map_id>/` |
| `_build/DataX/UserCampaigns/` | `GAME_DIR/DataX/UserCampaigns/` |
| `_build/Data/Text/` | `GAME_DIR/Data/Text/` |

> **Note:** `GAME_DIR` (the game reference directory containing `Data/maps` etc.) must be configured at the top of `build_text.py`.

### UTF-8 Conversion

```bash
python convert_text_utf8.py          # Convert all .ini/.txt in Localization/text/ to UTF-8
python convert_text_utf8.py --dry-run # Preview only
python convert_text_utf8.py --all    # Include _backup directories
```

## Publishing to GitHub Releases

### Local Publish (Full Build, Recommended)

```bash
python publish_build.py                  # build → zip → publish Release
python publish_build.py --no-build       # Reuse existing _build/ for packaging
python publish_build.py --tag v1.0       # Custom release tag
python publish_build.py --dry-run        # Package only, no release
```

Requires [gh CLI](https://cli.github.com/) installed and authenticated:
```bash
winget install GitHub.cli
gh auth login
```

### CI via GitHub Actions

Go to the **Actions** tab → **Build & Release** → **Run workflow** (optional: set `release_tag` / `game_data_url`).

> ⚠️ Game map data (SAGA_GAME_HACK/Data/maps/) is **not** in the repository. For the first CI build, upload it once:
> `gh release upload <tag> game-data.tar.gz --clobber`
> Or provide a direct download URL via the `game_data_url` input. Without game data, map building is skipped and only `Data/Text/` plus supplementary assets are published.

## FAQ

- **Release zip has no maps?** The CI build lacked `GAME_DIR` source data. Use `publish_build.py` locally instead.
- **Chinese text shows garbled?** Make sure the game launches with **German (GER)** selected — the Chinese (l10) content is loaded by an external hook.
- **Encoding issues:** The game only supports GB2312. `loc_tools.py build` has built-in GB2312 compatibility handling (`--` for dashes, `・` for name separators, alternative character substitutions).

## Disclaimer

This is a fan-made localization project for educational and exchange purposes only. All game assets are the property of the original developers and publishers. Not for commercial use.

---

## Upstream Credits / 上游致谢

This project's map-format tooling (and documentation) is derived from the
**Cultures2-dat-format** project. The exact scope of what was reused depends on
the files and links referenced in that upstream repository; we thank its
contributors for their research and tooling.

### Contributors（上游贡献者）

- [Mikulus](https://github.com/Mikulus6): Managed project and wrote Python code.
- [Basssiiie](https://github.com/Basssiiie): Decompiled parts of the game's engine via Ghidra.
- [Rumu](https://github.com/Rumu121/): Helped with empirical verifications in game.
- [Push42](https://github.com/push42): Helped with walk sectors data interpretation.

### Literature（上游文献）

- [Watto](https://github.com/wattostudios): "*Game Extractor*" (2004)
- [Bacter](mailto:the.bacter@gmail.com): "*Unknown Encryption In Cultures Game*" (2010) — <https://web.archive.org/web/20210724220815/https://forum.xentax.com/viewtopic.php?t=3711>
- [Red Blob Games](https://www.redblobgames.com/): "*Hexagonal Grids*" (2013) — <https://www.redblobgames.com/grids/hexagons/>
- [Siguza](https://github.com/Siguza): "*Cultures 2 file formats*" (2013) — <https://web.archive.org/web/20210724220815/https://forum.xentax.com/viewtopic.php?t=10705>
- [Nithanim](https://github.com/Nithanim): "*Northland or 8th Wonder of the World map.dat file format*" (2019) — <https://gist.github.com/Nithanim/766c31475377b0bd594bab974a1de8d2>
- [Martianboy](https://github.com/martianboy): "*cultures2-engine*" (2020) — <https://github.com/martianboy/cultures2-engine>
- [Mikulus](https://github.com/Mikulus6): "*Cultures map editor*" (2025) — <https://github.com/Mikulus6/Cultures-map-editor>

> *Cultures* is the property of [Funatics Development](https://www.funatics.de/) with all
> rights reserved; it is not covered by the GPL-3.0-or-later license.
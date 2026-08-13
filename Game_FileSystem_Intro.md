# Game File System Introduction

This document describes the file system structure of *Cultures: The Gates of Asgard* (SAGA_GAME) and the modded version (SAGA_GAME_HACK).

## File Types

| Extension | Description |
|-----------|-------------|
| `.hlt` | Script file for hypertext content — mission briefings, encyclopedia, knowledge base text with embedded graphics/formatting. |
| `.fnt` | Font file — sprite-based bitmap font used for in-game text rendering. |
| `.bmd` | 2D image storage, requires a `.pcx` palette file to render. |
| `.cif` | Serialized (encrypted) `.ini` file. The game engine reads `.cif` by default; if a plain `.ini` with the same name exists, it takes priority. |
| `.ini` | Game data configuration. Also contains localizable text strings (`strings.ini`). |
| `.pcx` | Palette file or 2D image — used as color palette for `.bmd` files, or as standalone graphics (backgrounds, buttons). |
| `.map.dat` | Binary map data file — stores terrain, objects, units, triggers, and scripting for a single map. |
| `.map.ini` | Map metadata — name, description, author, language, campaign info. |
| `.map.cif` | Encrypted map initialization file (same as `map.ini` but in `.cif` format). |
| `.wav` | Sound effect / voice-over audio. |
| `.mpg` | Full-motion video (FMV) — cutscenes and intro movies. |
| `.bik` | Bink video format — older FMV format, no longer supported by the current game build. |
| `.c2m` | Packed user campaign map — single-file archive containing `map.dat`, `map.ini`, `text/`, `sfx/`. |
| `.dls` | DirectMusic style — downloadable sound bank for MIDI-based music. |
| `.lib` | Game data archive — a single file containing many game assets (e.g. `data0001.lib`). Data is loaded from the `.lib` archive unless a corresponding file exists in the `Data/` directory tree (which takes priority). |

## Folder Structure

### `/` (Game Root)

| File / Dir | Description |
|------------|-------------|
| `Game.exe` | Main game executable. |
| `Game.ini` | Game configuration — language, resolution, renderer settings. |
| `GameMp.exe` | Multiplayer executable. |
| `Editor.exe` | Map editor executable. |
| `Data/` | Game data — maps, engine, GUI, logic, text. |
| `DataX/` | Extended data — FMV, music, user campaigns, pictures, DLL libraries. |
| `Editor/` | Map editor support files. |
| `Handbuch/` | Game manual (PDF). |

---

### `Data/` — Core Game Data

Preferred over `data0001.lib` — files placed here shadow the archive.

#### `Data/maps/`

Contains all campaign and single-player maps. Each map is a directory named by its map ID (e.g. `campaign_01_01`, `demo_mainmenu_10`).

**Map directory structure:**

```
<map_id>/
├── map.dat          # Binary map data (terrain, objects, triggers, scripts)
├── map.ini          # Map metadata (name, description, campaign affiliation)
├── map.cif          # Encrypted version of map.ini (optional, ini takes priority)
├── text/            # Localized text content
│   ├── ger/         # German (source language)
│   │   ├── strings.ini       # All UI strings for this map
│   │   ├── strings.cif       # Encrypted version of strings.ini
│   │   └── briefings/        # Mission briefing hypertext files
│   │       ├── 0000.hlt      # Script file for first briefing page
│   │       ├── briefings.txt # Briefing text source
│   │       ├── fonts/        # Font files for briefings
│   │       ├── graphics/     # Briefing images (.pcx)
│   │       └── palettes/     # Color palettes (.pcx, .bmp)
│   ├── eng/         # English (if available)
│   ├── pol/         # Polish (if available)
│   └── l10/         # Chinese localization (mod-added, loaded by external hook)
│       ├── strings.ini
│       └── briefings/
│           ├── 0000.hlt
│           ├── briefings.txt
│           ├── fonts/
│           ├── graphics/
│           └── palettes/
└── sfx/             # Voice-over audio files (.wav)
```

**Notes:**
- The original game (SAGA_GAME) has **85 maps** (GER only).
- The modded version (SAGA_GAME_HACK) has **128 maps** (with campaign_04 expansion and l10 Chinese).
- Maps from `data0001.lib` can be extracted and placed here to override the archived version.

#### `Data/text/`

Global system text — not map-specific.

```
Data/text/<lang>/
├── hypertext/           # Encyclopedia, history, mythology, help
│   ├── history/         # History timeline
│   │   ├── history.txt
│   │   ├── mythology.txt
│   │   ├── *.hlt        # Hypertext script files
│   │   ├── fonts/
│   │   ├── graphics/
│   │   └── palettes/
│   ├── mythology/       # Norse mythology
│   ├── ingamehelp/      # Keyboard help / controls
│   └── credits/         # Game credits
└── strings/             # Global game strings
    ├── gameobjects/     # Goods, houses, jobs, vehicles, tribes, etc.
    ├── ingamegui/       # UI windows, main menu, messages
    ├── mainmenu/
    ├── demoversion/
    ├── help/            # Tooltip help text
    ├── odin/            # Odin campaign strings
    ├── saga/            # Saga campaign strings
    ├── updates/         # Patch notes
    └── wonders/         # Wonders of the world
```

- The original game has only `ger/` (German).
- The modded game (SAGA_GAME_HACK) adds `l10/` (Chinese), loaded by an external hook DLL.

#### `Data/logic/`

Gameplay data definitions — each has a `.cif` (encrypted) and `.ini` (plain text) pair.

```
animaltypes, armortypes, goodtypes, housetypes, jobtypes,
humanjobexperiencetypes, landscapetypes, trianglepatterntypes,
vehicletypes, weapontypes, tribetypes/
```

#### `Data/engine2d/`

| Path | Description |
|------|-------------|
| `bin/bobs/` | 201 animated sprite objects (characters, buildings, effects) |
| `bin/palettes/` | 5 engine color palettes |
| `bin/sounds/` | 7 engine sound effects |
| `bin/textures/` | 90 terrain textures |
| `inis/` | Engine behavior configuration (animals, goods, houses, humans, landscapes, particles, etc.) |

#### `Data/gui/`

| Path | Description |
|------|-------------|
| `bitmaps/` | UI background images (`.pcx`) |
| `fonts/` | UI bitmap fonts (`font08.fnt` through `font12.fnt`) |
| `lang/<lang>/` | GUI language strings (e.g., `ger/` for German) |
| `palettes/` | UI color palettes (button states, bars, campaign map) |

#### `Data/edit/`

Map editor support files.

| Path | Description |
|------|-------------|
| `macromaps/` | Predefined macro-map templates |
| `mapgeneration/` | Landscape generation rules |
| `misc/` | Editor palette file |
| `randomgroups/` | Random group placement presets |

---

### `DataX/` — Extended Data

#### `DataX/FMV/`

Full-motion videos (cutscenes, intro). Organized by language:

```
FMV/
├── Ger/       # German intro movies
│   ├── intro.mpg
│   ├── intro01.mpg
│   ├── intro02.mpg
│   ├── Seq_0001.mpg
│   └── Seq_0002.mpg
├── Eng/       # English (mod-added)
└── L10/       # Chinese (mod-added)
```

#### `DataX/UserCampaigns/`

User-created campaigns. Each campaign is a directory; each map within is either a `.c2m` archive (original game) or an unpacked directory (modded game).

```
UserCampaigns/
├── Campaign00/           # First user campaign (22 maps)
│   ├── 01_Ein_neuer_Anfang.c2m    # .c2m packed map (original)
│   ├── 01_Ein_neuer_Anfang/       # Unpacked directory (modded)
│   │   ├── currentusermap/
│   │   │   ├── map.dat
│   │   │   ├── map.ini
│   │   │   └── text/
│   │   │       ├── ger/
│   │   │       └── l10/
│   └── ...
└── Campaign01/           # Second user campaign (6 maps)
    └── ...
```

#### `DataX/DM2/`

113 DirectMusic style files (`.dls`) — MIDI-based music/sound banks.

#### `DataX/Libs/`

| File | Description |
|------|-------------|
| `data0001.lib` | Main game data archive — contains all default game assets. Files in `Data/` override this archive. |
| `t.dat` | Additional data file |

#### `DataX/Mouse/`

Mouse cursor graphics (`.cur` files):
- `MouseNormal.cur` — default cursor
- `MousePressed.cur` — click cursor
- `MouseRight.cur` — right-click cursor

#### `DataX/Pictures/`

Title/loading screen images:
- `post00.bmp` — post-loading screen
- `pre00.bmp` — pre-loading screen

---

### `Editor/` — Map Editor Support

```
Editor/
└── Premaps/          # Pre-made maps for the editor (template files)
```

---

## Language Directory Convention

| Code | Language | Notes |
|------|----------|-------|
| `ger` | German | Source language, always present |
| `eng` | English | Available for some maps |
| `pol` | Polish | Available for some maps |
| `l10` | Chinese (Simplified) | Mod-added localization target; loaded by external hook, not by the game natively |

Within a map's `text/` directory, each language folder mirrors the same structure (`strings.ini`, `briefings/`).

## Original Game vs. Modded Version

| Aspect | SAGA_GAME | SAGA_GAME_HACK |
|--------|-----------|----------------|
| Maps | 85 (original campaigns) | 128 (85 original + campaign_04 expansion) |
| Text languages | `ger` only | `ger` + `l10` (Chinese) |
| FMV languages | `Ger` | `Ger`, `Eng`, `L10` |
| UserCampaigns | `.c2m` packed archives | Unpacked directories with `currentusermap/` |
| Purpose | Original game installation | Modded installation with Chinese localization |

## Asset Loading Priority

1. **Files in `Data/`** — override the lib archive (highest priority)
2. **`DataX/Libs/data0001.lib`** — default game archive
3. **Within a language directory**: `.ini` files take priority over `.cif` files with the same name
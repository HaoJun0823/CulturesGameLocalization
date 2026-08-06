# Tools/ —— 汉化工具链说明

本目录收录汉化流程中**仍在使用的工具**。所有工具为只读/校验类，
**不会修改 `Localization/ZH-CN/` 下的译文**（`translate_cli.py` 的 `repair`/`inject`
属于主动修复操作，见下）。

> 目录命名：汉化内容位于 `Localization/ZH-CN/`（旧称 `GAME_CHN` / `LOC_CN`，为对位游戏安装目录曾用名）。

## 总览

```
汉化内容（源）                        构建/校验工具                    交付物
────────────────────                ───────────────────            ─────────────
Localization/ZH-CN/
├── map_xml/      128 主战役 XML  ──► translate_cli.py  ──►        Output/<map>/text/l10/
├── map_xml_user/  28 C2M 地图 XML ─► loc_tools.py build ──►       strings.ini + briefings.txt
├── text/l10/      游戏内字符串+超文本                              （游戏可加载，GB2312）
│
language_union.csv（术语表）
    ▲
    └── trans_scan.py / audit_all_maps.py —— 质量校验
```

**Python 版本要求**：`audit_all_maps.py`、`loc_tools.py` 使用了 `match` 语句，需 **Python 3.10+**；
其余工具兼容 Python 3.8+。全部仅依赖标准库。

## 工具清单（按用途分类）

### 一、主流程工具

#### `translate_cli.py` — 统一汉化 CLI（主工具）

- **用途**：单文件入口，替代旧散装 `trans_*.py` / `inject.py` / `selfcheck.py`：
  - `scan` 盘点 128 个 XML 的完成度(A/B/C)、CRLF、GER 污染
  - `repair` 内容保全式修复非法 XML 结构（补 `<briefings>`、修被吃的首个 `<block id>`），先过 minidom 校验、不合法绝不落盘
  - `verify` 校验单文件：XML 解析 / CRLF / CHN 槽数==GER / 空 CHN
  - `inject` 从 `archive/` 读取翻译字典注入（archive 未随仓库分发，仅本地可用）
  - `commit` 在仓库根执行 git 提交
- **路径**：自动定位到本文件上一级 `Localization/ZH-CN/` 下的 `map_xml`，不依赖本机绝对路径。
- **用法**：
  ```bash
  python Tools/translate_cli.py scan
  python Tools/translate_cli.py verify              # 校验全部（无参 = 全部 128）
  python Tools/translate_cli.py verify campaign_01_01.xml   # 传文件名（相对 map_xml）
  python Tools/translate_cli.py repair [files...] [--apply]
  ```
- **注意**：
  - `verify`/`repair` 参数传**文件名**（相对 `map_xml/`），不要传全路径。
  - ⚠️ **`scan` 的完成度判断对 map_xml 结构存在误报**（用 `<lang code="CHN">` 正则，
    实际结构是 `<text lang="CHN">`），**验收一律以 `audit_all_maps.py` 为准**，见下。

#### `loc_tools.py` — XML 解析核心库 + 构建工具（依赖库）

- **用途**：用 `xml.etree.ElementTree` 解析地图 XML，
  按结构读出 `strings[sid]` 与 `briefings[bid]` 的各语言文本（GER/ENG/POL/CHN）。
- **谁依赖它**：`audit_all_maps.py`、`build_maps_from_versions.py` 都 `import` 它。
- **CLI 子命令**（`python Tools/loc_tools.py <cmd> --help`）：
  - `extract` / `extract-batch` 从游戏源数据提取为 XML
  - `build` 从 XML 构建游戏可加载的 ini/txt——构建 CHN 时**用 GB2312 编码**
    （游戏仅支持 GB2312；汉化源文本已保证 GB2312 兼容：破折号用 `--`、
    人名间隔号用 `・`、瞭望塔/瞭望手→哨塔/哨兵、神祇→神明、脅→威胁），
    briefings 的 **block id 自动 ASCII 化**（`10minutenspäter` → `10minutenspaeter`，
    官方汉化同策略），中文输出目录统一为 **`text/l10/`**（主战役与 C2M 一致，
    项目规范「chn输出为l10」；l10 是外挂汉化注入的目标语言目录，与源数据语言目录无关）
  - `validate` 校验 XML 完整性
- **注意**：它是共享库，也是带 CLI 的工具（Python 3.10+）。

### 二、质量校验工具

#### `audit_all_maps.py` — 全量三重审计（**验收标准**）

- **用途**：对 128 个主战役 + 28 个用户战役做：
  1. **合法性**：XML 可解析？
  2. **正确性**：目标语言槽数/段数 == 源语言？`@` 前缀是否平衡？
  3. **完整性**：目标语言空槽是否为零？
- **语言对比可参数化**：默认 `ger -> CHN`，可用 `--src-lang` / `--dst-lang`
  指定**任意两个语言**（如 `--src-lang eng --dst-lang CHN`）；`--list-langs`
  可列出各文件实际可用语言。
- **为什么用它**：CLI 的 `scan`/`verify` 用正则判断结构，对 `map_xml` 的
  `<text lang="CHN">` 结构存在误报；本工具走真解析，是唯一可靠的验收口径。
- **用法**：
  ```bash
  python Tools/audit_all_maps.py                          # ger -> CHN
  python Tools/audit_all_maps.py --src-lang eng --dst-lang CHN
  python Tools/audit_all_maps.py --list-langs
  ```
- 会自动定位仓库根下的 `Localization/ZH-CN/`，不依赖本机绝对路径。
- 输出：`map_xml` / `map_xml_user` 两段独立审计（非法数 / 空槽 / 残余源语言 / 段数对齐），
  结尾给总体 PASS/CHECK。退出码 0=全通过，1=有问题。
- 当前状态：**map_xml 128/128 完全完成（5054/5054 槽位 100%）**、map_xml_user 28/28 完成。

#### `trans_scan.py` — 待译空槽扫描

- **用途**：列出某个 XML 文件中所有「源语言有原文、目标语言为空」的槽位，附源语言原文预览，
  便于逐条翻译或核对遗漏。
- **语言对比可参数化**：默认 `ger -> CHN`，可用 `--src-lang` / `--dst-lang` 指定任意两语言。
- **用法**：
  ```bash
  python Tools/trans_scan.py <xml路径>                     # 单文件（ger->CHN）
  python Tools/trans_scan.py <xml路径> --src-lang ger --dst-lang eng
  python Tools/trans_scan.py                                # 扫全部（默认 map_xml/*.xml）
  ```
- 输出：按 block/string 分组列出空槽与源语言预览，末尾汇总空槽总数。

### 三、构建/转换工具

#### `scan_map_dat.py` — 递归扫描 map.dat 生成索引 CSV

- **用途**：递归搜索输入目录下所有 `map.dat`，计算 MD5，输出 CSV
  （map_id, md5, map_path, lang_root），供 `build_maps_from_csv.py` 按 MD5 关联源地图数据。
- **特性**：C2M 解包态（map.dat 在 `currentusermap/` 内）自动取地图真实 ID（父目录名）。
- **用法**：
  ```bash
  python Tools/scan_map_dat.py "G:/.../GAME_5_MAP/GER" "G:/.../GAME_2_MAP/GER" --output map_index.csv
  ```

#### `build_maps_from_csv.py` — 按 CSV 索引整合输出完整地图

- **用途**：读 CSV（`scan_map_dat.py` 生成），对每个 XML 用其 `map_md5` 找到源地图目录，
  调用 `loc_tools.build_map` 复制源数据（map.cif/dat/ini + sfx）+ 写入中文 `text/l10/`；
  **IsC2M=true 的 XML 自动打包为 .c2m**（包内带 `currentusermap\` 前缀 + 源 text/ger 原文 + 中文 l10）。
- **用法**：
  ```bash
  # 先建索引
  python Tools/scan_map_dat.py "G:/.../GAME_5_MAP/GER" --output map_index.csv
  # 整合输出（目录或单文件）
  python Tools/build_maps_from_csv.py --input Localization/ZH-CN/map_xml --csv map_index.csv --output Output
  python Tools/build_maps_from_csv.py --input Localization/ZH-CN/map_xml_user --csv map_index.csv --output Output
  ```
- **参数**：`--lang`（默认 CHN）、`--keep-c2m-dir`（C2M 打包后保留中间目录）。

#### `cultures2_converter.py` — Cultures 2 ini/cif 转换 + c2m 打包解包

- **用途**：独立 CLI 工具，提取自 [Cultures-map-editor](https://github.com/Mikulus6/Cultures-map-editor)
  （CulturesNation 社区，GPL-3.0）：
  - `cif2ini <in.cif> [out.ini]` —— 解密的 Cultures 2 初始化文件转 ini 文本
  - `ini2cif <in.ini> [out.cif]` —— ini 文本加密回 cif（往返字节级一致）
  - `c2m-unpack <in.c2m> [out_dir]` —— 解包用户战役 c2m 归档
  - `c2m-pack <in_dir> [out.c2m]` —— 打包目录为 c2m（输入含 `currentusermap/` 时自动识别为归档根）
- **依赖**：仅标准库，无第三方依赖。
- **致谢/版权**：见脚本头部 docstring（原项目作者 Mikulus 及贡献者、格式研究文献 Bacter/Siguza/Watto、GPL-3.0 许可）。

#### `build_maps_from_versions.py` — 按版本表构建地图本地化 XML

- **用途**：读取 `translation_version_choose.csv`（map_id, version_choose 两列），
  按每个地图指定的游戏版本（2/3/5），从源数据 `GAME_<v>_MAP/` 中提取
  `strings.ini` + `briefings.txt`，构建为 XML（自动合并该版本下所有可用语言：
  GER / ENG / POL），输出到 `Output/`。
- **典型场景**：从德语原版游戏数据重新生成 132 张地图的本地化 XML 模板
  （85 张取 GAME_5、46 张取 GAME_2、1 张取 GAME_3）。
- **用法**：
  ```bash
  python Tools/build_maps_from_versions.py \
      --csv translation_version_choose.csv \
      --src "G:/Projects/Cultures_Saga_CN" \
      --output Output
  ```
- **注意**：`--src` 指向包含 `GAME_2_MAP` / `GAME_3_MAP` / `GAME_5_MAP`
  的源数据根目录（游戏原始数据不随本仓库分发）。

## 典型工作流

### 日常维护（翻译者）

```bash
# 1. 盘点当前完成度（快速，仅参考）
python Tools/translate_cli.py scan

# 2. 找出某地图的待译空槽，对照德语原文逐条翻译（改 XML）
python Tools/trans_scan.py Localization/ZH-CN/map_xml/campaign_01_01.xml

# 3. 校验修改后的单文件
python Tools/translate_cli.py verify campaign_01_01.xml
```

### 验收（提交前）

```bash
# 全量三重审计（权威口径，替代 scan）
python Tools/audit_all_maps.py

# 任意语言对比（如 eng -> CHN）
python Tools/audit_all_maps.py --src-lang eng --dst-lang CHN
```

### 发布（构建游戏可加载文件）

```bash
# 主战役 128 张 → Output/
python Tools/loc_tools.py build -i Localization/ZH-CN/map_xml -l CHN -o Output

# C2M 用户战役 28 张（含子目录递归）
python -c "import sys; sys.path.insert(0,'Tools'); import loc_tools; from pathlib import Path; [loc_tools.build_map(f, Path('Output'), 'CHN') for f in sorted(Path('Localization/ZH-CN/map_xml_user').rglob('*.xml'))]"
```

### 游戏数据格式转换（可选）

```bash
# cif ↔ ini（Cultures 2 加密格式）
python Tools/cultures2_converter.py cif2ini foo.cif foo.ini
python Tools/cultures2_converter.py ini2cif foo.ini foo.cif

# c2m 解包 / 打包（用户战役）
python Tools/cultures2_converter.py c2m-unpack Campaign00/01_x.c2m unpacked/
python Tools/cultures2_converter.py c2m-pack unpacked/ repacked.c2m
```

## 不在仓库中的工具（已完成的旧脚本）

- 原 `GAME_CHN/archive/`（86 个散装 `trans_*.py` 翻译脚本）——历史留档，未入库。
- `scan_glossary_candidates.py` / `append_glossary_terms.py`——术语候选扫描与词典追加，
  已硬编码本机路径且词典已建成，仅在本地保留。
- 2 代历史年表工具（`translate_history2.py` 等）——依赖未入库的 `GAME_2_TEXT/GER` 源文件，一次性使用。

## 注意

- 本仓库为**成品汉化**，正常玩家只需按 README 安装 `Localization/ZH-CN/`，无需运行任何工具。
- 工具是给后续维护者/校对者用的质量保证手段。
- 汉化内容编辑遵循 GB2312 兼容规范（`--` / `・` / 哨塔 / 神明 / 威胁 等），新增译文勿引入
  `——`、`·`、瞭、祇、脅 等 GB2312 外字符，否则 `loc_tools.py build` 会编码失败。

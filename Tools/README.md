# tools/ —— 汉化工具链说明

本目录收录汉化流程中**仍在使用的工具**（旧的一次性脚本留在本地，未入库）。
所有工具为只读/校验类，**不会修改 `Localization/ZH-CN/` 下的译文**（`translate_cli.py` 除外，见下）。

> 目录命名：汉化内容位于 `Localization/ZH-CN/`（旧称 `GAME_CHN` / `LOC_CN`，为对位游戏安装目录曾用名）。

## 工具清单

### `translate_cli.py` — 统一汉化 CLI（主工具）

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
  python Tools/translate_cli.py verify campaign_01_01.xml   # 传文件名（相对 map_xml）
  python Tools/translate_cli.py repair [files...] [--apply]
  ```
- **注意**：`verify`/`repair` 参数传**文件名**（相对 `map_xml/`），不要传全路径。

### `loc_tools.py` — XML 真解析核心库（依赖库）

- **用途**：用 `xml.etree.ElementTree` 解析地图 XML，
  按结构读出 `strings[sid]` 与 `briefings[bid]` 的各语言文本（GER/ENG/POL/CHN）。
- **谁依赖它**：`audit_all_maps.py`、`audit_names.py`、`build_maps_from_versions.py` 都 `import` 它。
- **CLI 子命令**（`python Tools/loc_tools.py <cmd> --help`）：
  - `extract` / `extract-batch` 从游戏源数据提取为 XML
  - `build` 从 XML 构建游戏可加载的 ini/txt——构建 CHN 时**自动用 GBK 编码**
    （GB2312 无法编码「——」「瞭」等字形；游戏外挂实际读 GBK），
    briefings 的 **block id 自动 ASCII 化**（`10minutenspäter` → `10minutenspaeter`，
    官方汉化同策略），C2M 地图（IsC2M=true）输出到 `text/ger/`（C2M 包语言目录固定 ger）
  - `validate` 校验 XML 完整性
- **注意**：它是共享库，也是带 CLI 的工具。

### `audit_all_maps.py` — 全量三重审计（验收标准）

- **用途**：对 128 个主战役 + 28 个用户战役做：
  1. **合法性**：XML 可解析？
  2. **正确性**：CHN 槽数/段数 == GER？`@` 前缀是否平衡？
  3. **完整性**：CHN 空槽是否为零？
- **为什么用它**：CLI 的 `scan`/`verify` 用正则判断结构，对 `map_xml` 的
  `<text lang="CHN">` 结构存在误报；本工具走真解析，是唯一可靠的验收口径。
- **用法**：`python tools/audit_all_maps.py`（在仓库根目录运行）
- 会自动定位仓库根下的 `Localization/ZH-CN/`，不依赖本机绝对路径。

### `trans_scan.py` — 待译空槽扫描

- **用途**：列出某个 XML 文件中所有「GER 有原文、CHN 为空」的槽位，附德语原文预览，
  便于逐条翻译或核对遗漏。
- **用法**：
  - 单文件：`python tools/trans_scan.py <xml路径>`
  - 全部：在仓库根运行 `python tools/trans_scan.py`（默认扫 `Localization/ZH-CN/map_xml/*.xml`）

### `audit_names.py` — 人名/专名一致性自检（锚点法）

- **用途**：以 `language_union.csv` 中的专名中文写法为**规范形**，
  扫描全部 XML 中文文本，找出与规范形**等长、仅一字之差**的真实译名变体
  （如「芬里斯 / 芬里尔」这类不统一），并检查词典内部一词多译。
- **只读不改**：仅报告 (规范形, 异体) 对，不做任何修改。
- **用法**：在仓库根运行 `python tools/audit_names.py`
- 自动定位 `Localization/ZH-CN/` 与 `language_union.csv`，不依赖本机绝对路径。

### `build_maps_from_versions.py` — 按版本表构建地图本地化 XML

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

## 不在仓库中的工具（已完成的旧脚本）

- 原 `GAME_CHN/archive/`（86 个散装 `trans_*.py` 翻译脚本）——历史留档，未入库。
- `scan_glossary_candidates.py` / `append_glossary_terms.py`——术语候选扫描与词典追加，
  已硬编码本机路径且词典已建成，仅在本地保留。
- 2 代历史年表工具（`translate_history2.py` 等）——依赖未入库的 `GAME_2_TEXT/GER` 源文件，一次性使用。

## 注意

- 本仓库为**成品汉化**，正常玩家只需按 README 安装 `Localization/ZH-CN/`，无需运行任何工具。
- 工具是给后续维护者/校对者用的质量保证手段。

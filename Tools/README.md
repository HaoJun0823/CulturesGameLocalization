# Tools/ —— 汉化工具链说明（当前有效版）

> 本文件描述**当前仓库实际存在且在使用**的工具。全部仅依赖 Python 标准库；
> `loc_tools.py` 使用 `match` 语句需 **Python 3.10+**，其余兼容 3.8+。
> 已废弃工具见文末「废弃工具」节——**不要运行废弃工具**。

## 快速导航（按任务）

| 你要做什么 | 用哪个工具 | 示例 |
|---|---|---|
| XML 结构合法性检查（发布前必做） | `loc_tools.py validate` | `python Tools/loc_tools.py validate -i Localization/map_xml/` |
| 翻译质量审计（空翻/漏翻/错行） | `audit_translations.py` | `python Tools/audit_translations.py --out translation_audit.md --json audit.json` |
| 合并新语言（pol/cz/ru/eng…）进 XML | `integrate_lang_xml.py` | 见下方「多语言合并」 |
| 构建游戏可加载产物 | `build_text.py`（根目录） | `python build_text.py` |
| 部署到游戏目录 | `deploy_all.py` | `python Tools/deploy_all.py --dry-run` |
| 修正 XML 文件名变音 | `fix_xml_names.py` | `python Tools/fix_xml_names.py` |
| 术语表（20 语言母表） | 根目录 `language_union.csv` | 用 Excel/脚本编辑，勿当程序跑 |

> ⚠️ **每次开工前必读**：`../README-zh-cn.md`（项目总览与构建）、`../language_id-zh-cn.md`（20 语言 ID↔代码映射）、
> `../20-language-translation-guide.md`（多语言翻译总流程）。`.workbuddy/memory/MEMORY.md` 是项目长期记忆，
> `.workbuddy/skills/` 下 3 个工作流 skill 是标准执行流程——按 skill 正文执行，不要凭记忆另写一套逻辑。

## 工具清单

### `loc_tools.py` — XML 解析核心库 + CLI 工具（主依赖）

解析 `Localization/map_xml/*.xml`：按结构读出 `strings[sid]` 与 `briefings[bid]` 的各语言文本。
`audit_translations.py`、`integrate_lang_xml.py`、`build_text.py` 都依赖它。

CLI 子命令：

```bash
python Tools/loc_tools.py extract -i <地图目录> [--c2m]            # 单地图提取为 XML
python Tools/loc_tools.py extract-batch -i <源根1> -i <源根2> -o <输出> [--c2m]  # 批量提取
python Tools/loc_tools.py build -i Localization/map_xml -l CHN -o output [--map-data <游戏数据源>] [--force-utf8]
python Tools/loc_tools.py append -i Localization/map_xml/ --maps <含该语言的地图根>   # 按 MD5 追加语言
python Tools/loc_tools.py lang-add -i <xml> -l <代码3> [--alias X] [--encoding windows-1252] [--base] [--fix-1251]
python Tools/loc_tools.py lang-remove -i <xml> -l <代码3>
python Tools/loc_tools.py validate -i Localization/map_xml/        # 结构校验，输出 [OK]/[ERROR]
```

关键行为：
- `build` 构建 CHN 时用 **GB2312** 编码（游戏仅支持 GB2312）；`--force-utf8` 仅用于 UTF-8 能力目标（l10 汉化注入）。
- 中文输出目录统一为 `text/l10/`（项目规范「chn 输出为 l10」）。
- briefings 的 block id 自动 ASCII 化（`10minutenspäter` → `10minutenspaeter`）。
- `lang-add --base` 标记该语言为脚本源；构建时从 `--map-data` 按 MD5 找 `text/<base>/` 复制
  脚本文件（除 strings.ini/briefings/）到目标语言，文本型无条件 ASCII 化，二进制（pcx/fnt）原样拷贝。

### `integrate_lang_xml.py` — 多语言合并器（MD5 / id 双匹配 + id 一致性闸门）

把某语言的 `strings.ini/.cif` + `briefings` 合并进 XML。**这是接入新语言的标准入口**。

```bash
# 语言代码必须小写，如 pol/cz/ru/eng/fra/spa/por/hun...
python Tools/integrate_lang_xml.py --lang pol \
    --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps" --dry-run
python Tools/integrate_lang_xml.py --lang pol \
    --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps"
```

参数：`--lang`（必填）、`--source`（含各 map_dir 与 map.dat 的根）、`--xml-dir`（默认 `Localization/map_xml`）、
`--cif2ini`（cif2ini.py 路径，源只给 cif 时用）、`--dry-run`（只统计不写入）、
`--force-id-mismatch`（⚠️ 危险，跳过 id 闸门，仅确定源正确时用）。

安全机制（**不要绕过**）：
- 按 **map.dat MD5** 匹配；MD5 对不上回退「目录名 ↔ map_id/export_map_id」匹配。
- **非 MD5 命中强制 id 一致性闸门**：源 string id 须覆盖目标 ≥90%，否则判疑似错误地图并跳过告警。
- 写入前自动备份整个 map_xml 到 `map_xml.bak_<lang>_<时间戳>`（dry-run 不备份）。
- 源文件编码按「语言→代码页」显式解码（见下），**不要交给 detect_encoding**。

### `audit_translations.py` — 翻译质量审计（ger 基准，三类口径）

```bash
python Tools/audit_translations.py --out translation_audit.md --json audit.json
# 可选：--xml-dirs 指定目录（默认 map_xml + map_xml_user）、--base ger、--langs eng,chn
```

三类口径（**严禁自创维度当错误报**）：
- **空翻 empty**：语言节点存在但文本为空 → 明确缺陷。
- **漏翻 missing**：整文件缺语言 / 单 key 缺条目。
- **错行 line_mismatch**：行数不一致；⚠️ CHN 的错行几乎都是中文正常换行压缩，非截断，勿逐条改。

### `deploy_all.py` — 部署到游戏目录

```bash
python Tools/deploy_all.py --dry-run      # 预览（推荐先跑）
python Tools/deploy_all.py                 # 正式部署（自动备份将被覆盖的 text/）
python Tools/deploy_all.py --skip-backup   # 跳过备份
```

### `fix_xml_names.py` — 修正 XML 文件名与 map_id 中的变音字符

对齐游戏目录名（如源地图含 ä/ö/ü 时）。只改 `map_id` 属性与文件名，不动 `export_map_id`。

```bash
python Tools/fix_xml_names.py
```

## 多语言合并的编码规则（2026-08-18 实锤，反复踩坑）

- **cif 就是 ini 的序列化格式**：`G:/Projects/Cultures_Saga_CN/cif2ini.py`（或 `cif2ini_batch.py`）
  可完美解出 ini（按文件头 `\x41\x00`=C1 / `\xfd\x03`=C2 区分）。通常用户直接给 ini。
- **源抽取文件仍是原始代码页字节**：波兰/捷克等 `strings.ini/.cif` 是 cp1250 原始字节，
  俄/乌克兰是 cp1251。`detect_encoding` 顺序 utf-8→cp1252→…，而 **cp1250 在 cp1252 下也能"成功解码"（超集）**，
  会先返回 cp1252 造成乱码（`Zajmij siê budow¹` 应为 `Zajmij się budową`）。
- **正解**：`integrate_lang_xml.py:decode_source()` 按语言→代码页显式解码（pol/cz/sk…→cp1250，ru/uk…→cp1251），
  UTF-8 最优先（用户直接给的 UTF-8 ini 不受影响）。合并进 XML 的语言节点 `encoding="UTF-8"`。
- 复用：接 cz/ru 只需改 `--lang` 与 `--source`。

## 20 语言体系（未来翻译目标）

游戏原生支持 ID 0–19 共 20 种语言，映射见根目录 `language_id-zh-cn.md`：
`ger0 / eng1 / fra2 / ita3 / cze4 / rus5 / pol6 / spa7 / por8 / hun9 /
l10 简中10 / l11 繁中11 / l12 日12 / l13 韩13 / l14 印地14 / l15 阿拉伯15 /
l16 孟加拉16 / l17 印尼17 / l18 土耳其18 / l19 斯瓦希里19`

- 术语母表：根目录 `language_union.csv`（23 列 = 20 语言码 + META_TYPE/DESCRIPTION/REFERENCES；
  现有数据覆盖 ger/eng/l10，其余列待填）。
- 总流程见 `../20-language-translation-guide.md`；skill 见 `.workbuddy/skills/`。
- XML 内语言码注意大小写：`"CHN"` 大写（l10 的小写形式为 `chn`），其余小写三字母。

## 构建与发布（根目录脚本）

```bash
python build_text.py                  # 完整构建 → _build/（与游戏目录对齐）
python build_text.py --clean          # 先清 _build/
python build_text.py --dry-run        # 只预览
python convert_text_utf8.py           # 批量转 UTF-8
python publish_build.py               # 本地构建 + zip + GitHub Release（需 gh CLI）
```

> `build_text.py` 顶部需配置 `GAME_DIR`（游戏参考目录）。CI 首次需上传 game-data.tar.gz。

## 废弃工具（勿用）

- **`qa_translations.py`** —— 已废弃（早期版本把段落差异当 ERROR 报，噪声大）。
  翻译质量审计一律用 **`audit_translations.py`**。
- `archives/` 下的历史脚本 —— 归档留档，未维护。
- `Tools/Cultures-map-editor/`（子模块）的 cif 解码 —— 不再使用，统一走 `cif2ini.py`。

## 注意

- 本仓库为**成品汉化**；正常玩家按 README 安装即可，无需运行任何工具。
- 汉化内容遵循 GB2312 兼容规范（`--` / `・` / 哨塔 / 神明 / 威胁 等），新增译文勿引入
  `——`、`·`、瞭、祇、脅 等 GB2312 外字符。
- 编辑含 `\fonts`/`\palettes` 路径的脚本勿用 bash heredoc（`\p`/`\h` 会成非法转义）。

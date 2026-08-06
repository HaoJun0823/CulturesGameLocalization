# Cultures Saga 简体中文汉化

《Cultures: The Gates of Asgard》（文化：仙宫之门，第 2 代）的地图与文本**德语 → 简体中文**汉化包。

> 汉化内容以 `Localization/ZH-CN/` 目录组织，内含地图本地化 XML、游戏内字符串与超文本百科（北欧神话 / 历史年表 / 操作帮助）。
> 术语统一由 `language_union.csv` 术语表管理，全部译文经工具审计（0 空槽、结构合法、`@` 前缀与德文原版平衡）。

## 安装

1. **备份**游戏安装目录下的原 `map_xml/`、`text/` 文件夹。
2. 将本仓库 `Localization/ZH-CN/` 内**同名子目录**合并进游戏安装目录：
   - `map_xml/` → 游戏目录 `map_xml/`（128 个主战役地图，含 `_campaign_04_*` 系列）
   - `map_xml_user/` → 游戏目录 `map_xml_user/`（28 个 C2M 用户战役地图）
   - `text/` → 游戏目录 `text/`（l10 中文资源：游戏内字符串 + 超文本百科）
3. 启动游戏，语言设为德语（GER 为对齐锚点，CHN 由游戏外挂加载）。

> ⚠️ 请保留 `Localization/ZH-CN/` 目录结构原样拷贝；`map_xml/` 下的 `_campaign_04_*` 与 `campaign_04_*` 均为必要文件。

## 仓库结构

```
CulturesGameLocalization/
├── Localization/
│   └── ZH-CN/             # 汉化内容（安装时对位游戏目录）
│       ├── map_xml/       # 128 个主战役地图 XML
│       ├── map_xml_user/  # 28 个 C2M 用户战役地图 XML
│       └── text/l10/      # 游戏内字符串(ini) + 超文本百科(hlt/txt/pcx)
├── Tools/                 # 汉化工具链（说明见 Tools/README.md）
├── Output/                # 由构建工具生成的地图本地化 XML（132 张，见下）
├── translation_version_choose.csv  # 地图版本选择表（map_id → 游戏版本 2/3/5）
├── language_union.csv     # 术语表（664 词条，GER→CHN 权威来源）
├── 汉化工作指南.md         # 翻译方法与提交流程
└── 中文翻译指南.txt        # 游戏各版本文件结构说明
```

## 工具链

| 工具 | 用途 |
|------|------|
| `Tools/translate_cli.py` | 统一 CLI：`scan`（盘点）/`repair`（修复非法 XML）/`verify`（校验对齐）/`inject`（注入字典）/`commit` |
| `Tools/audit_all_maps.py` | 全量三重审计：合法性 / 正确性 / 完整性（128 + 28 全覆盖，验收标准） |
| `Tools/trans_scan.py` | 列出某文件全部待译空槽（CHN 空、GER 有原文），附德语预览 |
| `Tools/audit_names.py` | 人名/专名一致性自检（锚点法，找出仅一字之差的异体译名） |
| `Tools/loc_tools.py` | XML 真解析核心库（其余工具共享依赖） |
| `Tools/build_maps_from_versions.py` | 按版本表从游戏源数据构建地图本地化 XML（→ `Output/`） |
| `Tools/cultures2_converter.py` | Cultures 2 ini/cif 互转 + c2m 打包解包（提取自 Cultures-map-editor，GPL-3.0） |

## 汉化范围与质量

- **主战役**：`map_xml/` 128 个 XML，含 3 代战役（campaign_01/02/03）、第 4 代（`_campaign_04_*`）、多人地图、教程、Demo。
- **用户战役**：`map_xml_user/` 28 个 C2M 地图。
- **超文本百科**：北欧神话（13 页）、2 代历史年表（11 页 + 13 插图）、制作人员、操作帮助。
- **质量校验**：全部文件通过 XML 解析、GER/CHN 槽位与段数对齐、0 空槽、`@` 前缀与德文原版平衡。

## 构建地图本地化 XML（可选）

`Output/` 中的 156 个地图目录是**可直接放进游戏的地图本地化文件**（由 `LOC_CN` 的汉化 XML 构建）：

- 主战役（128 个）：`Output/<map_id>/text/l10/strings.ini` + `briefings/briefings.txt`，GB2312 编码
- C2M 用户战役（28 个）：同样输出 `Output/<map_id>/text/l10/...`（中文统一用 l10 目录，与主战役一致）

构建命令（使用 `Tools/loc_tools.py build`，已内置 GB2312 编码与 block id ASCII 化）：

```bash
# 主战役（128）
python Tools/loc_tools.py build -i Localization/ZH-CN/map_xml -l CHN -o Output
# C2M 用户战役（28，含子目录递归）
python -c "import sys; sys.path.insert(0,'Tools'); import loc_tools; from pathlib import Path; [loc_tools.build_map(f, Path('Output'), 'CHN') for f in sorted(Path('Localization/ZH-CN/map_xml_user').rglob('*.xml'))]"
```

> 说明：中文统一用 **GB2312** 编码（游戏仅支持 GB2312，不支持 GBK 扩展）。
> 汉化源文本已保证 GB2312 兼容：超集字形在源 XML 中直接改掉——破折号用 `--`、
> 人名间隔号用 `・`、瞭望塔/瞭望手改「哨塔/哨兵」、神祇改「神明」、脅改「威胁」；
> 中文输出目录统一为 **`text/l10/`**（项目规范「chn输出为l10」——l10 是外挂汉化注入的目标语言目录，
> 主战役与 C2M 一致；源数据里只有 ger 是官方原始包，不影响 l10 加载）；
> briefings 的 block id 按官方汉化策略做 ASCII 化（`10minutenspäter` → `10minutenspaeter`）。
> 历史版本：`Output/` 曾由 `Tools/build_maps_from_versions.py` 生成 132 张源数据 XML 模板
> （见 `translation_version_choose.csv` 版本选择表），已由可直接加载的 l10 文件取代。

## 免责声明

本仓库为民间汉化成果，仅供学习与交流。游戏版权归原开发者/发行商所有。

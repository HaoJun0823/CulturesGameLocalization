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

## 汉化范围与质量

- **主战役**：`map_xml/` 128 个 XML，含 3 代战役（campaign_01/02/03）、第 4 代（`_campaign_04_*`）、多人地图、教程、Demo。
- **用户战役**：`map_xml_user/` 28 个 C2M 地图。
- **超文本百科**：北欧神话（13 页）、2 代历史年表（11 页 + 13 插图）、制作人员、操作帮助。
- **质量校验**：全部文件通过 XML 解析、GER/CHN 槽位与段数对齐、0 空槽、`@` 前缀与德文原版平衡。

## 构建地图本地化 XML（可选）

`Output/` 中的 132 张地图 XML 由 `Tools/build_maps_from_versions.py` 按版本选择表
从游戏原始数据生成（85 张取 GAME_5、46 张取 GAME_2、1 张取 GAME_3），
可用作对照或重新生成模板：

```bash
python Tools/build_maps_from_versions.py \
    --csv translation_version_choose.csv \
    --src "<含 GAME_2/3/5_MAP 的源数据根目录>" \
    --output Output
```

> 游戏原始数据（GAME_2/3/5_MAP 等）**不随本仓库分发**，`--src` 需指向本机源数据。

## 免责声明

本仓库为民间汉化成果，仅供学习与交流。游戏版权归原开发者/发行商所有。

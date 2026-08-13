# Cultures Saga 简体中文汉化

《Cultures: The Gates of Asgard》（文化：仙宫之门，第 2 代）的地图与文本**德语 → 简体中文**汉化包。

> 汉化内容以 `Localization/map_xml/`、`Localization/map_xml_user/`、`Localization/text/l10/` 组织，内含地图本地化 XML、游戏内字符串与超文本百科（北欧神话 / 历史年表 / 操作帮助）。
> 全部译文经工具审计（0 空槽、结构合法、`@` 前缀与德文原版平衡）。

## 关联项目 / Related Projects

- **CulturesGameExtend** —— 真正在游戏内加载本仓库简体中文（`l10`）文本与地图内容的社区扩展 DLL（基于 UTF-8 文本引擎）。两个仓库相互独立；请在该仓库中构建并部署 DLL，将 `CulturesGameExtend.dll`（及 `plugins/`）放入游戏目录（或在运行 `build_text.py` 时设置 `CULTURES_EXTEND_DIR` 指向其根目录）。
  <https://github.com/HaoJun0823/CulturesGameExtend>

## 安装

1. **备份**游戏安装目录下的原 `Data/maps/`、`Data/text/` 文件夹。
2. 在游戏目录运行构建脚本 `build_text.py`（详见下方「构建与部署」），或直接下载 [Releases](https://github.com/HaoJun0823/CulturesGameLocalization/releases) 中的 zip 覆盖游戏目录。
3. 启动游戏，语言设为德语（GER 为对齐锚点，CHN 由游戏外挂加载）。

> ⚠️ 请保留 `Localization/map_xml/` 目录结构原样拷贝；`_campaign_04_*` 与 `campaign_04_*` 均为必要文件。

## 仓库结构

```
CulturesGameLocalization/
├── Localization/            # 本地化源文件
│   ├── map_xml/             # 128 个主战役地图 XML（CHN/ger/eng/pol 多语言）
│   ├── map_xml_user/        # 28 个 C2M 用户战役地图 XML
│   └── text/                # 游戏系统文本（ger 原文 + l10 中文）
├── Tools/                   # 汉化工具链
│   ├── loc_tools.py         # XML 解析核心库 + 构建工具（主依赖）
│   ├── deploy_all.py        # 部署到游戏目录的脚本
│   └── fix_xml_names.py     # 修正 XML 文件名中的变音字符
├── archives/                # 归档的历史工具与审计报告
├── build_text.py            # 主构建脚本（多语言 → _build/）
├── convert_text_utf8.py     # 批量转换文本为 UTF-8
├── publish_build.py         # 本地构建 + 打包 zip + 发布 GitHub Release
├── Game_FileSystem_Intro.md # 游戏文件系统结构说明
└── .github/workflows/       # GitHub Actions 自动构建发布
```

## 支持的语言

| 代码 | 语言 | 说明 |
|------|------|------|
| `ger` | 德语 | 官方源语言，始终保留 |
| `eng` | 英语 | 从 GAME_2/3/4 提取合并 |
| `pol` | 波兰语 | 从 GAME_2 提取合并 |
| `l10` | 简体中文 | 汉化注入目标语言（外挂加载）|

## 构建与部署

### 完整构建（本地，推荐）

```bash
# 一键构建：解析 XML → 生成全部语言 → 打包
python build_text.py          # 完整构建
python build_text.py --clean  # 先清空 _build/ 再构建
python build_text.py --dry-run # 只预览

# 构建后自动生成 _build/map_languages.csv（每张地图的语言清单）
```

构建输出 `_build/` 目录结构与游戏目录完全对齐，可直接复制覆盖：
- `_build/Data/maps/<map_id>/` → `游戏目录/Data/maps/<map_id>/`
- `_build/DataX/UserCampaigns/` → `游戏目录/DataX/UserCampaigns/`
- `_build/Data/Text/` → `游戏目录/Data/Text/`

> **注意**：需要在脚本顶部配置 `GAME_DIR`（游戏参考目录，含 `Data/maps` 等原始素材）。

### UTF-8 转换

```bash
python convert_text_utf8.py          # 转换 Localization/text/ 下所有 ini/txt 为 UTF-8
python convert_text_utf8.py --dry-run # 只预览
python convert_text_utf8.py --all    # 包含 _backup 目录
```

## 发布到 GitHub Release

### 方式 A：本地发布（完整构建）

```bash
python publish_build.py                  # build → zip → 发布 Release
python publish_build.py --no-build       # 仅使用已有 _build/ 打包发布
python publish_build.py --tag v1.0       # 自定义版本号
python publish_build.py --dry-run        # 只打包，不发布
```

需要先安装并登录 [gh CLI](https://cli.github.com/)：
```bash
winget install GitHub.cli
gh auth login
```

### 方式 B：GitHub Actions（CI）

仓库 Actions 页 → **Build & Release** → **Run workflow**（可填 release_tag / game_data_url）。

> ⚠️ 游戏地图数据（SAGA_GAME_HACK/Data/maps/）不在仓库中。CI 首次构建需先上传一次
> `gh release upload <tag> game-data.tar.gz --clobber`，或通过 `game_data_url` 输入提供下载链接。
> 无数据时地图构建会跳过，仅发布 Data/Text 等附加资源。

## 常见问题

- **发布 zip 里没有地图？** CI 构建缺少 `GAME_DIR` 源数据，改用本地 `publish_build.py`。
- **中文乱码？** 确认游戏以德语（GER）启动，CHN 由外挂注注入；文本构建为 UTF-8。
- **编码问题**：游戏仅支持 GB2312，`loc_tools.py build` 已内置 GB2312 兼容规范（`--`、`・`、哨塔/哨兵、神明、威胁）。

## 免责声明

本仓库为民间汉化成果，仅供学习与交流，请勿用于商业用途。游戏版权归原开发者/发行商所有。
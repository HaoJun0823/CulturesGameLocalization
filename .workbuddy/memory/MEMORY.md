# 项目长期记忆 — Cultures Saga 公开汉化仓库（工具链 + 构建）

> 公开仓库（GitHub: HaoJun0823/CulturesGameLocalization）。德语→简体中文汉化包。与 CulturesGameExtend（DLL）配合：本仓库出文本/地图，DLL 在游戏内加载 l10。
> **本文件与 `.workbuddy/skills/` 已随仓库提交**（防 AI 失忆/换机丢失）。开工前必读：本文件 +
> `README-zh-cn.md` + `language_id-zh-cn.md` + `20-language-translation-guide.md`。

## AI 执行铁律（防失忆，勿跳过）
1. 工作流按 `.workbuddy/skills/` 下 3 个 SKILL.md 正文执行，**不凭记忆另写一套逻辑**。
2. 每个有写操作的步骤先 `--dry-run` / 只读确认。
3. 干完活**必须写当日日志** `.workbuddy/memory/YYYY-MM-DD.md`（append-only）并 `git add`/`git commit`，
   绝不留 300+ 文件的工作树脏状态过夜。
4. 不认得的工具/路径先查 `Tools/README.md` 与本文档，找不到再问用户。

## 仓库结构
- `Localization/`：`map_xml/`(128 主战役 XML, 多语言 chn/ger/eng/pol)、`map_xml_user/`(28 C2M 用户战役)、`text/`(系统文本 ger+l10)
- `Tools/`：`loc_tools.py`(XML 解析核心+构建主依赖)、`deploy_all.py`、`fix_xml_names.py`、`integrate_lang_xml.py`(通用多语言合并器)、`audit_translations.py`(**ger 基准翻译质量审计：空翻/漏翻/错行，校准版**；旧 `qa_translations.py` 已废弃，勿用)
- 根目录文档：`README-zh-cn.md`(总览+构建)、`language_id-zh-cn.md`(20 语言 ID↔代码权威映射)、
  `20-language-translation-guide.md`(**多语言翻译总流程**)、`language_union.csv`(术语母表，23 列=20 语言码+META_*)、
  `Tools/README.md`(工具用法，已按当前工具重写)、`Game_FileSystem_Intro.md`(游戏文件系统)
- **cif 就是 ini 的序列化格式**：标准解压用 `G:/Projects/Cultures_Saga_CN/cif2ini.py` / `cif2ini_batch.py`（按文件头 `\x41\x00`=C1 / `\xfd\x03`=C2 区分），通常用户直接给 ini。子模块 `Tools/Cultures-map-editor` 的 cif 解码已不再使用。
- 构建：`build_text.py`(→_build/)、`convert_text_utf8.py`、`publish_build.py`(→GitHub Release)
- 游戏数据(map)不在仓库，来自 `SAGA_GAME_HACK/Data/maps/`；CI 首次需上传 game-data.tar.gz

## 20 语言体系（未来翻译目标，权威=language_id-zh-cn.md）
- ID 0–19：`ger0 eng1 fra2 ita3 cze4 rus5 pol6 spa7 por8 hun9 l10简中10 l11繁中11 l12日12 l13韩13
  l14印地14 l15阿拉伯15 l16孟加拉16 l17印尼17 l18土耳其18 l19斯瓦希里19`。
- XML 语言码大小写：`CHN`(l10)大写，其余小写三字母；比对字典键一律小写归一化。
- 代码页：中东欧源(pol/cz/sk/hu…)→cp1250；俄/乌(rus/uk…)→cp1251；UTF-8 最优先。勿用 detect_encoding 猜。
- 术语母表 `language_union.csv` 现状(2026-08-18)：有数据=ger/eng/l10(eng 已全面去德语词)；空列待填=fra/ita/cze/rus/pol/spa/por/hun/l11–l19。
- 接入新语言端到端步骤见 `20-language-translation-guide.md`。

## 各代主战役官方译名对照（已知语言，供多语言菜单/文本对齐）
- **仙宫之门**（Cultures II / Asgard's Gate）：ger **Die Tore Asgards**；pol **Bramy Asgardu**
- **北国风云**（Cultures III / Nordland）：ger **Reise nach Nordland**（菜单简称 Nordland）；pol **Wyprawa na Północ**
- **第八世界奇迹**（Cultures IV/VI / Das achte Weltwunder）：ger **Das achte Weltwunder**；pol **8 Cud Świata**
- **萨迦**（Cultures V / Saga）：ger **Saga**；pol **无官方译名，自行翻译**（Saga 为波兰语固有词，可保留 Saga）
- 用途：接 pol（及后续 cz/ru 等）到 `saga*.ini`、战役 XML 的菜单名/描述时，须用对应官方译名，勿音译或字面直译。

## 构建/部署
- `python build_text.py` → `_build/` 与游戏目录对齐，可直接覆盖
- 游戏以 GER 启动，CHN 由外挂 DLL 注入；文本 UTF-8 构建，游戏仅 GB2312（loc_tools 内置兼容）

## loc_tools 关键配置（v1.4+）
- `base="true"`（语言级）：该语言是脚本(hlt/fnt/pcx/ini)标准来源，build 时从 --map-data 源按 MD5 找 text/<base>/ 复制（除 strings.ini/briefings/）
- `deprecated="true"`（根级，紧跟 IsC2M 之后）：整张地图多语言弃用，build 整张跳过
- base 复制：文本型(hlt/ini/txt…)无条件 ASCII 化(fix_1251_chars)；二进制(pcx/fnt)原样拷贝

## POL/cz/ru 等多语言整合流程（reusable）
- 数据源（波兰语各代，目录前缀=游戏内部战役编号，≠用户口中的"几代"）：
  - `Cultures_Saga_Remix/Bramy Asgardu/.../maps`（1代 pol，已并入 campaign_01_*）
  - `Cultures_Saga_CN/C3_POL/Wyprawa na Północ/.../maps`（源目录 campaign_02_*）→ 2026-08-18 并入仓库 campaign_02_*
  - `Cultures_Saga_CN/C4_POL/8 Cud Świata/.../maps`（源目录 campaign_03_*）→ 2026-08-18 并入仓库 campaign_03_*
- 按 **map.dat MD5** 匹配 XML（多数命中）；MD5 对不上回退"目录名 ↔ map_id" + id 一致性闸门（≥90%）。
- **源文件编码陷阱（重要，2026-08-18 实锤，推翻了"编码不再是问题"的旧结论）**：
  尽管"输出侧 UTF-8 已落地"，但**源抽取文件（ini/cif）本身仍是 cp1250/cp1251 原始字节**。
  `loc_tools.detect_encoding` 顺序是 utf-8→cp1252→…，而 **cp1250 字节在 cp1252 下也能"成功解码"（超集）**，
  于是先返回 cp1252，造成乱码（`Zajmij siê budow¹` 应为 `Zajmij się budową`）。
  **正解**：`integrate_lang_xml.py:decode_source()` 按"语言→代码页"显式优先解码（pol/cz/sk…→cp1250，ru/uk…→cp1251），
  UTF-8 仍最优先（用户直接给的 UTF-8 ini 不受影响）。**切勿再"统一交给 detect_encoding"。**
- 工具：`Tools/integrate_lang_xml.py`（通用版，2026-08-18 由已删的 `integrate_pol_xml.py` 重建）；
  ini 优先，仅源只给 cif 时才调 cif2ini。复用：改 `--lang` 与 `--source` 即可接 cz/ru。
- **MD5 可能对不上**（不同游戏版本）→ 脚本回退"目录名 ↔ XML 的 map_id/export_map_id"匹配，
  且**非 MD5 命中时强制 id 一致性闸门**：源 string id 须覆盖目标 ≥90%，否则判疑似错误地图并跳过，绝不盲合。

## 已知坑
- **合并前必查 id 一致性**：MD5 不符时绝不可直接合并，先用 id 重叠率确认是同一张地图（见 integrate_lang_xml.py 闸门）
- 写含 `\fonts`/`\palettes` 路径的 .py 勿用 bash heredoc/`-c`（\p/\h 成非法转义）
- 文件名 `_campaign_04_*` 与 `campaign_04_*`（下划线前缀）均为必要文件，游戏读后者
- **XML「错误/合法性」检查唯一用 `Tools/loc_tools.py validate`**：只查结构（必填字段+可解析），输出 `[OK]`/`[ERROR]`。
- **翻译质量审计用 `Tools/audit_translations.py`**（ger 基准，比对 eng/chn），三类口径：空翻(空值)=明确缺陷；漏翻(整文件缺语言/单key缺)=缺陷；错行(行数不一致)=**CHN 上几乎都是中文正常换行压缩、非截断，勿逐条改**（行数启发式对中文是伪信号）。不要自创段落/占位符维度当错误报。
- **语言码大小写坑（反复栽过）**：XML 里语言是 `"CHN"`（大写），自写脚本比对字典键必须小写归一化，否则会把全部 CHN 误判缺失（曾因此假报 5066）。`audit_translations.py` 已内部归一化。
- 工作流 skill 在 `.workbuddy/skills/`，但本平台 Skill 工具未注册它们，按 skill 文件正文执行即可，不要凭记忆另写一套检查逻辑。

## 翻译质量现状（2026-08-18 审计 + 同日复核校准，156 XML = map_xml 128 + map_xml_user 28）
- **GER：已验证 DONE**。`Tools/ger_source_audit.py` 比对 GAME_2/3/4/5_MAP(+USER) 源：156/156 匹配正确源，152 完全一致，3 处仅 CRLF↔LF 行尾差异，1 处 campaign_01_09-sub 多余空 `header` 模板块，**0 幽灵块**（XML 空块在源里同样是空块）。commit `41c426d`。
- **空翻（节点空）**：eng 13 + chn 29 = **42 处，全部经工具复核为「幽灵块」**（ger 源该块同样为空或无内容），**不是真缺陷、绝不可编造填充**。commit `6d3a9d1` 已修 8 处真缺陷后剩余。
- **漏翻(key 级)**：0（只要文件声明该语言，ger 每个 key 都有对应条目）。
- **eng / pol 整文件缺失（二者完全重合，2026-08-18 核实）**：eng 与 pol **覆盖完全对齐**——各 114/156 有内容，且「有/无」在每个文件上一致。**同缺的 42 个文件完全相同**（0 个只缺其一）：14 个 `_campaign_04_*`(C2M) + 28 个 `map_xml_user` 用户地图；原版游戏这些地图即无 eng/pol，主战役(campaign_01–03/tutorial/demo…)二者都在。是否补译由用户定（中文本地化受众无需英文，建议不补）。**注意**：pol 实际覆盖 114 文件（85 非02/03主战役 + 12 campaign_02 + 17 campaign_03），不只是 02/03——原版游戏数据本就含 pol；eng/pol 在任何文件上都不存在"一个有一个无"的错位。
- **错行（行数不一致）**：chn 157 + eng 6，**全部经字符数复核为良性**——德文比中文约 3× 冗长，完整中译字符数本就只有德文 30–40%，行数差≠截断；eng 的 6 处 abs(差)<3 更无截断。无需逐条改。
- **已修的真实缺陷**（commit `6d3a9d1`）：eng 3 空翻(campaign_01_05 b:sub、campaign_01_07 b:spieler_attakiert_Byzanz、b:spieler_zahlt_tribut)+1 截断(b:wikiflucht)、chn 4 浓缩摘要(tutorial_007 b:00、multiplayer_007 begin_00、tutorial_001 b:00、multiplayer_02_06 begin_00)。
- 报告产物：`translation_audit.md` + `audit.json`（空翻/漏翻/错行口径）；`ger_audit_report.md` + `Tools/ger_source_audit.py`（GER 源一致性）。
- **eng/ger/chn 质量结论**：三项语言质量均已达「无可修真缺陷」状态；剩余项均为政策决策（42 文件补英文与否）或纯格式差异（CRLF/LF、模板空块）。下一步可转向其他语言（pol 已合并，可接 cz/ru/fra/ita…）。

## 关联
- 运行期 DLL：`G:\Projects\CulturesGameExtend`
- 游戏数据/逆向：`G:\Projects\Cultures_Saga_CN\SAGA_GAME_HACK`
- 波兰数据源：`G:\Projects\Cultures_Saga_Remix\Bramy Asgardu`
- 早期父仓库（术语溯源）：`G:\Projects\Cultures_Saga_CN`

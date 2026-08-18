# 20 语言翻译总流程指南（CulturesGameLocalization）

> 本文档是**未来把游戏翻译到全部 20 种语言**时的总执行规范，也是防失忆的「开工必读」。
> 配套文件：`language_id-zh-cn.md`（语言 ID↔代码映射）、`language_union.csv`（术语母表）、
> `Tools/README.md`（工具用法）、`.workbuddy/skills/`（3 个工作流 skill）、`.workbuddy/memory/MEMORY.md`（项目记忆）。
>
> **执行铁律**：① 按 skill 正文执行，不凭记忆另写逻辑；② 每个步骤先 `--dry-run` 或只读确认；
> ③ 完成后写当日日志到 `.workbuddy/memory/YYYY-MM-DD.md`；④ 干完活必须 `git add`/`git commit`，不留工作树脏状态。

## 1. 语言体系（ID 0–19）

游戏原生支持 20 种语言。ID、代码、语言对照（权威来源：`language_id-zh-cn.md`）：

| ID | 代码 | 语言 | 备注 |
|----|------|------|------|
| 0 | `ger` | 德语 | 源语言，始终保留 |
| 1 | `eng` | 英语 | 已有（部分文件缺） |
| 2 | `fra` | 法语 | |
| 3 | `ita` | 意大利语 | |
| 4 | `cze` | 捷克语 | 代码页 cp1250 |
| 5 | `rus` | 俄语 | 代码页 cp1251 |
| 6 | `pol` | 波兰语 | 已有，代码页 cp1250 |
| 7 | `spa` | 西班牙语 | |
| 8 | `por` | 葡萄牙语 | |
| 9 | `hun` | 匈牙利语 | |
| 10 | `l10` | 简体中文 | 汉化注入目标（XML 内语言码为 `CHN`） |
| 11 | `l11` | 繁体中文 | |
| 12 | `l12` | 日语 | |
| 13 | `l13` | 韩语 | |
| 14 | `l14` | 印地语 | |
| 15 | `l15` | 阿拉伯语 | |
| 16 | `l16` | 孟加拉语 | |
| 17 | `l17` | 印度尼西亚语 | |
| 18 | `l18` | 土耳其语 | |
| 19 | `l19` | 斯瓦希里语 | |

- **代码页规则**：中东欧语言（pol/cz/sk/hu…）源字节用 **cp1250**；俄/乌克兰（rus/uk…）用 **cp1251**；
  用户直接给的 UTF-8 文件最优先。**绝不交给 `detect_encoding` 猜**（cp1250 会被 cp1252 超集误吞）。
- XML 内语言码大小写：`CHN` 大写；其余小写三字母（`ger`/`eng`/`pol`…）。

## 2. 内容载体

| 载体 | 位置 | 说明 |
|---|---|---|
| 地图本地化 XML | `Localization/map_xml/`（128 主战役）+ `Localization/map_xml_user/`（28 C2M） | 每文件 `<strings>` + `<briefings>`，语言节点 `<text lang="X">` / `<lang code="X">` |
| 系统文本 | `Localization/text/<lang>/` | `strings/*.ini`（或源 cif）+ `hypertext/**`（history/mythology/credits/ingamehelp） |
| 术语母表 | 根目录 `language_union.csv` | 23 列 = 20 语言码 + META_TYPE/DESCRIPTION/REFERENCES |
| 语言映射文档 | 根目录 `language_id-zh-cn.md` | ID↔代码↔语言唯一权威 |

## 3. 接入新语言的完整流程（以 cz 为例）

### 3.1 准备源数据
拿到该语言版本的游戏地图目录（根下含各 `map_dir/{map.dat, text/<lang>/}`）。
若源是 `.cif`：用 `G:/Projects/Cultures_Saga_CN/cif2ini.py`（或 `cif2ini_batch.py`）解成 ini。
（cif 只是 ini 的序列化格式，头 `\x41\x00`=C1 / `\xfd\x03`=C2。）

### 3.2 合并进地图 XML —— skill「merge-lang-to-mapxml」
```bash
python Tools/integrate_lang_xml.py --lang cz \
    --source "G:/.../源地图根目录" --dry-run        # 先看匹配数与 id 重叠率
python Tools/integrate_lang_xml.py --lang cz \
    --source "G:/.../源地图根目录"                   # 确认后正式写入（自动备份 map_xml）
```
- MD5 匹配优先；MD5 对不上回退目录名↔map_id，且强制 id 一致性闸门（覆盖 ≥90%），绝不盲合。
- 若 XML 尚无该语言声明：`python Tools/loc_tools.py lang-add -i <xml目录> -l cz --encoding windows-1252`（或按需 UTF-8）。

### 3.3 系统文本 —— skill「merge-translate-text-history」
ger 是源；目标语言目录结构与 ger 对齐。`strings` 从源 ini/cif 提取翻译，`hypertext` 页面与 ger 一一对应。
**CJK 类语言（l11 繁中/l12 日/l13 韩）**：注意字体/调色板资源（`fonts/`、`palettes/`）需从 base 复制，
半角→全角标点、段落数严格对齐（见 skill 正文）。

### 3.4 术语表同步
翻译术语时同步维护 `language_union.csv`：新语言列（如 `cz`）填入该语言的术语译文。
列名即语言码；l10–l19 列头已带括号语言标注。用 Excel 打开（UTF-8 BOM）或脚本编辑。

### 3.5 质量校验 —— skill「validate-xml-translations」
```bash
python Tools/loc_tools.py validate -i Localization/map_xml/          # 结构：必填字段+可解析
python Tools/audit_translations.py --base ger --langs cz --out translation_audit.md --json audit.json
```
- 空翻 = 明确缺陷必填；漏翻 = 整文件缺语言/单 key 缺；错行 = 仅参考（中文换行压缩是伪信号）。
- **跨语言对译审计**：`audit_translations.py --base cz --langs chn` 可做 cz→chn 复核。

### 3.6 构建与部署
```bash
python build_text.py                  # → _build/（与游戏目录对齐）
python Tools/loc_tools.py build -i Localization/map_xml -l cz -o output [--map-data 游戏数据源]
python Tools/deploy_all.py --dry-run  # 部署预览
```
游戏内加载新语言：游戏以 GER 启动；非 l10 的语言若游戏原生支持（fra/spa…）直接切换语言即可，
l10 需外挂 DLL（CulturesGameExtend）。

### 3.7 收尾（防失忆铁律）
```bash
# 1) 记日志
#    .workbuddy/memory/YYYY-MM-DD.md 追加：语言、源目录、匹配统计、校验结果、提交 hash
# 2) 提交（精确 add，不用 -A）
git add Localization/map_xml/ language_union.csv Tools/ && git commit -m "feat: 接入 <语言> 本地化"
```

## 4. 术语表语言列现状（2026-08-18）

`language_union.csv`（23 列 × 871 行）：
- 有数据：`ger`（0）、`eng`（1）、`l10`（10 简中）。eng 列已全面清洗（德语词已译英）。
- 空列待填：`fra/ita/cze/rus/pol/spa/por/hun/l11–l19`（其中 `pol` 原版即 100% 空）。
- META_TYPE/DESCRIPTION/REFERENCES 为术语分类/释义/出处，翻译时保留不译。

## 5. 质量与一致性红线

1. **绝不盲合**：MD5 对不上时先 id 重叠率确认同一张图（≥90%），否则跳过并告警。
2. **源编码按语言代码页解**：cp1250/cp1251，UTF-8 优先；勿用 detect_encoding 猜。
3. **XML 语言码大小写**：CHN 大写；比对字典键一律小写归一化。
4. **结构检查唯一用 `loc_tools validate`**；翻译质量用 `audit_translations.py` 三类口径，不自创维度。
5. **GB2312 兼容**（仅影响 CHN 构建）：勿引入 `——`、`·`、瞭、祇、脅 等字符。
6. **所有语言共享同一 ger 锚点**：段数、key 集以 ger 为准。

## 6. 常用资源路径

| 资源 | 路径 |
|---|---|
| cif 解码 | `G:/Projects/Cultures_Saga_CN/cif2ini.py` / `cif2ini_batch.py` |
| 波兰语源（1代） | `G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/.../maps` |
| 波兰语源（2代/3代） | `G:/Projects/Cultures_Saga_CN/C3_POL/...`、`C4_POL/...` |
| 游戏数据/逆向 | `G:/Projects/Cultures_Saga_CN/SAGA_GAME_HACK` |
| 运行期 DLL | `G:\Projects\CulturesGameExtend` |

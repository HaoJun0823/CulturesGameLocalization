---
name: validate-xml-translations
description: 校验 Localization/map_xml(+map_xml_user) 的 XML。结构"错误检查"用 loc_tools validate；翻译质量复核(ger 基准的空翻/漏翻/错行)用 audit_translations.py，且必须按本流程定义的三类口径上报，不得自创维度。当要发布前检查 XML 是否合法、或用户要求"检查翻译/空翻/漏翻/错行"时使用。
---

# 工作流 3：XML 校验与翻译质量复核

## 1) 结构"错误检查"（用户口中的"检查错误"）
用仓库自带工具，不要自创：
```bash
python Tools/loc_tools.py validate -i Localization/map_xml/
```
校验必填字段（version / map_id / languages / strings / briefings）齐全、能解析，输出 `[OK]`/`[ERROR]`。
这是"错误检查"的主答案——之前 128 个 XML 全部 `[OK]`、0 错误。

## 2) 翻译质量复核（ger 基准，三类口径，已对真实数据校准）
```bash
python Tools/audit_translations.py --out translation_audit.md --json audit.json
# 默认扫 map_xml + map_xml_user，基准 ger，比对 eng/chn
```
脚本输出三类，严禁自创其他维度：

- **空翻 (empty)**：语言节点存在但文本为空/纯空白。→ **明确缺陷，直接定位去填**。
  - 当前实测：eng 16 处 + chn 29 处 = 45 处（全在 briefings）。
- **漏翻 (missing)**：
  - 整文件未声明该语言（`files_missing_lang`）：当前 eng 有 42 个文件未声明（多为 `_campaign_04_*` 与各 `XX_*.xml` 剧情/战役文件），是否补译由用户决定；
  - 单 key 漏翻（文件声明了语言但该 key 无条目）：当前实测 **0**——只要声明了语言，ger 的每个 key 都有对应条目。
- **错行 (line_mismatch)**：ger 与译文的非空行数不一致。
  - ⚠️ **经抽样核实，CHN 的错行几乎都是中文正常换行压缩（译文内容完整），并非截断，无需逐条修改**。行数启发式对中文是伪信号；如需严格校验需改用语义/字符数比对。
  - eng 的错行很少（6 处），可人工肉眼过一遍；其中 `campaign_01_07.xml b:wikiflucht` (ger=11/eng=2) 疑似真截断，优先看。

## 3) 关键坑（之前反复栽过）
- **语言码大小写**：XML 里是 `"CHN"`（大写），比对字典键必须用小写归一化，否则会把全部 CHN 误判成"缺失"（曾因此报出 5066 假阳性）。`audit_translations.py` 已内部归一化，勿在自写脚本里漏掉。
- **行是 `\n` 还是独立节点**：briefings 的每语言是一组 `{type,value}` 节点列表（一个节点整体含 `\n`），strings 的每语言是纯文本；提文本都要走 `text_of()` 统一处理。
- **不要自创段落/占位符规则当错误维度**——用户不认，且之前从未有过；只报上面三类。
- 合并其他语言后必须重跑 `loc_tools validate` 确认结构没被破坏。
- **术语抽查**：可用根目录 `language_union.csv`（术语母表，20 语言列）对照译文术语一致性（人工/脚本均可，勿把差异当硬错误）。
- **相关文档**：语言映射 `language_id-zh-cn.md`、翻译总流程 `20-language-translation-guide.md`。

## 执行顺序
1. 结构错误 → `loc_tools validate`（主答案）。
2. 翻译质量 → `audit_translations.py`，按上面三类口径读 `translation_audit.md`，重点修 45 处空翻。

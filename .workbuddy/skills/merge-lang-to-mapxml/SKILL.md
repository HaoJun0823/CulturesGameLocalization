---
name: merge-lang-to-mapxml
description: 将其他语言版本（eng/pol/ru/cz 等）合并进 Localization/map_xml/*.xml 的标准流程。当要把某个新语言集成到地图 XML、或补充已有 XML 缺失的语言列时使用。
---

# 工作流 1：合并其他语言版本到地图 XML

目标：把 eng / pol / ru / cz 等"其他语言"的本地化内容，匹配进
`Localization/map_xml/*.xml` 的对应 `<string>` / `<block>` 节点。

## 前置认知
- XML 结构：`<localization map_id="..." export_map_id="..." map_md5="..."><languages/><strings/><briefings/></localization>`，
  每语言在 `<string>` 下是 `<text lang="X">`，在 `<briefings>` 下是 `<lang code="X">`。
- **语言代码全集（游戏原生 0–19，权威映射见仓库根 `language_id-zh-cn.md`）**：
  `ger/eng/fra/ita/cze/rus/pol/spa/por/hun/l10(简中)/l11(繁中)/l12(日)/l13(韩)/l14(印地)/l15(阿拉伯)/l16(孟加拉)/l17(印尼)/l18(土耳其)/l19(斯瓦希里)`。
  XML 内语言码注意大小写：`CHN`（l10 的）大写，其余小写三字母。
- **总流程见仓库根 `20-language-translation-guide.md`**（接入任意新语言的端到端步骤）。
- **术语母表**：仓库根 `language_union.csv`（23 列 = 20 语言码 + META_*），翻译时同步填对应语言列。
- **XML 根的两个"id"是合并的安全锚点**：
  - `map_md5` —— 地图二进制哈希（首选匹配键）。
  - `map_id` / `export_map_id` —— 人类可读的场景 id（如 `campaign_01_01`），**MD5 对不上时的兜底匹配键**。
- **cif 只是 ini 的序列化格式**：`*.cif` 用 `cif2ini.py` 即可完美解成 `*.ini`。通常你直接提供 ini 版本，脚本优先吃 ini；
  仅当源只有 cif 时才用 `G:/Projects/Cultures_Saga_CN/cif2ini.py` 的 `cif2ini_content()` 解。
- **源抽取文件仍是原始代码页字节（重要，2026-08-18 实锤）**：输出侧 UTF-8 虽已落地，但波兰/捷克等源 `strings.ini/.cif` 本身是 cp1250 原始字节；`loc_tools.detect_encoding` 会因 cp1250 能在 cp1252（超集）下"成功解码"而先返回 cp1252，造成变音乱码。故 `integrate_lang_xml.py:decode_source()` **按语言→代码页显式优先解码**（pol/cz/sk…→cp1250，ru/uk…→cp1251），UTF-8 仍最优先。切勿再"统一交给 detect_encoding"。合并进 XML 的语言节点 `encoding="UTF-8"`。

## 步骤
1. **确认源语言与来源目录**（地图根，其下含各 `map_dir/{map.dat, text/<lang>/}`）。
   波兰示例源：`G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps`

2. **文本型语言（eng / ger / 你已解好的 ini）** → 直接用 `loc_tools.py`：
   ```bash
   # 多语言按 MD5 合并抽取为新 XML
   python Tools/loc_tools.py extract-batch -i <源根1> -i <源根2> -o _temp_xml/
   # 或把某语言追加进已有 XML（按 MD5 匹配）
   python Tools/loc_tools.py append -i Localization/map_xml/ --maps <含该语言的地图根>
   ```

3. **任意语言（含二进制 cif）** → 用专用脚本（内置 MD5 / id 双匹配 + id 一致性闸门）：
   ```bash
   python Tools/integrate_lang_xml.py --lang pol \
       --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps" --dry-run
   # 确认匹配数与 id 校验结果后真正写入（脚本先自动备份整个 map_xml 到 map_xml.bak_pol_<时间戳>）
   python Tools/integrate_lang_xml.py --lang pol \
       --source "G:/Projects/Cultures_Saga_Remix/Bramy Asgardu/DataX/Libs/data/maps"
   ```
   - 若源只有 cif（你没给 ini），脚本自动调用 `cif2ini.py` 解；可用 `--cif2ini <路径>` 指定。
   - 复用：换 cz/ru 只需改 `--lang` 与 `--source`。

4. **校验**
   ```bash
   python Tools/loc_tools.py validate -i Localization/map_xml/        # 结构校验
   ```
   - 抽查合并后 XML：确认 `<text lang="X">` / `<lang code="X">` 已填充。
   - 确认 `<languages>` 新增 `<language code="X" alias="X" encoding="UTF-8" fix_1251="false" base="false"/>`。

5. **收尾**：若有源引入含变音的文件名，跑 `python Tools/fix_xml_names.py` 校正；确认纯 LF。

## 关键坑（务必谨慎）
- **MD5 可能对不上**：不同游戏版本的 `map.dat` 哈希不同。脚本会**回退到 "目录名 ↔ map_id" 匹配**，
  并在**非 MD5 命中时强制做 id 一致性校验**——源语言的 string id 必须覆盖目标 XML 已有 id 的
  ≥90%，否则判定为"疑似错误地图"并**跳过告警**，绝不盲合。这是防止把 A 图翻译塞进 B 图的核心闸门。
- **永远先 --dry-run**：看清每文件的"匹配方式 [MD5|id(name)]"与 id 重叠率再写。
- **不要手改 base 语言**：ger 通常标记 `base="true"`，构建时脚本从源按 MD5 复制其地图脚本，勿误删。
- **cif 解码走 cif2ini，源字节按语言代码页解码**：cif 经 `cif2ini.py` 解成文本后，仍按 `decode_source()` 的语言→代码页规则解码（cp1250/cp1251），不要指望 `detect_encoding` 自动猜对。

# GER 严格一致性审计（XML vs GAME_2/3/4/5_MAP 源）

XML 总数 156 | OK 152 | 有问题 4 | 无源 0

## 问题分类

- BRIEF_WS_ONLY: 3
- BRIEF_EXTRA_XML: 1

## 无源 XML


## 有问题的 XML 明细

### campaign_01_09-sub.xml (map_id=campaign_01_09-sub, 匹配=name, 源=GAME_2_MAP/campaign_01_09-sub)
- BRIEF_EXTRA_XML:header

### campaign_02_01.xml (map_id=campaign_02_01, 匹配=name, 源=GAME_5_MAP/campaign_02_01)
- BRIEF_WS_ONLY:300

### campaign_02_02-sub.xml (map_id=campaign_02_02-sub, 匹配=name, 源=GAME_5_MAP/campaign_02_02-sub)
- BRIEF_WS_ONLY:200

### campaign_03_06.xml (map_id=campaign_03_06, 匹配=name, 源=GAME_5_MAP/campaign_03_06)
- BRIEF_WS_ONLY:300


## 结论与说明

- **156/156 XML 全部匹配到正确的源版本**（CSV 版本约束 + 名称匹配，MD5 交叉验证）。
- **152 个完全一致**：strings（stringn N）与 briefings（blockstart/end）逐条、逐节点精确匹配。
- **3 处仅行尾差异**：campaign_02_01 b:300、campaign_02_02-sub b:200、campaign_03_06 b:300 —— 源 briefings.txt 为 CRLF，XML 为 LF（仓库规范），内容完全一致，非错误。
- **1 处 XML 多余空块**：campaign_01_09-sub.xml 的 `header` 块在源 briefings.txt 中不存在（源块=start/lost/won/kampfsieg），且该块在 XML 内全语言为空（含 ger）。模板残留，无害；如需严格对齐可删除。
- **幽灵块核查**：0 处「XML ger 为空但源有内容」。XML 中所有空块在源 briefings.txt 中同样是 `[blockstart:X][blockend:X]` 空块。
- **数据完整性注意**：campaign_01_09 / campaign_01_09-sub 在 GAME_2_MAP 与 SAGA_GAME_HACK 均只有 text/、无 map.dat（XML map_md5 也为空）。ger 文本已核对一致，但二进制地图数据缺失，构建时这两张图的脚本复制会受影响——map.dat 可能在游戏的 .lib 归档内未解包。

# 翻译质量审计（基准 `ger`）

- 扫描文件总数: **156**


> **口径说明**

- **空翻 / 漏翻** 是明确缺陷，直接定位去填即可。

- **错行（行数不一致）**：经抽样核实，CHN 的错行几乎都是中文正常换行压缩（译文内容完整），
并非截断，**无需逐条修改**。如需严格校验需加入字符数/语义比对，行数启发式对中文是伪信号。

- 整文件缺语言 = 该文件未在 `<languages>` 声明此语言（覆盖缺口，是否补译由你决定）。


## 语言 `eng`

- 声明该语言的文件: **114/156**
（整文件缺失: 42）
- 单 key 漏翻: **0**
- 空翻(空值): **13**
- 错行(行数不一致): **6**
  - 其中疑似截断(差≥3): **0**


### `eng` 整文件缺失语言（42 个）

```
  _campaign_04_01.xml
  _campaign_04_01_sub1.xml
  _campaign_04_01_sub2.xml
  _campaign_04_01_sub3.xml
  _campaign_04_02.xml
  _campaign_04_02_sub1.xml
  _campaign_04_02_sub2.xml
  _campaign_04_03.xml
  _campaign_04_03_sub1.xml
  _campaign_04_04.xml
  _campaign_04_04_sub1.xml
  _campaign_04_04_sub2.xml
  _campaign_04_05.xml
  _campaign_04_05_sub1.xml
  01_Ein_neuer_Anfang.xml
  02_Spanien.xml
  03_Frankreich.xml
  04_Schweiz.xml
  05_Paris.xml
  06_Belgien.xml
  07_Germania.xml
  08_Österreich.xml
  09_Italien.xml
  10_Tunesien.xml
  11_Die_Unterwelt.xml
  12_Die_Prüfung.xml
  13_Das_Tal_der_Könige.xml
  14_Die_Eiswelt.xml
  15_Australien.xml
  16_Wigrid_Wall.xml
  17_Nordwestafrika.xml
  18_Tschad.xml
  19_Kongo.xml
  20_Die_Höhle.xml
  21_Südafrika.xml
  22_Daheim.xml
  01_Die_Pirateninsel.xml
  02_Die_Lavainsel.xml
  03_Verlorene_Welt.xml
  04_Die_Händler.xml
  05_Die_Münzsammler.xml
  06_Die_Entscheidung.xml
```

### `eng` 空翻（13 处，明确缺陷，优先修）

| 文件 | 位置 |
|---|---|
| campaign_01_09-sub.xml | b:header |
| campaign_02_02.xml | b:07 |
| campaign_03_01_sub.xml | b:50_end1 |
| campaign_03_02_sub.xml | b:03 |
| campaign_03_02_sub.xml | b:50_end1 |
| campaign_03_03.xml | b:990 |
| campaign_03_03_sub3.xml | b:09_end_header |
| campaign_03_05_sub1.xml | b:50_end1 |
| campaign_03_06.xml | b:20 |
| campaign_03_06_sub1.xml | b:50_end1 |
| campaign_03_06_sub2.xml | b:50_end1 |
| multiplayer_204_special_cap-the-flag.xml | b:38 |
| singleplayer_02_03.xml | b:begin_02 |

### `eng` 错行（6 处，待人工核对）

| 文件 | 位置 | ger行 | 译文行 | 疑似截断 |
|---|---|---|---|---|
| campaign_01_06.xml | b:gewonnen_01 | 2 | 3 |  |
| singleplayer_01_06.xml | b:7 | 3 | 4 |  |
| campaign_01_02-sub.xml | b:end | 3 | 2 |  |
| campaign_01_07.xml | b:spieler_attakiert_Byzanz | 6 | 5 |  |
| tutorial_001.xml | b:00 | 9 | 8 |  |
| campaign_01_07.xml | b:zerstörtesdorf | 4 | 2 |  |

## 语言 `chn`

- 声明该语言的文件: **156/156**
（整文件缺失: 0）
- 单 key 漏翻: **0**
- 空翻(空值): **29**
- 错行(行数不一致): **157**
  - 其中疑似截断(差≥3): **11**


### `chn` 空翻（29 处，明确缺陷，优先修）

| 文件 | 位置 |
|---|---|
| _campaign_04_01_sub1.xml | b:50_end |
| _campaign_04_01_sub1.xml | b:50_end1 |
| _campaign_04_01_sub2.xml | b:50_end1 |
| _campaign_04_01_sub3.xml | b:09 |
| _campaign_04_01_sub3.xml | b:50_end1 |
| _campaign_04_02.xml | b:11 |
| _campaign_04_02.xml | b:17 |
| _campaign_04_02.xml | b:18 |
| _campaign_04_02.xml | b:19 |
| _campaign_04_02.xml | b:20 |
| _campaign_04_02_sub2.xml | b:50_end1 |
| _campaign_04_03.xml | b:25 |
| _campaign_04_03_sub1.xml | b:50_end1 |
| _campaign_04_04_sub2.xml | b:50_end1 |
| _campaign_04_05.xml | b:25 |
| campaign_01_09-sub.xml | b:header |
| campaign_02_02.xml | b:07 |
| campaign_03_01_sub.xml | b:50_end1 |
| campaign_03_02_sub.xml | b:03 |
| campaign_03_02_sub.xml | b:50_end1 |
| campaign_03_03.xml | b:990 |
| campaign_03_03_sub3.xml | b:09_end_header |
| campaign_03_05_sub1.xml | b:50_end1 |
| campaign_03_06.xml | b:20 |
| campaign_03_06_sub1.xml | b:50_end1 |
| campaign_03_06_sub2.xml | b:50_end1 |
| multiplayer_204_special_cap-the-flag.xml | b:38 |
| singleplayer_02_03.xml | b:begin_02 |
| 14_Die_Eiswelt.xml | b:playerfriendly1 |

### `chn` 错行（157 处，待人工核对）

| 文件 | 位置 | ger行 | 译文行 | 疑似截断 |
|---|---|---|---|---|
| singleplayer_02_07.xml | s:3 | 1 | 8 | ⚠️ |
| _campaign_04_01_sub3.xml | b:50_end | 7 | 4 | ⚠️ |
| _campaign_04_05.xml | b:01 | 6 | 3 | ⚠️ |
| campaign_03_03.xml | b:273 | 13 | 10 | ⚠️ |
| campaign_03_03.xml | b:320 | 11 | 8 | ⚠️ |
| campaign_03_03.xml | b:450 | 11 | 8 | ⚠️ |
| multiplayer_103_special_militar.xml | b:begin_00 | 11 | 8 | ⚠️ |
| tutorial_005.xml | b:10 | 7 | 4 | ⚠️ |
| campaign_03_03.xml | b:00_start2 | 10 | 6 | ⚠️ |
| multiplayer_102_special_coop.xml | b:begin_00 | 12 | 8 | ⚠️ |
| campaign_01_03.xml | b:schiff_gebaut | 19 | 12 | ⚠️ |
| singleplayer_02_03.xml | b:begin_06 | 4 | 6 |  |
| tutorial_007.xml | b:100 | 1 | 3 |  |
| _campaign_04_03.xml | b:07 | 3 | 4 |  |
| _campaign_04_03.xml | b:16 | 3 | 4 |  |
| _campaign_04_03.xml | b:19 | 3 | 4 |  |
| _campaign_04_04.xml | b:03 | 4 | 5 |  |
| _campaign_04_05.xml | b:07 | 3 | 4 |  |
| _campaign_04_05.xml | b:15 | 3 | 4 |  |
| _campaign_04_05.xml | b:16 | 3 | 4 |  |
| demo_mainmenu_10.xml | b:00_start1 | 1 | 2 |  |
| singleplayer_02_01.xml | b:begin_32 | 7 | 8 |  |
| singleplayer_02_04.xml | b:begin_29 | 3 | 4 |  |
| singleplayer_02_04.xml | b:begin_30 | 2 | 3 |  |
| singleplayer_02_04.xml | b:begin_31 | 3 | 4 |  |
| singleplayer_02_04.xml | b:begin_32 | 2 | 3 |  |
| tutorial_005.xml | b:00 | 2 | 3 |  |
| tutorial_007.xml | b:06 | 1 | 2 |  |
| _campaign_04_01.xml | b:01 | 5 | 4 |  |
| _campaign_04_01.xml | b:02 | 5 | 4 |  |
| _campaign_04_01.xml | b:06 | 5 | 4 |  |
| _campaign_04_01.xml | b:10 | 4 | 3 |  |
| _campaign_04_01.xml | b:11 | 3 | 2 |  |
| _campaign_04_01.xml | b:24 | 3 | 2 |  |
| _campaign_04_01.xml | b:25 | 4 | 3 |  |
| _campaign_04_01.xml | b:50_end | 3 | 2 |  |
| _campaign_04_01_sub3.xml | b:00_start1 | 2 | 1 |  |
| _campaign_04_01_sub3.xml | b:02 | 5 | 4 |  |
| _campaign_04_01_sub3.xml | b:04 | 3 | 2 |  |
| _campaign_04_01_sub3.xml | b:05 | 5 | 4 |  |
| _campaign_04_01_sub3.xml | b:06 | 3 | 2 |  |
| _campaign_04_02.xml | b:09 | 4 | 3 |  |
| _campaign_04_02_sub2.xml | b:01 | 3 | 2 |  |
| _campaign_04_04_sub1.xml | b:00_start | 2 | 1 |  |
| _campaign_04_04_sub2.xml | b:00_start | 2 | 1 |  |
| _campaign_04_04_sub2.xml | b:50_end | 2 | 1 |  |
| _campaign_04_05.xml | b:14 | 3 | 2 |  |
| _campaign_04_05.xml | b:18 | 5 | 4 |  |
| campaign_01_02-sub.xml | b:start | 4 | 3 |  |
| campaign_01_02.xml | b:jäger | 5 | 4 |  |
| campaign_01_04.xml | b:won_01 | 2 | 1 |  |
| campaign_01_05-sub.xml | b:verließ | 4 | 3 |  |
| campaign_02_03.xml | b:03_Jäger1 | 3 | 2 |  |
| campaign_02_04-sub2.xml | b:02_unicorn | 4 | 3 |  |
| campaign_02_04.xml | b:04_player_2_seen_frank | 3 | 2 |  |
| campaign_02_08.xml | b:03_thor | 7 | 6 |  |
| campaign_03_02.xml | b:01 | 5 | 4 |  |
| campaign_03_02.xml | b:06 | 4 | 3 |  |
| campaign_03_03.xml | b:260 | 6 | 5 |  |
| campaign_03_03.xml | b:315 | 5 | 4 |  |
| campaign_03_03.xml | b:350 | 6 | 5 |  |
| campaign_03_03.xml | b:40 | 8 | 7 |  |
| campaign_03_03.xml | b:420 | 8 | 7 |  |
| campaign_03_03.xml | b:424 | 5 | 4 |  |
| campaign_03_03.xml | b:430 | 12 | 11 |  |
| campaign_03_03_sub1.xml | b:120 | 3 | 2 |  |
| campaign_03_03_sub2.xml | b:120 | 3 | 2 |  |
| campaign_03_03_sub3.xml | b:00_start | 5 | 4 |  |
| demo_mainmenu_10.xml | b:00_start | 2 | 1 |  |
| demo_mainmenu_10.xml | b:06 | 4 | 3 |  |
| demo_mainmenu_10.xml | b:08 | 5 | 4 |  |
| demo_mainmenu_10.xml | b:17 | 4 | 3 |  |
| demo_mainmenu_10.xml | b:19 | 3 | 2 |  |
| demo_singleplayer_02.xml | b:03 | 6 | 5 |  |
| demo_singleplayer_02.xml | b:15 | 9 | 8 |  |
| demo_singleplayer_02.xml | b:70 | 5 | 4 |  |
| demo_singleplayer_02.xml | b:75 | 7 | 6 |  |
| multiplayer_003_militar.xml | b:begin_00 | 3 | 2 |  |
| multiplayer_003_ressourcen.xml | b:begin_00 | 3 | 2 |  |
| multiplayer_004_militar.xml | b:begin_00 | 4 | 3 |  |
| multiplayer_004_ressourcen.xml | b:begin_00 | 4 | 3 |  |
| multiplayer_004_special_cap-the-cow.xml | b:begin_00 | 6 | 5 |  |
| multiplayer_105_militaer.xml | b:begin_00 | 4 | 3 |  |
| multiplayer_202_special_millitar.xml | b:begin_00 | 9 | 8 |  |
| singleplayer_01_06.xml | b:2 | 4 | 3 |  |
| singleplayer_01_06.xml | b:7 | 3 | 2 |  |
| singleplayer_01_07.xml | b:outpost | 3 | 2 |  |
| singleplayer_01_07.xml | b:starttext | 4 | 3 |  |
| singleplayer_02_01.xml | b:begin_01 | 12 | 11 |  |
| singleplayer_02_04.xml | b:begin_11 | 5 | 4 |  |
| singleplayer_03_01.xml | b:10 | 12 | 11 |  |
| singleplayer_03_04.xml | b:09 | 7 | 6 |  |
| singleplayer_03_05.xml | b:01 | 7 | 6 |  |
| tutorial_001.xml | b:00 | 9 | 8 |  |
| tutorial_001.xml | b:01 | 5 | 4 |  |
| tutorial_001.xml | b:04 | 5 | 4 |  |
| tutorial_001.xml | b:05 | 4 | 3 |  |
| tutorial_001.xml | b:10 | 5 | 4 |  |
| tutorial_003.xml | b:00 | 4 | 3 |  |
| tutorial_003.xml | b:03 | 4 | 3 |  |
| tutorial_003.xml | b:04 | 4 | 3 |  |
| tutorial_003.xml | b:05 | 8 | 7 |  |
| tutorial_004.xml | b:00 | 4 | 3 |  |
| tutorial_004.xml | b:14 | 4 | 3 |  |
| tutorial_004.xml | b:15 | 4 | 3 |  |
| tutorial_004.xml | b:16 | 4 | 3 |  |
| tutorial_004.xml | b:17 | 4 | 3 |  |
| tutorial_004.xml | b:18 | 4 | 3 |  |
| tutorial_005.xml | b:01 | 6 | 5 |  |
| tutorial_005.xml | b:03 | 5 | 4 |  |
| tutorial_005.xml | b:09 | 4 | 3 |  |
| tutorial_006.xml | b:01 | 4 | 3 |  |
| tutorial_006.xml | b:06 | 4 | 3 |  |
| tutorial_006.xml | b:15 | 8 | 7 |  |
| tutorial_006.xml | b:18 | 6 | 5 |  |
| tutorial_006.xml | b:19 | 5 | 4 |  |
| tutorial_007.xml | b:10 | 4 | 3 |  |
| weinachten_2002.xml | b:01 | 6 | 5 |  |
| _campaign_04_01_sub1.xml | b:01 | 8 | 6 |  |
| _campaign_04_01_sub3.xml | b:03 | 5 | 3 |  |
| _campaign_04_05.xml | b:03 | 5 | 3 |  |
| campaign_01_04.xml | b:soldierlimit | 3 | 1 |  |
| campaign_02_02.xml | b:15_Ykol | 7 | 5 |  |
| campaign_03_03.xml | b:00_start3 | 6 | 4 |  |
| campaign_03_03.xml | b:10 | 6 | 4 |  |
| campaign_03_03.xml | b:201 | 8 | 6 |  |
| campaign_03_03.xml | b:250 | 7 | 5 |  |
| campaign_03_03.xml | b:270 | 10 | 8 |  |
| campaign_03_03.xml | b:280 | 6 | 4 |  |
| campaign_03_03.xml | b:380 | 8 | 6 |  |
| campaign_03_03.xml | b:391 | 8 | 6 |  |
| campaign_03_03.xml | b:410 | 7 | 5 |  |
| campaign_03_03.xml | b:440 | 4 | 2 |  |
| campaign_03_03.xml | b:480 | 8 | 6 |  |
| multiplayer_005_ressourcen.xml | b:begin_00 | 7 | 5 |  |
| multiplayer_007_millitar.xml | b:begin_00 | 6 | 4 |  |
| multiplayer_007_special_coop.xml | b:begin_00 | 6 | 4 |  |
| multiplayer_101_special_coop.xml | b:begin_00 | 6 | 4 |  |
| multiplayer_105_ressourcen.xml | b:begin_00 | 5 | 3 |  |
| multiplayer_203_special_militar.xml | b:begin_00 | 13 | 11 |  |
| singleplayer_01_06.xml | b:0 | 6 | 4 |  |
| singleplayer_02_03.xml | b:begin_04 | 9 | 7 |  |
| singleplayer_03_01.xml | b:09 | 12 | 10 |  |
| singleplayer_03_03.xml | b:01 | 7 | 5 |  |
| singleplayer_03_03.xml | b:08 | 7 | 5 |  |
| tutorial_001.xml | b:07 | 7 | 5 |  |
| tutorial_003.xml | b:11 | 4 | 2 |  |
| tutorial_004.xml | b:12 | 7 | 5 |  |
| tutorial_005.xml | b:02 | 4 | 2 |  |
| tutorial_005.xml | b:04 | 5 | 3 |  |
| tutorial_005.xml | b:06 | 6 | 4 |  |
| tutorial_006.xml | b:08 | 7 | 5 |  |
| tutorial_006.xml | b:09 | 7 | 5 |  |
| tutorial_006.xml | b:14 | 9 | 7 |  |
| tutorial_006.xml | b:16 | 7 | 5 |  |
| tutorial_007.xml | b:01 | 5 | 3 |  |
| tutorial_007.xml | b:04 | 5 | 3 |  |
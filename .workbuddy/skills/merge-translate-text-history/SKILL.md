---
name: merge-translate-text-history
description: 把新 ger 源文本合并进 Localization/text/ger，并将 ger 翻译/补齐到 Localization/text/l10，重点补齐 2 代 Cultures 战役的 history 超文本。当要同步系统文本、或补全 l10 的 history 页面时使用。
---

# 工作流 2：合并/翻译到 Localization/text 并补齐 2 代 history

目标：`ger` = 权威德语源；`l10` = 中文产物（外挂 DLL 注入目标）。所有汉化以 ger 为准。
把 ger 源合并进 `Localization/text/ger/`，并把缺失/空缺的中文补齐进 `Localization/text/l10/`，
重点是 **history 超文本**（含 2 代 Cultures 战役内容）。

## 目录约定
- `text/ger/strings/*.cif`（二进制源）、少数 `.ini`；`text/l10/strings/*.ini`（构建产物）。
- **cif 是 ini 的序列化格式**：需要解 ger 的 `strings/*.cif` 时，用
  `G:/Projects/Cultures_Saga_CN/cif2ini.py`（或 `cif2ini_batch.py` 批量）完美解成 ini，通常你直接给 ini 版本。
- `text/<lang>/hypertext/{history,mythology,credits,ingamehelp}/`：`.hlt` 页面 + `*.txt` 文本库。
- `history/index.hlt` 用 `<include:$local$\history.txt,KEY,1>` 引用 `history.txt` 的
  `[blockstart:KEY]...[blockend:KEY]` 文本块，并用 `<globaljump:campaign_01_XX.hlt,0>` 跳转页面。
- **源文件仍是原始代码页字节（2026-08-18 实锤）**：ger 的 `strings/*.cif` 经 `cif2ini.py` 解出后仍是 cp1250/cp1251 原始字节，须按语言代码页解码（`detect_encoding` 会误判 cp1252 致乱码）；UTF-8 仅在构建产物生效。解 cif 只产出 l10，不动 ger 源编码。
- **相关文档**：语言映射 `language_id-zh-cn.md`、总流程 `20-language-translation-guide.md`、
  术语母表 `language_union.csv`（翻译术语时同步填该语言列）。

## 步骤
1. **同步 ger 源**（若游戏出了新版本文本）：把新 ger 的 `strings/*.cif`/`.ini` 与 `hypertext/**`
   合并进 `Localization/text/ger/`，保持目录结构不变。cif 用 `cif2ini.py` 解。

2. **定位 l10 缺失**（文件名级）：
   ```bash
   diff <(ls -1 Localization/text/ger/hypertext/history/) \
        <(ls -1 Localization/text/l10/hypertext/history/)
   ```
   常见差异：l10 缺 `fonts/` 与 `palettes/`（`.hlt` 引用的
   `$local$\fonts\*.fnt` / `$local$\palettes\*.pcx` 二进制资源）→ 必须从 ger 复制：
   ```bash
   cp -r Localization/text/ger/hypertext/history/fonts    Localization/text/l10/hypertext/history/fonts
   cp -r Localization/text/ger/hypertext/history/palettes Localization/text/l10/hypertext/history/palettes
   ```

3. **补齐 history 文本**（KEY 级）：
   - 逐 KEY 对比 `ger/hypertext/history/history.txt` 与 `l10/.../history.txt`：
     ger 有而 l10 缺失/为空的 KEY → 翻译并填入 l10 对应 `txt`；已存在但需校对的 → 对照 ger 修订。
   - "2 代 Cultures 战役"指 ger 已整合的后续战役 history（见 commit `95a4c90`）。
     确保 l10 的 `history.txt` 含 ger 全部 KEY，`campaign_XX_XX.hlt` / `mythology_XX.hlt`
     页面与 ger 一一对应（文件名相同）。

4. **字符串（strings）补齐**：
   - ger 的 `strings/*.cif` 是源，l10 的 `strings/*.ini` 是产物。
   - 若 l10 缺某 id：从 ger 对应 cif 经 `cif2ini.py` 解出 → 翻译为 l10 的 `strings.ini` 条目。
   - 可并行用工作流 1 的 `integrate_lang_xml.py` 处理地图 XML 内的同批字符串。

5. **CJK 强校验规则**
   - 半角 `'` → 全角 `'`。
   - 保留 ger 元音变音词（`überschrift`、`zurücktext` 等）在 l10 的**对应 key 名**（key 名按 ASCII 化，
     但内容须与 ger 对齐）。
   - 段落数（按 `\n`）l10 与 ger **严格对齐**。

6. **构建验证**
   ```bash
   python build_text.py                 # 构建到 _build/（GB2312）
   python convert_text_utf8.py          # 或 --force-utf8 双产物（UTF-8 + 保留变音）
   ```
   把 `_build/.../text/l10/` 部署进游戏，核对 history 页字体/调色板正常、无乱码。

7. **收尾**：纯 LF、精确 `git add`（避免 `-A`），不与 dirty/untracked 仓库自动交互。

## 关键坑
- **字体/调色板资源常被漏拷**：l10 history 显示异常多半是缺 `fonts/`/`palettes/`，先 diff 文件名。
- **history.txt 的 KEY 必须齐全**：`.hlt` 引用的 KEY 若在 l10 缺失，页面会空块。
- **不要改 ger 源编码**：ger 的 cif 由游戏原生，解码翻译时只产出 l10，不动 ger；编码交给 UTF-8 流水线。

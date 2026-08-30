#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 Localization/text/{eng,pol} 文本体系，对齐 ger/l10 结构。

阶段①步骤：
  A. 复制 28 个官方 ENG/POL strings ini（来自 OriginalText/GAME_4，回退 GAME_2/3）
  B. 生成 eng/pol 版 saga001.ini（从 ger 语义翻译，l10 中文为锚点，战役专名借用官方译法）
  C. 复制 ger hypertext 整树为骨架（含二进制资源 fonts/graphics/palettes，保证 include 解析），
     再覆盖 4 个 txt 为对应 ENG/POL 译文（history<-GAME_2, history/mythology<-GAME_4,
     ingamehelp/keys<-GAME_2/4, mythology/mythology<-GAME_3）
  D. 校验：ini 文件名集合==ger、每 ini 的 [text] string 数==ger、txt 的 [blockstart] 集合==ger

用法：
  python Tools/build_engpol_text.py            # 执行构建 + 校验
  python Tools/build_engpol_text.py --check-only  # 仅校验（不写）
"""
import os, re, shutil, sys

ROOT = "G:/Projects/CulturesGameLocalization"
GER_TXT = os.path.join(ROOT, "Localization/text/ger")
OT = os.path.join(ROOT, "OriginalText")

# saga001.ini 译文（结构严格照搬 ger：stringn 10 位置 + 17 条 string，顺序一致）
# 战役专名官方译法：Nordland=Reise nach Nordland(英 Northland / 波 Wyprawa na Północ)
#   Weltwunder=Das achte Weltwunder(英 Wonder of the World / 波 8 Cud Świata)
#   Saga(英 Saga / 波 Saga)；Die Tore Asgards(英 The Gates of Asgard / 波 Bramy Asgardu)
SAGA_ENG = '''[control]
stringidmultiplier 1
[text]
stringn 10 "'Northland' Campaign"
string "To the 'Northland' campaign screen"
string "'Wonder of the World' Campaign"
string "To the 'Wonder of the World' campaign screen"
string "'Saga' Campaign"
string "To the 'Saga' campaign screen"
string "Custom Campaigns"
string "To the custom campaigns screen"
string "'Yogi00' Campaign"
string "To the 'Yogi00' campaign screen"
string "'Yogi01' Campaign"
string "To the 'Yogi01' campaign screen"
string "Custom Campaigns"
string "'Yogi00' Campaign"
string "'Yogi01' Campaign"
string "'The Gates of Asgard' Campaign"
string "To the 'The Gates of Asgard' campaign screen"
'''

SAGA_POL = '''[control]
stringidmultiplier 1
[text]
stringn 10 "'Wyprawa na Północ' Kampania"
string "Do ekranu kampanii 'Wyprawa na Północ'"
string "'8 Cud Świata' Kampania"
string "Do ekranu kampanii '8 Cud Świata'"
string "'Saga' Kampania"
string "Do ekranu kampanii 'Saga'"
string "Kampanie użytkowników"
string "Do ekranu kampanii użytkowników"
string "'Yogi00' Kampania"
string "Do ekranu kampanii 'Yogi00'"
string "'Yogi01' Kampania"
string "Do ekranu kampanii 'Yogi01'"
string "Kampanie użytkowników"
string "'Yogi00' Kampania"
string "'Yogi01' Kampania"
string "'Bramy Asgardu' Kampania"
string "Do ekranu kampanii 'Bramy Asgardu'"
'''

# hypertext txt 源映射（rel 路径 -> 候选源，按序取第一个存在）
HTX_MAP = {
    "history/history.txt": [
        "{GAME}/GAME_2/{L}/hypertext/history/history.txt",
        "{GAME}/GAME_4/{L}/hypertext/history/history.txt",
    ],
    "history/mythology.txt": [
        "{GAME}/GAME_4/{L}/hypertext/history/mythology.txt",
    ],
    "ingamehelp/keys.txt": [
        "{GAME}/GAME_4/{L}/hypertext/ingamehelp/keys.txt",
        "{GAME}/GAME_2/{L}/hypertext/ingamehelp/keys.txt",
    ],
    "mythology/mythology.txt": [
        "{GAME}/GAME_3/{L}/hypertext/mythology/mythology.txt",
    ],
}

STRING_RE = re.compile(r'^\s*string(n)?\s')
BLOCK_RE = re.compile(r'\[blockstart:([^\]]+)\]')

def list_inis(base):
    out = []
    for dp, _, fs in os.walk(base):
        for f in fs:
            if f.endswith('.ini'):
                out.append(os.path.relpath(os.path.join(dp, f), base))
    return sorted(out)

def count_strings(path):
    n = 0
    in_text = False
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            s = line.strip()
            if s.startswith('[text]') or s.startswith('[TEXT]'):
                in_text = True; continue
            if s.startswith('[') and s.endswith(']') and s != '[text]':
                in_text = False; continue
            if in_text and STRING_RE.match(s):
                n += 1
    return n

def block_names(path, enc="utf-8"):
    names = set()
    with open(path, 'r', encoding=enc, errors='replace') as fh:
        for line in fh:
            m = BLOCK_RE.search(line)
            if m:
                names.add(m.group(1))
    return names

def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

def build_strings(lang):
    """复制 28 个官方 ini（不含 saga）；回退 GAME_2/3。"""
    src_game4 = os.path.join(OT, f"GAME_4/{lang}/strings")
    fallbacks = [os.path.join(OT, f"GAME_3/{lang}/strings"),
                 os.path.join(OT, f"GAME_2/{lang}/strings")]
    dst_root = os.path.join(ROOT, f"Localization/text/{lang.lower()}/strings")
    ger_inis = [r for r in list_inis(os.path.join(GER_TXT, "strings")) if r != "saga/saga001.ini"]
    copied = 0
    for rel in ger_inis:
        s = os.path.join(src_game4, rel)
        if not os.path.exists(s):
            for fb in fallbacks:
                cand = os.path.join(fb, rel)
                if os.path.exists(cand):
                    s = cand; break
        if not os.path.exists(s):
            print(f"  [WARN] {lang}: 找不到官方 ini -> {rel}")
            continue
        cp(s, os.path.join(dst_root, rel))
        copied += 1
    print(f"  [OK] {lang}: 复制 {copied} 个官方 ini")
    return copied

def build_saga(lang, content, encoding):
    dst = os.path.join(ROOT, f"Localization/text/{lang.lower()}/strings/saga/saga001.ini")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding=encoding, newline='\n') as fh:
        fh.write(content)
    print(f"  [OK] {lang}: 生成 saga001.ini ({encoding})")

def build_hypertext(lang):
    dst = os.path.join(ROOT, f"Localization/text/{lang.lower()}/hypertext")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    # 复制 ger 整树（结构 + 二进制资源）
    shutil.copytree(os.path.join(GER_TXT, "hypertext"), dst)
    # 覆盖 txt 译文
    replaced = 0
    for rel, cands in HTX_MAP.items():
        s = None
        for c in cands:
            p = c.format(GAME=OT, L=lang)
            if os.path.exists(p):
                s = p; break
        if s is None:
            print(f"  [WARN] {lang}: 找不到 txt 源 -> {rel}")
            continue
        cp(s, os.path.join(dst, rel))
        replaced += 1
    print(f"  [OK] {lang}: 复制 hypertext 骨架 + 覆盖 {replaced} 个 txt")

def validate():
    print("\n=== 校验 ===")
    ok = True
    ger_inis = list_inis(os.path.join(GER_TXT, "strings"))
    # 各语言 txt 正确解码编码：ger/l10=UTF-8；eng=cp1252；pol=cp1250
    TXT_ENC = {"eng": "cp1252", "pol": "cp1250"}
    for lang in ("eng", "pol"):
        dst_inis = list_inis(os.path.join(ROOT, f"Localization/text/{lang}/strings"))
        # 文件名集合
        if set(dst_inis) != set(ger_inis):
            ok = False
            miss = set(ger_inis) - set(dst_inis)
            extra = set(dst_inis) - set(ger_inis)
            print(f"  [FAIL] {lang}: ini 文件名集合不一致 缺={miss} 多={extra}")
        else:
            print(f"  [OK] {lang}: ini 文件名集合 == ger ({len(ger_inis)})")
        # 每 ini string 数
        for rel in ger_inis:
            g = os.path.join(GER_TXT, "strings", rel)
            d = os.path.join(ROOT, f"Localization/text/{lang}/strings", rel)
            if not os.path.exists(d):
                continue
            gc, dc = count_strings(g), count_strings(d)
            if gc != dc:
                ok = False
                print(f"  [FAIL] {lang}: {rel} string 数 ger={gc} != {lang}={dc}")
        # txt block 名
        for rel in HTX_MAP:
            g = os.path.join(GER_TXT, "hypertext", rel)
            d = os.path.join(ROOT, f"Localization/text/{lang}/hypertext", rel)
            if not os.path.exists(g) or not os.path.exists(d):
                continue
            gb, db = block_names(g, "utf-8"), block_names(d, TXT_ENC[lang])
            if gb != db:
                ok = False
                miss = gb - db; extra = db - gb
                print(f"  [FAIL] {lang}: {rel} block 名不一致 缺={sorted(miss)} 多={sorted(extra)}")
            else:
                print(f"  [OK] {lang}: {rel} block 名 == ger ({len(gb)})")
    print("\n校验结果:", "全部通过 ✅" if ok else "存在失败 ❌")
    return ok

def main():
    check_only = "--check-only" in sys.argv
    if not check_only:
        for lang in ("ENG", "POL"):
            print(f"\n--- {lang} strings ---")
            build_strings(lang)
        print("\n--- saga001.ini ---")
        build_saga("eng", SAGA_ENG, "cp1252")
        build_saga("pol", SAGA_POL, "cp1250")
        print("\n--- hypertext ---")
        for lang in ("ENG", "POL"):
            build_hypertext(lang)
    ok = validate()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()

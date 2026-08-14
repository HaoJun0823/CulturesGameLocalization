# -*- coding: utf-8 -*-
"""统计各游戏 logic 文件记录数与差异摘要"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
GAMES = ["GAME_2", "GAME_3", "GAME_4", "GAME_5"]
FILES = ["animaltypes.ini", "armortypes.ini", "atomicanimations/atomicanimations.ini",
         "goodtypes.ini", "housetypes.ini", "humanjobexperiencetypes.ini", "jobtypes.ini",
         "landscapetypes.ini", "trianglepatterntypes.ini", "tribetypes/tribetypes.ini",
         "vehicletypes.ini", "weapontypes.ini"]

print(f"{'文件':<42} " + " ".join(f"{g:>7}" for g in GAMES))
for f in FILES:
    counts = []
    for g in GAMES:
        p = os.path.join(ROOT, g, "logic", f)
        n = 0
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8-sig", errors="replace") as fp:
                n = sum(1 for ln in fp if ln.strip().startswith("["))
        counts.append(n)
    print(f"{f:<42} " + " ".join(f"{c:>7}" for c in counts))

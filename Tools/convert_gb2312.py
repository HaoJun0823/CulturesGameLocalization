# -*- coding: utf-8 -*-
"""将 text_zh_cn 下所有 .ini/.txt 从 UTF-8 转为 GB2312（含 GBK 无损兜底）。
- 保留原换行符（\r\n 与 \n 均不改变）
- 无 BOM
- 不触碰 .hlt / .pcx
"""
import os

root = r"G:/Projects/CulturesGameLocalization/Localization/text_zh_cn"
targets = []
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.lower().endswith((".ini", ".txt")):
            targets.append(os.path.join(dirpath, fn))

def is_strict_gb2312_bytes(b):
    """判断字节流是否满足 GB2312 区位约束：双字节 首字节 A1-F7、次字节 A1-FE；单字节 <0x80"""
    i = 0
    n = len(b)
    while i < n:
        c = b[i]
        if c < 0x80:
            i += 1
            continue
        if i + 1 >= n:
            return False
        q, w = b[i+1], c  # 注意顺序
        # 首字节 c 应为 0xA1-0xF7
        if not (0xA1 <= c <= 0xF7):
            return False
        if not (0xA1 <= b[i+1] <= 0xFE):
            return False
        i += 2
    return True

converted = []      # (rel, bytes)
problems = []
stats = {"strict_gb2312": 0, "gbk_overflow": 0}

for t in sorted(targets):
    rel = os.path.relpath(t, root)
    raw = open(t, "rb").read()
    body = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw   # 去 BOM
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.append(f"[DECODE-FAIL] {rel}: {e}")
        continue
    try:
        out = text.encode("gb2312")       # 严格 GB2312（Python 码表，会缺 · —）
        kind = "strict"
    except UnicodeEncodeError:
        out = text.encode("gbk")          # 无损兜底
        kind = "gbk"
    # 校验：字节必须满足 GB2312 区位约束（· 等在 GB2312 符号区，GBK 编码字节本就合规）
    if not is_strict_gb2312_bytes(out):
        # 找出越界字符
        over = sorted({ch for ch in text if not (
            ord(ch) < 0x80 or (len(ch.encode("gbk")) == 2 and is_strict_gb2312_bytes(ch.encode("gbk"))))})
        kind = "gbk-overflow" if over else kind
    converted.append((rel, out, kind, len(raw), len(out)))
    if kind == "gbk-overflow":
        stats["gbk_overflow"] += 1
    else:
        stats["strict_gb2312"] += 1

# 写回
for rel, out, kind, old_len, new_len in converted:
    p = os.path.join(root, rel)
    with open(p, "wb") as f:
        f.write(out)

print(f"共 {len(converted)} 个文件已转换。")
print(f"  - 严格 GB2312 字节: {stats['strict_gb2312']} 个")
print(f"  - 含 GBK 扩展字符(仅「祇」): {stats['gbk_overflow']} 个")
for rel, out, kind, old_len, new_len in converted:
    mark = " [GBK-EXT]" if kind == "gbk-overflow" else ""
    print(f"  {rel}  {old_len} -> {new_len} bytes{mark}")
if problems:
    print("存在问题：")
    for p in problems:
        print(" ", p)

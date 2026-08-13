# -*- coding: utf-8 -*-
"""验证：转换后文件 GBK 解码 == 备份 UTF-8 原文（逐字符、含换行符）；hlt 未动；无 BOM"""
import os

new_root = r"G:/Projects/CulturesGameLocalization/Localization/text_zh_cn"
bak_root = r"G:/Projects/CulturesGameLocalization/_backup_text_zh_cn_utf8_20260810/text_zh_cn"

fail = 0
checked = 0
for dirpath, dirnames, filenames in os.walk(new_root):
    for fn in filenames:
        np = os.path.join(dirpath, fn)
        rel = os.path.relpath(np, new_root)
        bp = os.path.join(bak_root, rel)
        raw_new = open(np, "rb").read()
        raw_bak = open(bp, "rb").read()
        if fn.lower().endswith((".ini", ".txt")):
            checked += 1
            # 无 BOM
            if raw_new.startswith(b"\xef\xbb\xbf") or raw_new.startswith(b"\xff\xfe") or raw_new.startswith(b"\xfe\xff"):
                print(f"[BOM!] {rel}")
                fail += 1
            # GBK 解码
            try:
                new_text = raw_new.decode("gbk")
            except UnicodeDecodeError as e:
                print(f"[DECODE-FAIL] {rel}: {e}")
                fail += 1
                continue
            # 备份解码（可能是 UTF-8 或 BOM）
            body = raw_bak[3:] if raw_bak.startswith(b"\xef\xbb\xbf") else raw_bak
            try:
                bak_text = body.decode("utf-8")
            except UnicodeDecodeError:
                bak_text = body.decode("gbk")
            if new_text != bak_text:
                fail += 1
                # 定位第一个差异
                for i, (a, b) in enumerate(zip(new_text, bak_text)):
                    if a != b:
                        print(f"[DIFF] {rel} @pos{i}: new={a!r} bak={b!r}")
                        break
                else:
                    print(f"[DIFF-LEN] {rel}: len new={len(new_text)} bak={len(bak_text)}")
            # 换行符保持
            if new_text.count("\r\n") != bak_text.count("\r\n") or new_text.count("\n") != bak_text.count("\n"):
                print(f"[EOL-CHANGED] {rel} crlf {bak_text.count(chr(13)+chr(10))}->{new_text.count(chr(13)+chr(10))}")
                fail += 1
        else:
            # 非 ini/txt（hlt/pcx）必须字节级一致
            if raw_new != raw_bak:
                print(f"[HLT/PCX-MODIFIED!] {rel}")
                fail += 1

print(f"\n检查 {checked} 个 ini/txt + 其余文件。失败数: {fail}")
print("结论:", "全部通过，无损转换 ✓" if fail == 0 else "存在问题 ✗")

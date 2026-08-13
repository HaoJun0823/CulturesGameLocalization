# -*- coding: utf-8 -*-
"""
map_xml 修复工具
================
1. 结构修复: 按 GER 的子元素序列重建 CHN (补 usericon/font/picture, text 顺序不变)
2. 内容重排: 对 _campaign_04 平移错位文件, 将 CHN block 内容整体平移并对齐 GER
用法: python fix_map_xml.py
"""
import os, re, sys, copy
import xml.etree.ElementTree as ET

ROOT = r"G:/Projects/CulturesGameLocalization/Localization"
MAP_XML = os.path.join(ROOT, "map_xml")

# 内容错位已全部修复, 现在对所有文件执行结构修复
MISMATCH_FILES = set()


def parse(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "cp1252"):
        try:
            return ET.fromstring(raw.decode(enc))
        except Exception:
            pass
    raise RuntimeError("parse fail: " + path)


def write(root, path):
    ET.indent(root, space="  ")
    data = ET.tostring(root, encoding="unicode")
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + data + "\n")


def fix_block_structure(block, dry=False):
    """按 GER 子元素序列重建 CHN lang。返回 (changed, reason)。"""
    langs = {l.get("code"): l for l in block.findall("lang")}
    cn, ge = langs.get("CHN"), langs.get("ger")
    if cn is None or ge is None:
        return False, "缺语言"
    cn_tags = [c.tag for c in cn]
    ge_tags = [c.tag for c in ge]
    if cn_tags == ge_tags:
        return False, ""
    cn_texts = [c for c in cn if c.tag == "text"]
    ge_texts = [c for c in ge if c.tag == "text"]
    if len(cn_texts) != len(ge_texts):
        return False, "text数量不一致(%d vs %d)" % (len(cn_texts), len(ge_texts))
    ge_nontext = [c for c in ge if c.tag != "text"]
    nti = 0
    gi = 0
    new_els = []
    for tag in ge_tags:
        if tag == "text":
            new_els.append(copy.deepcopy(cn_texts[gi]))
            gi += 1
        else:
            src = ge_nontext[nti]
            nti += 1
            el = ET.Element(tag, dict(src.attrib))
            el.text = src.text
            el.tail = "\n      "
            new_els.append(el)
    for i, el in enumerate(new_els):
        el.tail = "\n      " if i < len(new_els) - 1 else "\n    "
    # 替换(用切片赋值, 保留 lang 元素的 code 属性; 不能用 clear()——它会清掉属性)
    cn[:] = new_els
    return True, "CHN%s -> GER%s" % (cn_tags, ge_tags)


def main():
    n_fixed = 0
    n_skip_mismatch = 0
    for fn in sorted(os.listdir(MAP_XML)):
        if not fn.endswith(".xml"):
            continue
        if fn in MISMATCH_FILES:
            n_skip_mismatch += 1
            continue
        path = os.path.join(MAP_XML, fn)
        root = parse(path)
        changed_any = False
        for block in root.findall("./briefings/block"):
            ch, reason = fix_block_structure(block)
            if ch:
                changed_any = True
        if changed_any:
            write(root, path)
            n_fixed += 1
            print("FIX   %s" % fn)
    print("结构修复完成: %d 个文件; 跳过错位文件 %d 个" % (n_fixed, n_skip_mismatch))


if __name__ == "__main__":
    main()

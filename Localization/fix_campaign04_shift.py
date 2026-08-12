# -*- coding: utf-8 -*-
"""
_campaign_04 平移错位修复
========================
对 CHN 相对 GER 平移错位的文件, 按映射表重排 CHN block 内容。
映射规则: (目标block, 来源)
  ('X', 'COPY', 'Y')  -> block X 的 CHN 内容 = 旧 block Y 的 CHN 内容
  ('X', 'NEW', 文本)  -> block X 的 CHN 内容 = 新翻译文本(保留 GER 的空行/段落结构)
用法: python fix_campaign04_shift.py
"""
import os, copy
import xml.etree.ElementTree as ET

ROOT = r"G:/Projects/CulturesGameLocalization/Localization/map_xml"

# ============ 每个文件的修复映射 ============
FIXES = {
    # ---- _campaign_04_01_sub2: CHN 整体向前错位, 00_start 补译 ----
    "_campaign_04_01_sub2.xml": [
        ("00_start", "NEW",
         "\n玛尼与诺伯特再次踏入阿夸斯位于海底的水之神庙。在这陌生的环境里，他们的动作变得迟缓，眼前波光闪烁。\n\n"),
        ("00_start1", "COPY", "00_start"),
        ("01", "COPY", "00_start1"),
        ("02", "COPY", "01"),
        ("03", "COPY", "02"),
        ("500", "COPY", "03"),
    ],
    # ---- _campaign_04_01_sub3: CHN 整体向前错位, 00_start 补译 ----
    "_campaign_04_01_sub3.xml": [
        ("00_start", "NEW",
         "\n诺伯特与玛尼一路走到了这里。\n石龙的神圣殿堂就在他们面前。\n\n"),
        ("00_start1", "COPY", "00_start"),
        ("01", "COPY", "00_start1"),
        ("02", "COPY", "01"),
        ("03", "COPY", "02"),
        ("04", "COPY", "03"),
        ("05", "COPY", "04"),
        ("06", "COPY", "05"),
        ("07", "COPY", "06"),
        ("08", "COPY", "07"),
        ("500", "COPY", "08"),
    ],
}


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
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + data + "\n")


def get_blocks(root):
    return root.findall("./briefings/block")


def block_by_id(root, bid):
    for b in get_blocks(root):
        if b.get("id") == bid:
            return b
    return None


def set_chn_texts(block, texts):
    """把 block 的 CHN lang 替换为 [texts...] (每个元素一个 <text>, 文本原样保留)。"""
    langs = {l.get("code"): l for l in block.findall("lang")}
    cn = langs.get("CHN")
    if cn is None:
        return False
    # 只保留 GER 里非 text 元素的结构? 这里保持 CHN 现有非text元素数量即可。
    # 简单方案: 清空 CHN 的 text 子元素, 按 texts 重建; 非 text 元素保留。
    texts_els = [c for c in cn if c.tag == "text"]
    nontext = [c for c in cn if c.tag != "text"]
    new = []
    for i, t in enumerate(texts):
        el = ET.Element("text")
        el.text = t
        el.tail = "\n        "
        new.append(el)
    for el in new:
        el.tail = "\n        "
    cn[:] = new
    return True


def main():
    for fn, mapping in FIXES.items():
        path = os.path.join(ROOT, fn)
        root = parse(path)
        blocks = {b.get("id"): b for b in get_blocks(root)}
        # 先保存旧 CHN 内容(deepcopy)
        old_chn = {}
        for bid, b in blocks.items():
            langs = {l.get("code"): l for l in b.findall("lang")}
            cn = langs.get("CHN")
            if cn is not None:
                old_chn[bid] = copy.deepcopy(cn)
        # 应用映射
        for dest, kind, src in mapping:
            db = blocks.get(dest)
            if db is None:
                print("[!] %s: 找不到 block %s" % (fn, dest))
                continue
            langs = {l.get("code"): l for l in db.findall("lang")}
            cn = langs.get("CHN")
            if cn is None:
                print("[!] %s: block %s 无 CHN" % (fn, dest))
                continue
            if kind == "COPY":
                if src not in old_chn:
                    print("[!] %s: 旧 block %s 无 CHN" % (fn, src))
                    continue
                cn[:] = copy.deepcopy(list(old_chn[src]))
            elif kind == "NEW":
                cn[:] = [ET.Element("text")]
                cn[0].text = src
                cn[0].tail = "\n        "
        write(root, path)
        print("OK   %s (%d 处映射)" % (fn, len(mapping)))


if __name__ == "__main__":
    main()

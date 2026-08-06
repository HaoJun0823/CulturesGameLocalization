#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cultures Saga Translation Helper
读 XML，列出所有「源语言有原文、目标语言为空」的槽位，附源语言预览，便于批量翻译。

语言可参数化：--src-lang / --dst-lang（默认 ger -> CHN）。
用法：
  python Tools/trans_scan.py                                    # 扫全部（默认 ger->CHN）
  python Tools/trans_scan.py <xml路径>                          # 单文件
  python Tools/trans_scan.py <xml路径> --src-lang ger --dst-lang CHN
  python Tools/trans_scan.py --src-lang eng --dst-lang CHN      # 扫全部，eng 为源
"""
import xml.etree.ElementTree as ET
import sys, os, glob, argparse


def show_empty(xml_path, src_lang, dst_lang):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    map_id = root.get('map_id', 'unknown')

    print(f"\n=== {map_id} ===")

    strings = root.find('strings')
    empty_count = 0
    if strings is not None:
        for s in strings.findall('string'):
            sid = s.get('id', '?')
            src = dst = ""
            for t in s.findall('text'):
                if t.get('lang') == src_lang: src = (t.text or '').strip()
                if t.get('lang') == dst_lang: dst = (t.text or '').strip()
            if not dst and src:
                empty_count += 1
                print(f"  S:{sid} | {src[:100]}")

    briefings = root.find('briefings')
    if briefings is not None:
        for b in briefings.findall('block'):
            bid = b.get('id', '?')
            src_lang_elem = dst_lang_elem = None
            for l in b.findall('lang'):
                if l.get('code') == src_lang: src_lang_elem = l
                if l.get('code') == dst_lang: dst_lang_elem = l
            if dst_lang_elem is not None and src_lang_elem is not None:
                # Check if empty
                has_text = False
                for child in dst_lang_elem:
                    if child.tag == 'text' and child.text and child.text.strip():
                        has_text = True
                        break
                if not has_text:
                    # Extract source language text for reference
                    src_texts = []
                    for child in src_lang_elem:
                        if child.tag == 'text' and child.text:
                            src_texts.append(child.text.strip()[:120])
                    if src_texts:
                        empty_count += 1
                        preview = src_texts[0] if src_texts else "(empty)"
                        print(f"  B:{bid} ({len(src_texts)} texts) | {preview}")

    print(f"  >> {empty_count} empty entries")
    return empty_count


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="列出源语言有原文、目标语言为空的槽位")
    ap.add_argument("files", nargs="*", help="XML 文件路径（缺省=扫全部）")
    ap.add_argument("--src-lang", default="ger", help="源语言（默认 ger）")
    ap.add_argument("--dst-lang", default="CHN", help="目标语言（默认 CHN）")
    args = ap.parse_args()

    if args.files:
        files = args.files
    else:
        files = sorted(glob.glob('Localization/ZH-CN/map_xml/*.xml'))

    total = 0
    for f in files:
        total += show_empty(f, args.src_lang, args.dst_lang)
    print(f"\nTotal empty ({args.src_lang}->{args.dst_lang}): {total}")

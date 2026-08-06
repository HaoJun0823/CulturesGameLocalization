#!/usr/bin/env python3
"""
Cultures Saga Translation Helper
Reads XML, shows all empty CHN entries with German reference, helps batch translate
"""
import xml.etree.ElementTree as ET
import sys, os, glob

def show_empty_chn(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    map_id = root.get('map_id', 'unknown')
    
    print(f"\n=== {map_id} ===")
    
    strings = root.find('strings')
    empty_count = 0
    if strings is not None:
        for s in strings.findall('string'):
            sid = s.get('id', '?')
            chn = ger = ""
            for t in s.findall('text'):
                if t.get('lang') == 'CHN': chn = (t.text or '').strip()
                if t.get('lang') == 'ger': ger = (t.text or '').strip()
            if not chn and ger:
                empty_count += 1
                print(f"  S:{sid} | {ger[:100]}")
    
    briefings = root.find('briefings')
    if briefings is not None:
        for b in briefings.findall('block'):
            bid = b.get('id', '?')
            chn_lang = ger_lang = None
            for l in b.findall('lang'):
                if l.get('code') == 'CHN': chn_lang = l
                if l.get('code') == 'ger': ger_lang = l
            if chn_lang is not None and ger_lang is not None:
                # Check if empty
                has_text = False
                for child in chn_lang:
                    if child.tag == 'text' and child.text and child.text.strip():
                        has_text = True
                        break
                if not has_text:
                    # Extract German text for reference
                    ger_texts = []
                    for child in ger_lang:
                        if child.tag == 'text' and child.text:
                            ger_texts.append(child.text.strip()[:120])
                    if ger_texts:
                        empty_count += 1
                        preview = ger_texts[0] if ger_texts else "(empty)"
                        print(f"  B:{bid} ({len(ger_texts)} texts) | {preview}")
    
    print(f"  >> {empty_count} empty entries")
    return empty_count

if __name__ == '__main__':
    if len(sys.argv) < 2:
        files = sorted(glob.glob('Localization/ZH-CN/map_xml/*.xml'))
    else:
        files = [sys.argv[1]]
    
    total = 0
    for f in files:
        total += show_empty_chn(f)
    print(f"\nTotal empty: {total}")

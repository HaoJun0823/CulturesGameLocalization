# -*- coding: utf-8 -*-
"""修正 XML 文件名和 map_id 中的变音字符，对齐游戏目录名。"""
import re
from pathlib import Path

FIX_MAP = {'ä': 'a', 'Ä': 'A', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U', 'ß': 'ss'}

def fix1251(t):
    return ''.join(FIX_MAP.get(c, c) for c in t)

xml_dir = Path(__file__).resolve().parent.parent / "Localization" / "map_xml"
to_fix = [f for f in sorted(xml_dir.glob("*.xml")) if any(ord(c) > 127 for c in f.stem)]
print(f"待修正: {len(to_fix)} 个文件\n")

fixed = 0
for f in to_fix:
    old_name = f.name
    old_stem = f.stem
    new_stem = fix1251(old_stem)
    new_name = new_stem + ".xml"
    new_path = f.parent / new_name

    if new_path.exists():
        print(f"  [跳过] {old_name} -> {new_name} 已存在")
        continue

    # 读 XML
    text = f.read_text("utf-8")

    # 替换 map_id="..." 中的变音字符（保留 export_map_id 不变）
    # 只替换 map_id= 属性，不替换 export_map_id=
    text = re.sub(
        r'(map_id=")([^"]+)(")',
        lambda m: m.group(1) + fix1251(m.group(2)) + m.group(3),
        text
    )

    # 写回
    f.write_text(text, "utf-8")
    f.rename(new_path)

    print(f"  [OK] {old_name}")
    print(f"        -> {new_name}")
    fixed += 1

print(f"\n完成: {fixed} 个文件")

# 验证
remaining = [f for f in sorted(xml_dir.glob("*.xml")) if any(ord(c) > 127 for c in f.stem)]
if remaining:
    print(f"⚠️ 仍有 {len(remaining)} 个非ASCII文件名:")
    for f in remaining:
        print(f"  {f.name}")
else:
    print("✅ 所有文件名已ASCII化")
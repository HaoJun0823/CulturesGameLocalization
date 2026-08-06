#!/usr/bin/env python3
"""
Cultures Saga Localization Tool
用于提取和构建游戏本地化文件（strings.ini 和 briefings.txt）
输出格式：XML
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any


# 配置常量
VERSION = "1.3"
SUPPORTED_FILES = ["strings.ini", "briefings.txt"]


def md5_file(filepath: Path) -> str:
    """计算文件的MD5值"""
    if not filepath.exists():
        return ""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def detect_encoding(content: bytes) -> str:
    """检测文件编码"""
    encodings = ["utf-8", "windows-1252", "iso-8859-1", "cp1250"]
    for enc in encodings:
        try:
            content.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


FIX_1251_MAP = {
    'ä': 'a', 'Ä': 'A',
    'ë': 'e', 'Ë': 'E',
    'ï': 'i', 'Ï': 'I',
    'ö': 'o', 'Ö': 'O',
    'ü': 'u', 'Ü': 'U',
    'ß': 'ss',
    'à': 'a', 'À': 'A',
    'á': 'a', 'Á': 'A',
    'â': 'a', 'Â': 'A',
    'ã': 'a', 'Ã': 'A',
    'å': 'a', 'Å': 'A',
    'æ': 'ae', 'Æ': 'AE',
    'ç': 'c', 'Ç': 'C',
    'è': 'e', 'È': 'E',
    'é': 'e', 'É': 'E',
    'ê': 'e', 'Ê': 'E',
    'î': 'i', 'Î': 'I',
    'ì': 'i', 'Ì': 'I',
    'í': 'i', 'Í': 'I',
    'ð': 'd', 'Ð': 'D',
    'ñ': 'n', 'Ñ': 'N',
    'ò': 'o', 'Ò': 'O',
    'ó': 'o', 'Ó': 'O',
    'ô': 'o', 'Ô': 'O',
    'õ': 'o', 'Õ': 'O',
    'ø': 'o', 'Ø': 'O',
    'ù': 'u', 'Ù': 'U',
    'ú': 'u', 'Ú': 'U',
    'û': 'u', 'Û': 'U',
    'ý': 'y', 'Ý': 'Y',
    'þ': 'th', 'Þ': 'TH',
    'ÿ': 'y', 'Ÿ': 'Y',
}


def fix_1251_chars(text: str) -> str:
    """将特殊字符转换为英文字母，用于 GBK2312 编码输出"""
    return ''.join(FIX_1251_MAP.get(c, c) for c in text)


class StringsParser:
    """解析 strings.ini 文件"""
    
    STRING_RE = re.compile(r'stringn\s+(\d+)\s+"([^"]+)"')
    
    @classmethod
    def parse(cls, filepath: Path) -> Dict[str, str]:
        """解析 strings.ini，返回 {id: text}"""
        strings = {}
        if not filepath.exists():
            return strings
        
        content = filepath.read_bytes()
        enc = detect_encoding(content)
        text = content.decode(enc, errors="ignore")
        
        for match in cls.STRING_RE.finditer(text):
            str_id = match.group(1)
            str_text = match.group(2)
            strings[str_id] = str_text
        
        return strings
    
    @classmethod
    def build(cls, strings: Dict[str, str], filepath: Path, encoding: str = "windows-1252") -> None:
        """从字典生成 strings.ini"""
        lines = ["[text]"]
        for str_id, str_text in strings.items():
            lines.append(f'stringn {str_id} "{str_text}"')
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("\n".join(lines), encoding=encoding)


class BriefingsParser:
    """解析 briefings.txt 文件"""
    
    @classmethod
    def parse(cls, filepath: Path) -> Dict[str, List[Dict[str, str]]]:
        """解析 briefings.txt，返回 {block_id: [{'type': 'text|font|picture', 'value': ...}]}"""
        blocks = {}
        if not filepath.exists():
            return blocks
        
        content = filepath.read_bytes()
        enc = detect_encoding(content)
        text = content.decode(enc, errors="ignore")
        
        text = text.replace('\r\n', '\n')
        
        parts = re.split(r'(\[blockstart:\S+\]|\[blockend:\S+\])', text)
        
        current_block_id = None
        current_content = []
        
        for part in parts:
            if part.startswith('[blockstart:'):
                if current_block_id:
                    blocks[current_block_id] = cls._parse_block_content(''.join(current_content))
                current_block_id = part[12:-1]
                current_content = []
            elif part.startswith('[blockend:'):
                if current_block_id:
                    blocks[current_block_id] = cls._parse_block_content(''.join(current_content))
                current_block_id = None
                current_content = []
            elif current_block_id:
                current_content.append(part)
        
        if current_block_id:
            blocks[current_block_id] = cls._parse_block_content(''.join(current_content))
        
        return blocks
    
    @classmethod
    def _parse_block_content(cls, content: str) -> List[Dict[str, str]]:
        """解析块内容，提取标签和文本节点"""
        nodes = []
        
        tag_pattern = r'<(\w+):([^>]+)>'
        parts = re.split(tag_pattern, content)
        
        for i, part in enumerate(parts):
            if i % 3 == 0:
                if part.strip():
                    nodes.append({'type': 'text', 'value': part})
            elif i % 3 == 1:
                tag_type = part
            elif i % 3 == 2:
                tag_value = part
                nodes.append({'type': tag_type, 'value': tag_value})
        
        return nodes
    
    @classmethod
    def build(cls, blocks: Dict[str, List[Dict[str, str]]], filepath: Path, encoding: str = "windows-1252") -> None:
        """从结构化数据生成 briefings.txt

        block id 中的德语变音符号（ä/ö/ü/ß）会被 ASCII 化（fix_1251_chars）：
        官方中文版（POL_OLDCHN）的 block id 全部为 ASCII，游戏引擎按 ASCII id
        匹配对话段；变音 id 无法用 GBK 编码，故必须转写（10minutenspäter →
        10minutenspaeter）。
        """
        lines = []
        for block_id, nodes in blocks.items():
            ascii_id = fix_1251_chars(block_id)
            lines.append(f"[blockstart:{ascii_id}]")
            for i, node in enumerate(nodes):
                if node['type'] == 'text':
                    text_lines = node['value'].strip('\n').split('\n')
                    for j, line in enumerate(text_lines):
                        if j > 0:
                            lines.append("")
                        lines.append(line)
                else:
                    lines.append(f"<{node['type']}:{node['value']}>")
            lines.append(f"[blockend:{ascii_id}]")
            lines.append("")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text('\n'.join(lines).strip(), encoding=encoding)


def is_map_directory(path: Path) -> bool:
    """判断路径是否为地图目录（包含 map.dat 或 text/ 子目录）"""
    return (path / "map.dat").exists() or (path / "text").exists()


def is_c2m_map(map_dir: Path) -> bool:
    """判断地图是否为打包的 C2M 地图（True），还是文件夹形式地图（False）。

    当前 extract / extract-batch 仅处理文件夹形式地图（含 map.dat / text/），
    因此默认返回 False。若地图目录旁存在同名 .c2m 文件，或目录内直接含 .c2m，
    则视为已打包的 C2M 地图，返回 True。
    """
    if (map_dir.parent / f"{map_dir.name}.c2m").is_file():
        return True
    if any(map_dir.glob("*.c2m")):
        return True
    return False


def find_map_directories(root: Path) -> List[Path]:
    """查找所有地图目录"""
    maps = []
    if is_map_directory(root):
        return [root]
    
    for child in root.iterdir():
        if child.is_dir() and is_map_directory(child):
            maps.append(child)
    
    return sorted(maps)


def _is_map_root(d: Path) -> bool:
    """d 是否为真正的地图根（含 text/ 或 map.dat）。"""
    return d.is_dir() and ((d / "text").exists() or (d / "map.dat").exists())


def find_c2m_map_directories(root: Path) -> List[tuple]:
    """查找 C2M 解包后的地图目录。

    两种输入形态均可识别：
      形态 A（推荐）：<root>/<CampaignXX>/<mapname>/currentusermap/
        此时 root = <GER根>，返回 (map_dir=.../<mapname>, campaign=<CampaignXX>)
      形态 B：直接传入单个 <mapname> 目录（其内含 currentusermap/）
        此时返回 (map_dir=<mapname>, campaign="")

    判断标准：目录自身直接含有 ``text/`` 或 ``map.dat``（已是地图根），
    或含 ``currentusermap/`` 且该子目录是地图根。
    """
    results = []

    def _looks_like_map_dir(d: Path) -> bool:
        """d 是否为 <mapname> 目录（自身是地图根，或内含 currentusermap 地图根）。"""
        if not d.is_dir():
            return False
        if _is_map_root(d):
            return True
        return _is_map_root(d / "currentusermap")

    children = sorted([c for c in root.iterdir() if c.is_dir()])

    # 形态 B：root 自身即一个 <mapname> 地图目录
    if _looks_like_map_dir(root):
        return [(root, "")]

    # 形态 A：root 下是 <CampaignXX>，每个含若干 <mapname>
    for campaign_dir in children:
        if not campaign_dir.is_dir():
            continue
        for map_dir in sorted(campaign_dir.iterdir()):
            if _looks_like_map_dir(map_dir):
                results.append((map_dir, campaign_dir.name))

    if not results:
        # 退化：root 直接就是 <CampaignXX>（其下是 <mapname>）
        if children and all(_looks_like_map_dir(c) for c in children):
            for map_dir in children:
                results.append((map_dir, root.name))

    return results

def find_languages(text_dir: Path) -> List[str]:
    """查找 text/ 下的所有语言目录（3字符）"""
    languages = []
    if not text_dir.exists():
        return languages
    
    for child in text_dir.iterdir():
        if child.is_dir() and len(child.name) == 3:
            languages.append(child.name)
    
    return sorted(languages)


def extract_c2m_map(map_dir: Path, output_dir: Path, campaign: str = "") -> None:
    """提取单个 C2M 解包后的地图本地化内容。

    C2M 解包后的目录结构为：
        <GER根>/<CampaignXX>/<mapname>/currentusermap/{map.dat, text/ger/...}
    真正的地图目录是 ``currentusermap`` 这一层，而地图名取自其上一级
    ``<mapname>``。为避免所有地图都落到 ``currentusermap.xml`` 并保留战役
    目录结构（便于与原始 c2m 目录对应），输出文件命名为：
        <output_dir>/<CampaignXX>/<mapname>.xml
    且强制标记 IsC2M="true"（这是 reminder 标记，说明该地图源自 c2m）。
    """
    real_map_dir = map_dir / "currentusermap"
    if not _is_map_root(real_map_dir):
        real_map_dir = map_dir  # 容错：form B 时 map_dir 自身即是地图根
    map_id = map_dir.name
    map_md5 = md5_file(real_map_dir / "map.dat")

    text_dir = real_map_dir / "text"
    languages = find_languages(text_dir)

    if not languages:
        print(f"  [WARN] No languages found in {map_id}")
        return

    # 提取 strings.ini
    all_strings: Dict[str, Dict[str, str]] = {}
    for lang in languages:
        strings_path = text_dir / lang / "strings.ini"
        strings = StringsParser.parse(strings_path)
        for str_id, text in strings.items():
            if str_id not in all_strings:
                all_strings[str_id] = {}
            all_strings[str_id][lang] = text

    # 提取 briefings.txt
    all_briefings: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    for lang in languages:
        briefings_path = text_dir / lang / "briefings" / "briefings.txt"
        briefings = BriefingsParser.parse(briefings_path)
        for block_id, nodes in briefings.items():
            if block_id not in all_briefings:
                all_briefings[block_id] = {}
            all_briefings[block_id][lang] = nodes

    # 构建 XML 内容
    root = ET.Element("localization")
    root.set("version", VERSION)
    root.set("map_id", map_id)
    root.set("export_map_id", map_id)
    root.set("map_md5", map_md5)
    # C2M 解包地图：强制标记为 true（reminder 标记）
    root.set("IsC2M", "true")

    # Languages
    langs_elem = ET.SubElement(root, "languages")
    for lang in languages:
        lang_elem = ET.SubElement(langs_elem, "language")
        lang_elem.set("code", lang)
        lang_elem.set("alias", lang)
        lang_elem.set("encoding", "windows-1252")
        lang_elem.set("fix_1251", "false")

    # Strings
    strings_elem = ET.SubElement(root, "strings")
    for str_id in sorted(all_strings.keys(), key=lambda x: int(x)):
        str_elem = ET.SubElement(strings_elem, "string")
        str_elem.set("id", str_id)
        for lang in languages:
            text = all_strings[str_id].get(lang, "")
            lang_elem = ET.SubElement(str_elem, "text")
            lang_elem.set("lang", lang)
            lang_elem.text = text

    # Briefings
    briefings_elem = ET.SubElement(root, "briefings")
    for block_id in sorted(all_briefings.keys()):
        block_elem = ET.SubElement(briefings_elem, "block")
        block_elem.set("id", block_id)
        for lang in languages:
            nodes = all_briefings[block_id].get(lang, [])
            lang_elem = ET.SubElement(block_elem, "lang")
            lang_elem.set("code", lang)
            for node in nodes:
                if node['type'] == 'text':
                    text_elem = ET.SubElement(lang_elem, "text")
                    text_elem.text = node['value']
                else:
                    tag_elem = ET.SubElement(lang_elem, node['type'])
                    tag_elem.text = node['value']

    # 格式化输出
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)

    # 保留战役目录结构：<output_dir>/<CampaignXX>/<mapname>.xml
    out_subdir = output_dir / campaign if campaign else output_dir
    out_subdir.mkdir(parents=True, exist_ok=True)
    output_file = out_subdir / f"{map_id}.xml"

    with open(output_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8")

    print(f"  [OK] {map_id} (c2m) -> {output_file.name}")


def extract_map(map_dir: Path, output_dir: Path) -> None:
    """提取单个地图的本地化内容"""
    map_id = map_dir.name
    map_md5 = md5_file(map_dir / "map.dat")
    
    text_dir = map_dir / "text"
    languages = find_languages(text_dir)
    
    if not languages:
        print(f"  [WARN] No languages found in {map_id}")
        return
    
    # 提取 strings.ini
    all_strings: Dict[str, Dict[str, str]] = {}
    for lang in languages:
        strings_path = text_dir / lang / "strings.ini"
        strings = StringsParser.parse(strings_path)
        for str_id, text in strings.items():
            if str_id not in all_strings:
                all_strings[str_id] = {}
            all_strings[str_id][lang] = text
    
    # 提取 briefings.txt
    all_briefings: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    for lang in languages:
        briefings_path = text_dir / lang / "briefings" / "briefings.txt"
        briefings = BriefingsParser.parse(briefings_path)
        for block_id, nodes in briefings.items():
            if block_id not in all_briefings:
                all_briefings[block_id] = {}
            all_briefings[block_id][lang] = nodes
    
    # 构建 XML 内容
    root = ET.Element("localization")
    root.set("version", VERSION)
    root.set("map_id", map_id)
    root.set("export_map_id", map_id)
    root.set("map_md5", map_md5)
    # 元顶级信息：是否为打包的 C2M 地图（True）还是文件夹形式地图（False）
    root.set("IsC2M", "true" if is_c2m_map(map_dir) else "false")
    
    # Languages
    langs_elem = ET.SubElement(root, "languages")
    for lang in languages:
        lang_elem = ET.SubElement(langs_elem, "language")
        lang_elem.set("code", lang)
        lang_elem.set("alias", lang)
        lang_elem.set("encoding", "windows-1252")
        lang_elem.set("fix_1251", "false")
    
    # Strings
    strings_elem = ET.SubElement(root, "strings")
    for str_id in sorted(all_strings.keys(), key=lambda x: int(x)):
        str_elem = ET.SubElement(strings_elem, "string")
        str_elem.set("id", str_id)
        for lang in languages:
            text = all_strings[str_id].get(lang, "")
            lang_elem = ET.SubElement(str_elem, "text")
            lang_elem.set("lang", lang)
            lang_elem.text = text
    
    # Briefings
    briefings_elem = ET.SubElement(root, "briefings")
    for block_id in sorted(all_briefings.keys()):
        block_elem = ET.SubElement(briefings_elem, "block")
        block_elem.set("id", block_id)
        for lang in languages:
            nodes = all_briefings[block_id].get(lang, [])
            lang_elem = ET.SubElement(block_elem, "lang")
            lang_elem.set("code", lang)
            for node in nodes:
                if node['type'] == 'text':
                    text_elem = ET.SubElement(lang_elem, "text")
                    text_elem.text = node['value']
                else:
                    tag_elem = ET.SubElement(lang_elem, node['type'])
                    tag_elem.text = node['value']
    
    # 格式化输出
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    
    output_file = output_dir / f"{map_id}.xml"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8")
    
    print(f"  [OK] {map_id} -> {output_file.name}")


def extract_command(args: argparse.Namespace) -> None:
    """extract 命令：提取本地化内容"""
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else Path("translations")
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    if getattr(args, "c2m", False):
        # C2M 解包后的目录：<root>/<CampaignXX>/<mapname>/currentusermap/
        c2m_maps = find_c2m_map_directories(input_path)
        if not c2m_maps:
            print("Error: No C2M map directories found")
            sys.exit(1)
        print(f"Found {len(c2m_maps)} C2M map(s)")
        for map_dir, campaign in c2m_maps:
            extract_c2m_map(map_dir, output_dir, campaign)
        print(f"\nExtracted {len(c2m_maps)} C2M map(s) to {output_dir}")
        return
    
    map_dirs = find_map_directories(input_path)
    
    if not map_dirs:
        print("Error: No map directories found")
        sys.exit(1)
    
    print(f"Found {len(map_dirs)} map(s)")
    
    for map_dir in map_dirs:
        extract_map(map_dir, output_dir)
    
    print(f"\nExtracted {len(map_dirs)} map(s) to {output_dir}")


def parse_xml_file(xml_file: Path) -> Dict[str, Any]:
    """解析 XML 文件，返回数据结构"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    data = {
        "version": root.get("version", ""),
        "map_id": root.get("map_id", ""),
        "export_map_id": root.get("export_map_id", root.get("map_id", "")),
        "map_md5": root.get("map_md5", ""),
        "IsC2M": root.get("IsC2M", "false") == "true",
        "languages": [],
        "lang_configs": {},
        "strings": {},
        "briefings": {}
    }
    
    # 解析 Languages
    langs_elem = root.find("languages")
    if langs_elem is not None:
        for lang_elem in langs_elem.findall("language"):
            code = lang_elem.get("code", "")
            data["languages"].append(code)
            data["lang_configs"][code] = {
                "alias": lang_elem.get("alias", code),
                "encoding": lang_elem.get("encoding", "windows-1252"),
                "fix_1251": lang_elem.get("fix_1251", "false") == "true"
            }
    
    # 解析 Strings
    strings_elem = root.find("strings")
    if strings_elem is not None:
        for str_elem in strings_elem.findall("string"):
            str_id = str_elem.get("id", "")
            data["strings"][str_id] = {}
            for text_elem in str_elem.findall("text"):
                lang = text_elem.get("lang", "")
                data["strings"][str_id][lang] = text_elem.text or ""
    
    # 解析 Briefings
    briefings_elem = root.find("briefings")
    if briefings_elem is not None:
        for block_elem in briefings_elem.findall("block"):
            block_id = block_elem.get("id", "")
            data["briefings"][block_id] = {}
            for lang_elem in block_elem.findall("lang"):
                lang = lang_elem.get("code", "")
                nodes = []
                for child in lang_elem:
                    if child.tag == "text":
                        nodes.append({'type': 'text', 'value': child.text or ""})
                    else:
                        nodes.append({'type': child.tag, 'value': child.text or ""})
                data["briefings"][block_id][lang] = nodes
    
    return data


def write_xml_file(data: Dict[str, Any], xml_file: Path) -> None:
    """将数据结构写入 XML 文件"""
    root = ET.Element("localization")
    root.set("version", data["version"])
    root.set("map_id", data["map_id"])
    root.set("export_map_id", data.get("export_map_id", data["map_id"]))
    root.set("map_md5", data["map_md5"])
    root.set("IsC2M", "true" if data.get("IsC2M", False) else "false")
    
    # Languages
    langs_elem = ET.SubElement(root, "languages")
    for lang in data["languages"]:
        lang_elem = ET.SubElement(langs_elem, "language")
        lang_elem.set("code", lang)
        config = data.get("lang_configs", {}).get(lang, {})
        lang_elem.set("alias", config.get("alias", lang))
        lang_elem.set("encoding", config.get("encoding", "windows-1252"))
        lang_elem.set("fix_1251", "true" if config.get("fix_1251", False) else "false")
    
    # Strings
    strings_elem = ET.SubElement(root, "strings")
    for str_id in sorted(data.get("strings", {}).keys(), key=lambda x: int(x)):
        str_elem = ET.SubElement(strings_elem, "string")
        str_elem.set("id", str_id)
        for lang in data["languages"]:
            text = data["strings"][str_id].get(lang, "")
            lang_elem = ET.SubElement(str_elem, "text")
            lang_elem.set("lang", lang)
            lang_elem.text = text
    
    # Briefings
    briefings_elem = ET.SubElement(root, "briefings")
    for block_id in sorted(data.get("briefings", {}).keys()):
        block_elem = ET.SubElement(briefings_elem, "block")
        block_elem.set("id", block_id)
        for lang in data["languages"]:
            nodes = data["briefings"][block_id].get(lang, [])
            lang_elem = ET.SubElement(block_elem, "lang")
            lang_elem.set("code", lang)
            for node in nodes:
                if node['type'] == 'text':
                    text_elem = ET.SubElement(lang_elem, "text")
                    text_elem.text = node['value']
                else:
                    tag_elem = ET.SubElement(lang_elem, node['type'])
                    tag_elem.text = node['value']
    
    # 格式化输出
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    
    with open(xml_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8")


def add_language_to_xml(xml_file: Path, language: str, 
                         alias: str = None, encoding: str = "windows-1252", 
                         fix_1251: bool = False, fix_map_id: bool = False) -> bool:
    """向单个 XML 文件添加新语言"""
    data = parse_xml_file(xml_file)
    
    if language in data.get("languages", []):
        print(f"  [SKIP] {xml_file.name}: Language '{language}' already exists")
        return False
    
    data["languages"].append(language)
    data["languages"].sort()
    
    if "lang_configs" not in data:
        data["lang_configs"] = {}
    data["lang_configs"][language] = {
        "alias": alias if alias else language,
        "encoding": encoding,
        "fix_1251": fix_1251
    }
    
    for str_id in data.get("strings", {}):
        data["strings"][str_id][language] = ""
    
    for block_id in data.get("briefings", {}):
        lang_map = data["briefings"][block_id]
        if lang_map:
            first_lang = next(iter(lang_map.keys()))
            template_nodes = lang_map[first_lang]
            new_nodes = []
            for node in template_nodes:
                if node['type'] == 'text':
                    new_nodes.append({'type': 'text', 'value': ""})
                else:
                    new_nodes.append({'type': node['type'], 'value': node['value']})
            data["briefings"][block_id][language] = new_nodes
        else:
            data["briefings"][block_id][language] = []
    
    if fix_map_id:
        export_map_id = data.get("export_map_id", data.get("map_id", ""))
        fixed_map_id = fix_1251_chars(export_map_id)
        if fixed_map_id != export_map_id:
            data["export_map_id"] = fixed_map_id
            print(f"  [INFO] {xml_file.name}: Fixed export_map_id '{export_map_id}' -> '{fixed_map_id}'")
    
    write_xml_file(data, xml_file)
    
    print(f"  [OK] {xml_file.name}: Added language '{language}' (alias: {alias if alias else language}, encoding: {encoding}, fix_1251: {fix_1251})")
    return True


def lang_add_command(args: argparse.Namespace) -> None:
    """lang-add 命令：向 XML 文件添加新语言"""
    input_path = Path(args.input)
    language = args.language.strip().upper() if len(args.language) <= 3 else args.language
    
    if len(language) != 3:
        print(f"Error: Language code must be 3 characters (got '{language}')")
        sys.exit(1)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    xml_files = []
    if input_path.is_file() and input_path.suffix == ".xml":
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    
    if not xml_files:
        print("Error: No XML files found")
        sys.exit(1)
    
    alias = getattr(args, 'alias', None)
    encoding = getattr(args, 'encoding', "windows-1252")
    fix_1251 = getattr(args, 'fix_1251', False)
    fix_map_id = getattr(args, 'fix_map_id', False)
    
    print(f"Adding language '{language}' to {len(xml_files)} XML file(s)...")
    print(f"  Alias: {alias if alias else language}")
    print(f"  Encoding: {encoding}")
    print(f"  fix_1251: {fix_1251}")
    print(f"  fix_map_id: {fix_map_id}")
    
    count = 0
    for xml_file in xml_files:
        if add_language_to_xml(xml_file, language, alias, encoding, fix_1251, fix_map_id):
            count += 1
    
    print(f"\nAdded language '{language}' to {count} file(s)")


def remove_language_from_xml(xml_file: Path, language: str) -> bool:
    """从单个 XML 文件删除语言"""
    data = parse_xml_file(xml_file)
    
    if language not in data.get("languages", []):
        print(f"  [SKIP] {xml_file.name}: Language '{language}' not found")
        return False
    
    data["languages"].remove(language)
    
    for str_id in data.get("strings", {}):
        data["strings"][str_id].pop(language, None)
    
    for block_id in data.get("briefings", {}):
        data["briefings"][block_id].pop(language, None)
    
    write_xml_file(data, xml_file)
    
    print(f"  [OK] {xml_file.name}: Removed language '{language}'")
    return True


def lang_remove_command(args: argparse.Namespace) -> None:
    """lang-remove 命令：从 XML 文件删除语言"""
    input_path = Path(args.input)
    language = args.language.strip().upper() if len(args.language) <= 3 else args.language
    
    if len(language) != 3:
        print(f"Error: Language code must be 3 characters (got '{language}')")
        sys.exit(1)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    xml_files = []
    if input_path.is_file() and input_path.suffix == ".xml":
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    
    if not xml_files:
        print("Error: No XML files found")
        sys.exit(1)
    
    print(f"Removing language '{language}' from {len(xml_files)} XML file(s)...")
    
    count = 0
    for xml_file in xml_files:
        if remove_language_from_xml(xml_file, language):
            count += 1
    
    print(f"\nRemoved language '{language}' from {count} file(s)")


def copy_map_data(src_map_dir: Path, dst_map_dir: Path) -> None:
    """复制地图数据（排除 text/ 目录）"""
    if not src_map_dir.exists():
        return
    
    dst_map_dir.mkdir(parents=True, exist_ok=True)
    
    for item in src_map_dir.iterdir():
        if item.name == "text":
            continue
        
        dst_item = dst_map_dir / item.name
        
        if item.is_dir():
            shutil.copytree(item, dst_item, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst_item)


def find_all_map_dat(map_data_dir: Path) -> Dict[str, Path]:
    """递归搜索所有 map.dat 文件，返回 {md5: directory_path}"""
    md5_to_dir = {}
    
    for map_dat in map_data_dir.rglob("map.dat"):
        map_dir = map_dat.parent
        map_md5 = md5_file(map_dat)
        if map_md5 and map_md5 not in md5_to_dir:
            md5_to_dir[map_md5] = map_dir
    
    return md5_to_dir


def build_map(xml_file: Path, output_dir: Path, language: str, 
              map_data_dir: Optional[Path] = None,
              md5_to_dir: Optional[Dict[str, Path]] = None) -> None:
    """从 XML 文件构建单个地图的本地化文件"""
    data = parse_xml_file(xml_file)
    
    map_id = data.get("map_id")
    map_md5 = data.get("map_md5", "")
    export_map_id = data.get("export_map_id", map_id)
    strings_data = data.get("strings", {})
    briefings_data = data.get("briefings", {})
    
    # CHN 语言构建修正：
    #  1) 编码：统一 GB2312（游戏仅支持 GB2312，不支持 GBK 扩展）。XML 配置写
    #     GB2312 或 windows-1252 均覆盖为 GB2312。要求源 XML 文本本身已为
    #     GB2312 兼容（超集字形在汉化源中直接改掉，不做运行时替换）。
    #  2) 输出目录：无论主战役还是 C2M 用户地图，中文统一输出到 text/l10/——
    #     l10 是外挂汉化注入的目标语言目录（项目规范「chn输出为l10」），
    #     与源数据里是否只有 ger 无关（GAME_5_MAP 普通地图源也只有 ger，但 l10 照样加载）。
    #     因此 C2M 的 alias 也统一为 l10（若 XML 配置 alias 为 CHN/ger 等则覆盖）。
    if language.upper() == "CHN":
        lang_config = dict(data.get("lang_configs", {}).get(language, {}))
        lang_config["encoding"] = "GB2312"       # 游戏仅支持 GB2312
        lang_config["alias"] = "l10"             # 中文输出目录统一 text/l10/
    else:
        lang_config = data.get("lang_configs", {}).get(language, {})
    output_lang = lang_config.get("alias", language)
    encoding = lang_config.get("encoding", "windows-1252")
    apply_fix_1251 = lang_config.get("fix_1251", False)
    
    map_output_dir = output_dir / export_map_id
    
    if map_data_dir:
        if md5_to_dir is None:
            md5_to_dir = find_all_map_dat(map_data_dir)
        
        if map_md5 and map_md5 in md5_to_dir:
            src_map_dir = md5_to_dir[map_md5]
            copy_map_data(src_map_dir, map_output_dir)
            print(f"  [INFO] Copied map data from {src_map_dir}")
        else:
            print(f"  [WARN] Map data not found for MD5 {map_md5[:8] if map_md5 else '(empty)'}")
    
    text_output_dir = map_output_dir / "text" / output_lang
    text_output_dir.mkdir(parents=True, exist_ok=True)
    
    strings = {}
    for str_id, lang_map in strings_data.items():
        text = lang_map.get(language, "")
        if not text:
            text = next(iter(lang_map.values()), "")
        if apply_fix_1251:
            text = fix_1251_chars(text)
        strings[str_id] = text
    
    strings_path = text_output_dir / "strings.ini"
    StringsParser.build(strings, strings_path, encoding)
    
    briefings = {}
    for block_id, lang_map in briefings_data.items():
        nodes = lang_map.get(language, [])
        if not nodes:
            nodes = next(iter(lang_map.values()), [])
        if apply_fix_1251:
            processed_nodes = []
            for node in nodes:
                if node['type'] == 'text':
                    processed_nodes.append({'type': 'text', 'value': fix_1251_chars(node['value'])})
                else:
                    processed_nodes.append(node)
            briefings[block_id] = processed_nodes
        else:
            briefings[block_id] = nodes
    
    briefings_path = text_output_dir / "briefings" / "briefings.txt"
    BriefingsParser.build(briefings, briefings_path, encoding)
    
    print(f"  [OK] {map_id} -> {map_output_dir.name} (encoding: {encoding}, fix_1251: {apply_fix_1251})")


def build_command(args: argparse.Namespace) -> None:
    """build 命令：从 XML 构建本地化文件"""
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else Path("output")
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    if not args.language:
        print("Error: --language (-l) is required")
        sys.exit(1)
    
    map_data_dir = Path(args.map_data) if args.map_data else None
    if map_data_dir and not map_data_dir.exists():
        print(f"Error: Map data path does not exist: {map_data_dir}")
        sys.exit(1)
    
    xml_files = []
    if input_path.is_file() and input_path.suffix == ".xml":
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    
    if not xml_files:
        print("Error: No XML files found")
        sys.exit(1)
    
    print(f"Found {len(xml_files)} XML file(s)")
    print(f"Building language: {args.language}")
    
    md5_to_dir = None
    if map_data_dir:
        print(f"Searching for map data in: {map_data_dir}")
        md5_to_dir = find_all_map_dat(map_data_dir)
        print(f"Found {len(md5_to_dir)} map(s) by MD5")
    
    for xml_file in xml_files:
        build_map(xml_file, output_dir, args.language, map_data_dir, md5_to_dir)
    
    print(f"\nBuilt {len(xml_files)} map(s) to {output_dir}")


def validate_command(args: argparse.Namespace) -> None:
    """validate 命令：验证 XML 文件完整性"""
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    xml_files = []
    if input_path.is_file() and input_path.suffix == ".xml":
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    
    if not xml_files:
        print("Error: No XML files found")
        sys.exit(1)
    
    print(f"Validating {len(xml_files)} XML file(s)...")
    
    errors = 0
    for xml_file in xml_files:
        try:
            data = parse_xml_file(xml_file)
            
            required_fields = ["version", "map_id", "languages", "strings", "briefings"]
            for field in required_fields:
                if field not in data:
                    print(f"  [ERROR] {xml_file.name}: Missing field '{field}'")
                    errors += 1
            
            print(f"  [OK] {xml_file.name}")
        except Exception as e:
            print(f"  [ERROR] {xml_file.name}: {e}")
            errors += 1
    
    if errors > 0:
        print(f"\nValidation failed with {errors} errors")
        sys.exit(1)
    else:
        print("\nValidation passed!")


def append_language_to_xml(xml_file: Path, map_dir: Path) -> bool:
    """将地图目录中的语言内容追加到 XML 文件"""
    data = parse_xml_file(xml_file)
    
    map_id = data.get("map_id")
    xml_md5 = data.get("map_md5", "")
    
    new_md5 = md5_file(map_dir / "map.dat")
    if xml_md5 and new_md5 and xml_md5 != new_md5:
        print(f"  [SKIP] {xml_file.name}: MD5 mismatch ({xml_md5[:8]} vs {new_md5[:8]})")
        return False
    
    text_dir = map_dir / "text"
    languages = find_languages(text_dir)
    
    if not languages:
        print(f"  [SKIP] {xml_file.name}: No languages found in map")
        return False
    
    added = False
    
    all_strings: Dict[str, Dict[str, str]] = {}
    for lang in languages:
        strings_path = text_dir / lang / "strings.ini"
        strings = StringsParser.parse(strings_path)
        for str_id, text in strings.items():
            if str_id not in all_strings:
                all_strings[str_id] = {}
            all_strings[str_id][lang] = text
    
    all_briefings: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    for lang in languages:
        briefings_path = text_dir / lang / "briefings" / "briefings.txt"
        briefings = BriefingsParser.parse(briefings_path)
        for block_id, nodes in briefings.items():
            if block_id not in all_briefings:
                all_briefings[block_id] = {}
            all_briefings[block_id][lang] = nodes
    
    for lang in languages:
        if lang in data.get("languages", []):
            print(f"  [SKIP] {xml_file.name}: Language '{lang}' already exists")
            continue
        
        data["languages"].append(lang)
        data["languages"].sort()
        
        if "lang_configs" not in data:
            data["lang_configs"] = {}
        data["lang_configs"][lang] = {
            "alias": lang,
            "encoding": "windows-1252",
            "fix_1251": False
        }
        
        for str_id in data.get("strings", {}):
            data["strings"][str_id][lang] = all_strings.get(str_id, {}).get(lang, "")
        
        for block_id in data.get("briefings", {}):
            nodes = all_briefings.get(block_id, {}).get(lang, [])
            if nodes:
                data["briefings"][block_id][lang] = nodes
            else:
                if block_id in data["briefings"]:
                    first_lang = next(iter(data["briefings"][block_id].keys()), None)
                    if first_lang:
                        template_nodes = data["briefings"][block_id][first_lang]
                        new_nodes = []
                        for node in template_nodes:
                            if node['type'] == 'text':
                                new_nodes.append({'type': 'text', 'value': ""})
                            else:
                                new_nodes.append({'type': node['type'], 'value': node['value']})
                        data["briefings"][block_id][lang] = new_nodes
        
        added = True
        print(f"  [OK] {xml_file.name}: Added language '{lang}'")
    
    if added:
        for str_id, lang_map in all_strings.items():
            if str_id not in data["strings"]:
                data["strings"][str_id] = {}
            for lang, text in lang_map.items():
                if lang not in data["strings"][str_id]:
                    data["strings"][str_id][lang] = text
        
        for block_id, lang_map in all_briefings.items():
            if block_id not in data["briefings"]:
                data["briefings"][block_id] = {}
            for lang, nodes in lang_map.items():
                if lang not in data["briefings"][block_id]:
                    data["briefings"][block_id][lang] = nodes
        
        write_xml_file(data, xml_file)
    
    return added


def append_command(args: argparse.Namespace) -> None:
    """append 命令：根据 MD5 自动追加其他语言到 XML 文件"""
    input_path = Path(args.input)
    map_path = Path(args.maps)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    if not map_path.exists():
        print(f"Error: Map path does not exist: {map_path}")
        sys.exit(1)
    
    xml_files = []
    if input_path.is_file() and input_path.suffix == ".xml":
        xml_files = [input_path]
    elif input_path.is_dir():
        xml_files = sorted(input_path.glob("*.xml"))
    
    if not xml_files:
        print("Error: No XML files found")
        sys.exit(1)
    
    map_dirs = find_map_directories(map_path)
    
    if not map_dirs:
        print("Error: No map directories found")
        sys.exit(1)
    
    print(f"Found {len(xml_files)} XML file(s)")
    print(f"Found {len(map_dirs)} map directory(ies)")
    
    md5_to_map = {}
    for map_dir in map_dirs:
        map_md5 = md5_file(map_dir / "map.dat")
        md5_to_map[map_md5] = map_dir
    
    count = 0
    for xml_file in xml_files:
        try:
            data = parse_xml_file(xml_file)
            xml_md5 = data.get("map_md5", "")
            
            if xml_md5 and xml_md5 in md5_to_map:
                if append_language_to_xml(xml_file, md5_to_map[xml_md5]):
                    count += 1
            elif xml_md5:
                print(f"  [SKIP] {xml_file.name}: No matching map found for MD5 {xml_md5[:8]}")
            else:
                for map_dir in map_dirs:
                    map_name = map_dir.name
                    xml_name = xml_file.stem
                    if map_name == xml_name:
                        if append_language_to_xml(xml_file, map_dir):
                            count += 1
                        break
                else:
                    print(f"  [SKIP] {xml_file.name}: No matching map found")
        except Exception as e:
            print(f"  [ERROR] {xml_file.name}: {e}")
    
    print(f"\nUpdated {count} file(s)")


def extract_batch_command(args: argparse.Namespace) -> None:
    """extract-batch 命令：从多个文件夹批量提取本地化内容"""
    input_dirs = args.input
    output_dir = Path(args.output) if args.output else Path("translations")
    
    if getattr(args, "c2m", False):
        # C2M 模式：每个 input 是 <CampaignXX> 的父级（或本身即 <CampaignXX>）
        c2m_maps = []
        for input_dir in input_dirs:
            path = Path(input_dir)
            if not path.exists():
                print(f"Error: Input path does not exist: {input_dir}")
                sys.exit(1)
            c2m_maps.extend(find_c2m_map_directories(path))
        if not c2m_maps:
            print("Error: No C2M map directories found")
            sys.exit(1)
        print(f"Found {len(c2m_maps)} C2M map(s) across {len(input_dirs)} input directories")
        seen = set()
        for map_dir, campaign in c2m_maps:
            key = (campaign, map_dir.name)
            if key in seen:
                continue
            seen.add(key)
            extract_c2m_map(map_dir, output_dir, campaign)
        print(f"\nExtracted {len(seen)} C2M map(s) to {output_dir}")
        return
    
    all_map_dirs = []
    for input_dir in input_dirs:
        path = Path(input_dir)
        if not path.exists():
            print(f"Error: Input path does not exist: {input_dir}")
            sys.exit(1)
        
        map_dirs = find_map_directories(path)
        all_map_dirs.extend(map_dirs)
    
    if not all_map_dirs:
        print("Error: No map directories found")
        sys.exit(1)
    
    print(f"Found {len(all_map_dirs)} map(s) across {len(input_dirs)} input directories")
    
    md5_to_map = {}
    for map_dir in all_map_dirs:
        map_md5 = md5_file(map_dir / "map.dat")
        if map_md5 not in md5_to_map:
            md5_to_map[map_md5] = map_dir
    
    print(f"Processing {len(md5_to_map)} unique map(s)...")
    
    for map_md5, map_dir in md5_to_map.items():
        extract_map(map_dir, output_dir)
    
    for map_dir in all_map_dirs:
        map_md5 = md5_file(map_dir / "map.dat")
        if md5_to_map.get(map_md5) != map_dir:
            xml_file = output_dir / f"{map_dir.name}.xml"
            if xml_file.exists():
                append_language_to_xml(xml_file, map_dir)
    
    print(f"\nExtracted {len(md5_to_map)} map(s) to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description=f"Cultures Saga Localization Tool v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  extract      - 提取地图本地化内容到 XML 文件
  extract-batch - 从多个文件夹批量提取本地化内容
  build        - 从 XML 文件构建本地化文件
  append       - 根据 MD5 自动追加其他语言到 XML 文件
  lang-add     - 向 XML 文件添加新语言
  lang-remove  - 从 XML 文件删除语言
  validate     - 验证 XML 文件完整性

Examples:
  # 提取单个地图
  python loc_tools.py extract -i "GAME_2_MAP/ENG/campaign_01_08" -o "translations/"
  
  # 提取目录中所有地图
  python loc_tools.py extract -i "GAME_2_MAP/ENG" -o "translations/"
  
  # 批量提取多个语言目录（按MD5自动合并）
  python loc_tools.py extract-batch -i "GAME_2_MAP/ENG" -i "GAME_2_MAP/GER" -i "GAME_2_MAP/POL" -o "translations/"
  
  # 构建特定语言（使用XML中的别名配置）
  python loc_tools.py build -i "translations/" -l CHN -o "GAME_2_MAP/CN"
  
  # 构建时包含地图数据文件
  python loc_tools.py build -i "translations/" -l CHN --map-data "GAME_2_MAP/ENG" -o "GAME_2_MAP/CN"
  
  # 根据MD5追加其他语言
  python loc_tools.py append -i "translations/" --maps "GAME_2_MAP/GER"
  
  # 添加新语言
  python loc_tools.py lang-add -i "translations/" -l JAP
  
  # 删除语言
  python loc_tools.py lang-remove -i "translations/" -l CHN
  
  # 验证 XML 文件
  python loc_tools.py validate -i "translations/"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    extract_parser = subparsers.add_parser("extract", help="Extract localization content")
    extract_parser.add_argument("-i", "--input", required=True, help="Input path (single map or maps directory)")
    extract_parser.add_argument("-o", "--output", help="Output directory (default: translations/)")
    extract_parser.add_argument("--c2m", action="store_true", help="Input is C2M-unpacked structure: <root>/<CampaignXX>/<mapname>/currentusermap/")
    
    extract_batch_parser = subparsers.add_parser("extract-batch", help="Batch extract from multiple directories")
    extract_batch_parser.add_argument("-i", "--input", required=True, action="append", 
                                      help="Input directory (multiple allowed, e.g., GAME_2_MAP/ENG, GAME_2_MAP/GER)")
    extract_batch_parser.add_argument("-o", "--output", help="Output directory (default: translations/)")
    extract_batch_parser.add_argument("--c2m", action="store_true", help="Input is C2M-unpacked structure: <root>/<CampaignXX>/<mapname>/currentusermap/")
    
    build_parser = subparsers.add_parser("build", help="Build localization files from XML")
    build_parser.add_argument("-i", "--input", required=True, help="Input path (single XML or XML directory)")
    build_parser.add_argument("-l", "--language", required=True, help="Target language code")
    build_parser.add_argument("--map-data", help="Source directory for map data files (map.dat, etc.)")
    build_parser.add_argument("-o", "--output", help="Output directory (default: output/)")
    
    append_parser = subparsers.add_parser("append", help="Append languages to XML files by MD5")
    append_parser.add_argument("-i", "--input", required=True, help="Input path (single XML or XML directory)")
    append_parser.add_argument("--maps", required=True, help="Map directory to append languages from")
    
    lang_add_parser = subparsers.add_parser("lang-add", help="Add a new language to XML files")
    lang_add_parser.add_argument("-i", "--input", required=True, help="Input path (single XML or XML directory)")
    lang_add_parser.add_argument("-l", "--language", required=True, help="New language code (3 characters)")
    lang_add_parser.add_argument("--alias", help="Language alias (default: same as language code)")
    lang_add_parser.add_argument("--encoding", default="windows-1252", help="Output encoding (default: windows-1252)")
    lang_add_parser.add_argument("--fix-1251", action="store_true", help="Apply fix_1251 character conversion")
    lang_add_parser.add_argument("--fix-map-id", action="store_true", help="Fix export_map_id with fix_1251 characters")
    
    lang_remove_parser = subparsers.add_parser("lang-remove", help="Remove a language from XML files")
    lang_remove_parser.add_argument("-i", "--input", required=True, help="Input path (single XML or XML directory)")
    lang_remove_parser.add_argument("-l", "--language", required=True, help="Language code to remove (3 characters)")
    
    validate_parser = subparsers.add_parser("validate", help="Validate XML files")
    validate_parser.add_argument("-i", "--input", required=True, help="Input path (single XML or XML directory)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "extract":
        extract_command(args)
    elif args.command == "extract-batch":
        extract_batch_command(args)
    elif args.command == "build":
        build_command(args)
    elif args.command == "append":
        append_command(args)
    elif args.command == "lang-add":
        lang_add_command(args)
    elif args.command == "lang-remove":
        lang_remove_command(args)
    elif args.command == "validate":
        validate_command(args)


if __name__ == "__main__":
    main()
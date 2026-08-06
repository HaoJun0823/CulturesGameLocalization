# -*- coding: utf-8 -*-
"""
cultures2_converter.py —— Cultures 2（仙宫之门 / SAGA）ini/cif 转换 与 c2m 打包解包工具。

提取自开源项目 Cultures-map-editor（GPL-3.0）：
  https://github.com/Mikulus6/Cultures-map-editor

功能：
  * cif <-> ini 互转（Cultures 2 加密格式，含 cipher 算法）
  * c2m 打包 / 解包（Cultures 2 用户战役单文件归档，与 .lib 同格式）

用法：
  python cultures2_converter.py cif2ini <input.cif> [output.ini]
  python cultures2_converter.py ini2cif <input.ini> [output.cif]
  python cultures2_converter.py c2m-unpack <input.c2m> [output_dir]
  python cultures2_converter.py c2m-pack <input_dir> [output.c2m]

致谢与版权：
  * 本项目为 CulturesNation 社区（https://culturesnation.pl/）的粉丝工具，
    非官方项目，与原版 Cultures 系列无隶属关系。原开发者官网：Funatics（https://www.funatics.de/）。
  * 主要作者：Mikulus（https://github.com/Mikulus6）
  * 贡献者：Basssiiie（Ghidra 反编译游戏引擎）、Peti（文本脚本条目测试与记录）、
    Benedikt Magnus（地形数据解读）、Tyrannica（行走区块可视化）、Proszak（UI 图形）。
  * 格式研究文献：
      - Bacter: "Unknown Encryption In Cultures Game"（XeNTaX 论坛，2010）
      - Siguza: "Cultures 2 file formats"（2013）
      - Watto: "Game Extractor"（2004）
  * 依据 GNU General Public License 3.0 分发（https://www.gnu.org/licenses/gpl-3.0.txt）。
  * Cultures 游戏本体版权归 Funatics Software / THQ 所有。
"""

import argparse
import os
import sys

# ==========================================================================
# 二进制读写工具（提取自 scripts/buffer.py，仅保留本工具所需部分）
# ==========================================================================
DATA_ENCODING = "cp1252"


class BufferGiver:
    """从 bytes 中按需读取数据（小端数字 / 字符串）。"""

    def __init__(self, sequence: bytes):
        self.sequence = bytes(sequence)
        self.offset = 0

    def bytes(self, length: int) -> bytes:
        self.offset += length
        if self.offset > len(self.sequence):
            raise IndexError("Buffer overrun")
        return self.sequence[self.offset - length:self.offset]

    def unsigned(self, length: int) -> int:
        return int.from_bytes(self.bytes(length), byteorder="little")

    def string(self, length: int) -> str:
        return str(self.bytes(length), encoding=DATA_ENCODING)

    def __str__(self) -> str:
        return str(self.sequence[self.offset:], encoding=DATA_ENCODING)


class BufferTaker:
    """向 bytes 中追加数据（小端数字 / 字符串）。"""

    def __init__(self):
        self.sequence = b""

    def bytes(self, item: bytes):
        self.sequence += item

    def unsigned(self, item: int, *, length: int):
        self.bytes(item.to_bytes(byteorder="little", length=length, signed=False))

    def string(self, item: str):
        self.sequence += bytes(item, encoding=DATA_ENCODING)

    def __bytes__(self) -> bytes:
        return self.sequence

    def __len__(self) -> int:
        return len(self.sequence)


# ==========================================================================
# cif <-> ini 转换（提取自 supplements/initialization.py + converters.py）
# ==========================================================================
NEWLINE_REPRESENTATION = "\\r\\n"
NEWLINE_FACTUAL = "\r\n"


def apply_cipher(bytes_obj: bytes, mode: str) -> bytes:
    """Cultures cif 的加/解密变换。mode: 'decode' 或 'encode'。"""
    result = BufferTaker()
    c, d = 71, 126
    for b in bytes_obj:
        if mode == "decode":
            b = (b - 1) ^ c
        elif mode == "encode":
            b = (b ^ c) + 1
        else:
            raise ValueError("mode must be 'decode' or 'encode'")
        c += d
        d += 33
        result.unsigned(b % 256, length=1)
    return bytes(result)


def cif_to_ini(content: bytes) -> str:
    """cif 字节 -> ini 文本（Cultures 2 格式，case 1021）。"""
    buffer = BufferGiver(content)
    magic = buffer.unsigned(length=2)
    if magic == 65:      # cultures 1
        raise ValueError("该 cif 为 Cultures 1 格式，本工具仅支持 Cultures 2（SAGA/仙宫之门）")
    assert magic == 1021, f"未知 cif 魔数: {magic}"

    assert buffer.unsigned(length=6) == 0
    assert buffer.unsigned(length=4) == 1
    entries_num = buffer.unsigned(4)
    assert entries_num == buffer.unsigned(4) == buffer.unsigned(4)
    text_table_size = buffer.unsigned(4)
    assert buffer.unsigned(length=4) == 1001
    assert buffer.unsigned(length=4) == 0
    index_table_encoded = buffer.bytes(buffer.unsigned(4))
    assert buffer.unsigned(length=1) == 1
    assert buffer.unsigned(length=4) == 1001
    assert buffer.unsigned(length=4) == 0
    assert text_table_size == buffer.unsigned(length=4)
    text_table_encoded = buffer.bytes(text_table_size)

    index_table = apply_cipher(index_table_encoded, "decode")
    text_table = apply_cipher(text_table_encoded, "decode")

    index_buf = BufferGiver(index_table)
    decoded = []
    for _ in range(len(index_table) // 4):
        index_value = index_buf.unsigned(4)
        entry = BufferTaker()
        while (ch := text_table[index_value]) != 0:
            entry.unsigned(ch, length=1)
            index_value += 1
        line = str(BufferGiver(bytes(entry)))
        # 首字节标记：1=节标题 [..]，2=普通行
        line_buf = BufferGiver(bytes(entry))
        kind = line_buf.unsigned(length=1)
        if kind == 1:
            line = "[" + str(line_buf) + "]"
        elif kind == 2:
            line = str(line_buf)
        else:
            raise ValueError(f"未知行类型标记: {kind}")
        decoded.append(line.replace(NEWLINE_FACTUAL, NEWLINE_REPRESENTATION))
    return "\n".join(decoded)


def ini_to_cif(content: str) -> bytes:
    """ini 文本 -> cif 字节（Cultures 2 格式）。"""
    text_table = BufferTaker()
    index_table = BufferTaker()

    for line in content.split("\n"):
        line = line.replace(NEWLINE_REPRESENTATION, NEWLINE_FACTUAL)
        index_table.unsigned(len(text_table), length=4)
        if line.startswith("[") and line.endswith("]"):
            text_table.unsigned(1, length=1)
            text_table.string(line[1:-1])
        else:
            text_table.unsigned(2, length=1)
            text_table.string(line)
        text_table.unsigned(0, length=1)

    index_enc = apply_cipher(bytes(index_table), "encode")
    text_enc = apply_cipher(bytes(text_table), "encode")
    entries_num = len(index_enc) // 4

    out = BufferTaker()
    out.unsigned(1021, length=2)
    out.unsigned(0, length=6)
    out.unsigned(1, length=4)
    out.unsigned(entries_num, length=4)
    out.unsigned(entries_num, length=4)
    out.unsigned(entries_num, length=4)
    out.unsigned(len(text_enc), length=4)
    out.unsigned(1001, length=4)
    out.unsigned(0, length=4)
    out.unsigned(len(index_enc), length=4)
    out.bytes(index_enc)
    out.unsigned(1, length=1)
    out.unsigned(1001, length=4)
    out.unsigned(0, length=4)
    out.unsigned(len(text_enc), length=4)
    out.bytes(text_enc)
    return bytes(out)


# ==========================================================================
# c2m 打包 / 解包（提取自 supplements/library.py，Cultures 2 格式）
# ==========================================================================
SEPARATOR = "\\"


class C2MLibrary:
    """Cultures 2 的 c2m / lib 单文件归档。dict: {归档内路径: 内容}"""

    def __init__(self):
        self.files = {}

    # ---- 加载（解包） ----
    def load(self, filename: str):
        with open(filename, "rb") as f:
            bytes_obj = f.read()
        self._extract_cultures_2(bytes_obj)

    def _extract_cultures_2(self, bytes_obj: bytes):
        buffer = BufferGiver(bytes_obj)
        assert buffer.unsigned(4) == 1
        number_of_directories = buffer.unsigned(4)
        number_of_files = buffer.unsigned(4)
        assert buffer.unsigned(4) == 1
        assert buffer.unsigned(4) == 92
        assert buffer.unsigned(1) == 0
        for _ in range(number_of_directories - 1):
            path_length = buffer.unsigned(4)
            filepath = buffer.string(path_length)
            scope = buffer.unsigned(4)
            assert filepath.count(SEPARATOR) == scope
        for _ in range(number_of_files):
            path_length = buffer.unsigned(4)
            filepath = buffer.string(path_length)
            offset = buffer.unsigned(4)
            size = buffer.unsigned(4)
            self.files[filepath] = bytes_obj[offset:][:size]

    # ---- 保存（打包） ----
    def save(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self._pack_cultures_2())

    def _pack_cultures_2(self) -> bytes:
        head = BufferTaker()
        body = BufferTaker()

        directories = set()
        for filepath in self.files:
            current = os.path.dirname(filepath)
            while len(current) > 0:
                directories.add(current.replace(os.sep, SEPARATOR) + SEPARATOR)
                current = os.path.dirname(current)
        directories = sorted(directories, key=lambda p: p.count(SEPARATOR))

        header_length = (sum(map(len, list(self.files) + directories))
                         + len(directories) * 8 + len(self.files) * 12 + 21)

        head.unsigned(1, length=4)
        head.unsigned(len(directories) + 1, length=4)
        head.unsigned(len(self.files), length=4)
        head.unsigned(1, length=4)
        head.unsigned(92, length=4)
        head.unsigned(0, length=1)

        for dir_name in directories:
            head.unsigned(len(dir_name), length=4)
            head.string(dir_name)
            head.unsigned(dir_name.count(SEPARATOR), length=4)

        for filepath, content in self.files.items():
            head.unsigned(len(filepath), length=4)
            head.string(filepath)
            head.unsigned(header_length + len(body), length=4)
            head.unsigned(len(content), length=4)
            body.bytes(content)

        return bytes(head) + bytes(body)

    # ---- 目录 <-> 归档 ----
    def pack_directory(self, directory: str):
        """把目录（含子目录）打包进归档。

        根识别规则：若输入目录下存在 currentusermap/（Cultures 2 用户战役
        解包态标准结构），则以该目录的父级为归档根，包内路径保留
        currentusermap\\ 前缀（与官方 c2m 一致，如 currentusermap\\map.cif）；
        否则以输入目录自身为根。
        """
        cu = os.path.join(directory, "currentusermap")
        base = os.path.abspath(os.path.join(cu, os.pardir)) if os.path.isdir(cu) else os.path.abspath(directory)
        walk_root = cu if os.path.isdir(cu) else directory
        for r, _, files in os.walk(walk_root):
            for name in files:
                filepath = os.path.join(r, name)
                with open(filepath, "rb") as f:
                    rel = os.path.abspath(filepath)[len(base) + 1:].replace(os.sep, SEPARATOR)
                    self.files[rel] = f.read()

    def extract_directory(self, directory: str):
        """把归档内容解包到目录。"""
        for filepath, content in self.files.items():
            target = os.path.join(directory, filepath)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(content)


# ==========================================================================
# CLI
# ==========================================================================
def _ensure_suffix(path: str, suffix: str) -> str:
    return path if path.lower().endswith(suffix) else path + suffix


def cmd_cif2ini(args):
    out = args.output or _ensure_suffix(os.path.splitext(args.input)[0], ".ini")
    with open(args.input, "rb") as f:
        content = f.read()
    text = cif_to_ini(content)
    with open(out, "w", encoding=DATA_ENCODING, newline="") as f:
        f.write(text)
    print(f"[OK] {args.input} -> {out}")


def cmd_ini2cif(args):
    out = args.output or _ensure_suffix(os.path.splitext(args.input)[0], ".cif")
    with open(args.input, "r", encoding=DATA_ENCODING) as f:
        text = f.read()
    data = ini_to_cif(text)
    with open(out, "wb") as f:
        f.write(data)
    print(f"[OK] {args.input} -> {out}")


def cmd_c2m_unpack(args):
    out = args.output or os.path.splitext(args.input)[0]
    lib = C2MLibrary()
    lib.load(args.input)
    lib.extract_directory(out)
    print(f"[OK] 解包 {len(lib.files)} 个文件 -> {out}")


def cmd_c2m_pack(args):
    out = args.output or _ensure_suffix(args.input, ".c2m")
    lib = C2MLibrary()
    lib.pack_directory(args.input)
    lib.save(out)
    print(f"[OK] 打包 {len(lib.files)} 个文件 -> {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Cultures 2 ini/cif 转换 与 c2m 打包解包（提取自 Cultures-map-editor，GPL-3.0）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("cif2ini", help="cif -> ini")
    p.add_argument("input"); p.add_argument("output", nargs="?"); p.set_defaults(func=cmd_cif2ini)

    p = sub.add_parser("ini2cif", help="ini -> cif")
    p.add_argument("input"); p.add_argument("output", nargs="?"); p.set_defaults(func=cmd_ini2cif)

    p = sub.add_parser("c2m-unpack", help="解包 c2m 到目录")
    p.add_argument("input"); p.add_argument("output", nargs="?"); p.set_defaults(func=cmd_c2m_unpack)

    p = sub.add_parser("c2m-pack", help="从目录打包 c2m")
    p.add_argument("input"); p.add_argument("output", nargs="?"); p.set_defaults(func=cmd_c2m_pack)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

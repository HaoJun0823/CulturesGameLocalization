import itertools
import logging
from pathlib import Path

# 配置日志输出格式
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# ----------------------------------------------------------------------
# 核心解码逻辑（基于 Cultures 游戏 CIF 格式）
# ----------------------------------------------------------------------

def cultures_cif_block_encoder_decoder(mode: str, buffer: bytes) -> bytes:
    buf = list(buffer)
    c = 71
    d = 126
    buffer_size = len(buf)

    for i in range(buffer_size):
        b = buf[i]
        if mode == 'decode':  # cif -> ini
            b = b - 1
            b = b ^ c
        elif mode == 'encode':  # ini -> cif
            b = b ^ c
            b = b + 1
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        c = c + d
        d = d + 33
        buf[i] = b % 256

    return bytes(buf)


def bytes_buffer(bytes_obj: bytes):
    for byte in bytes_obj:
        yield byte


def nexts(iterable, var: int) -> bytes:
    return bytes(list(itertools.islice(iterable, var)))


def bytes_to_integers(bytes_obj: bytes) -> list:
    bytes_list = [bytes_obj[4 * i : 4 * i + 4] for i in range(len(bytes_obj) // 4)]
    return [int.from_bytes(bytes(el), byteorder="little") for el in bytes_list]


def read_texttable(bytes_decoded_indextable: bytes, bytes_decoded_texttable: bytes) -> list:
    decoded_indextable = bytes_to_integers(bytes_decoded_indextable)
    decoded_texttable = []

    for index_value in decoded_indextable:
        decoded_texttable.append(b'')
        i = index_value
        while i < len(bytes_decoded_texttable) and bytes_decoded_texttable[i] != 0:
            decoded_texttable[-1] += int.to_bytes(bytes_decoded_texttable[i], byteorder="little", length=1)
            i += 1

    return decoded_texttable


def from_cif_header_cultures1(buffer):
    bytes_unknown0 = nexts(buffer, 2)
    bytes_number_of_entries_1 = nexts(buffer, 4)
    bytes_number_of_entries_2 = nexts(buffer, 4)
    bytes_unknown1 = nexts(buffer, 4)
    bytes_size_of_index_table = nexts(buffer, 4)

    size_of_index_table = int.from_bytes(bytes_size_of_index_table, byteorder="little")
    number_of_entries_1 = int.from_bytes(bytes_number_of_entries_1, byteorder="little")
    number_of_entries_2 = int.from_bytes(bytes_number_of_entries_2, byteorder="little")

    assert number_of_entries_1 == number_of_entries_2 == size_of_index_table / 4

    bytes_encoded_indextable = nexts(buffer, size_of_index_table)
    bytes_unknown2 = nexts(buffer, 2)
    bytes_unknown3 = nexts(buffer, 4)

    assert bytes_unknown0 == bytes_unknown2 == b'\x01\x00'
    assert bytes_unknown1 == bytes_unknown3 == b'\x0a\x00\x00\x00'

    bytes_size_of_text_table = nexts(buffer, 4)
    size_of_text_table = int.from_bytes(bytes_size_of_text_table, byteorder="little")
    bytes_encoded_texttable = nexts(buffer, size_of_text_table)

    return bytes_encoded_indextable, bytes_encoded_texttable


def from_cif_header_cultures2(buffer):
    bytes_unknown0 = nexts(buffer, 6)
    bytes_unknown1 = nexts(buffer, 4)
    bytes_number_of_entries_1 = nexts(buffer, 4)
    bytes_number_of_entries_2 = nexts(buffer, 4)
    bytes_number_of_entries_3 = nexts(buffer, 4)
    bytes_size_of_text_table_1 = nexts(buffer, 4)

    bytes_unknown2 = nexts(buffer, 4)
    bytes_unknown3 = nexts(buffer, 4)
    bytes_size_of_index_table = nexts(buffer, 4)

    size_of_index_table = int.from_bytes(bytes_size_of_index_table, byteorder="little")
    bytes_encoded_indextable = nexts(buffer, size_of_index_table)

    bytes_unknown4 = nexts(buffer, 1)
    bytes_unknown5 = nexts(buffer, 4)
    bytes_unknown6 = nexts(buffer, 4)
    bytes_size_of_text_table_2 = nexts(buffer, 4)

    size_of_text_table_1 = int.from_bytes(bytes_size_of_text_table_1, byteorder="little")
    size_of_text_table_2 = int.from_bytes(bytes_size_of_text_table_2, byteorder="little")

    number_of_entries_1 = int.from_bytes(bytes_number_of_entries_1, byteorder="little")
    number_of_entries_2 = int.from_bytes(bytes_number_of_entries_2, byteorder="little")
    number_of_entries_3 = int.from_bytes(bytes_number_of_entries_3, byteorder="little")

    assert number_of_entries_1 == number_of_entries_2 == number_of_entries_3 == size_of_index_table / 4
    assert size_of_text_table_1 == size_of_text_table_2

    assert bytes_unknown0 == b'\x00\x00\x00\x00\x00\x00'
    assert bytes_unknown1 == b'\x01\x00\x00\x00'
    assert bytes_unknown2 == bytes_unknown5 == b'\xe9\x03\x00\x00'
    assert bytes_unknown3 == bytes_unknown6 == b'\x00\x00\x00\x00'
    assert bytes_unknown4 == b'\x01'

    bytes_encoded_texttable = nexts(buffer, size_of_text_table_1)
    return bytes_encoded_indextable, bytes_encoded_texttable


def cif2ini_content(bytes_obj: bytes, tab_file: bool = False) -> bytes:
    buffer = bytes_buffer(bytes_obj)
    bytes_file_id = nexts(buffer, 2)

    if bytes_file_id == b'\x41\x00':  # Cultures 1
        bytes_encoded_indextable, bytes_encoded_texttable = from_cif_header_cultures1(buffer)
    elif bytes_file_id == b'\xfd\x03':  # Cultures 2
        bytes_encoded_indextable, bytes_encoded_texttable = from_cif_header_cultures2(buffer)
    else:
        raise ValueError(f"Unknown CIF magic header: {bytes_file_id.hex()}")

    bytes_decoded_indextable = cultures_cif_block_encoder_decoder("decode", bytes_encoded_indextable)
    bytes_decoded_texttable = cultures_cif_block_encoder_decoder("decode", bytes_encoded_texttable)

    decoded_texttable = read_texttable(bytes_decoded_indextable, bytes_decoded_texttable)

    decoded_lines = []
    for line in decoded_texttable:
        line = line.replace(b"\n", b"\\n")
        try:
            first_byte = line[0]
            if first_byte == 1:
                line = b"[" + line[1:] + b"]"
            elif first_byte == 2:
                line = line[1:]
            else:
                raise ValueError("Invalid line flag byte")
        except (ValueError, IndexError):
            if not tab_file:
                raise ValueError("Failed to parse section/key structure in CIF text line.")

        decoded_lines.append(line)

    return b"\n".join(decoded_lines)


# ----------------------------------------------------------------------
# 批量处理逻辑
# ----------------------------------------------------------------------

def batch_convert_cif_to_ini(target_dir: str = "."):
    root_path = Path(target_dir).resolve()
    logging.info(f"开始扫描目录: {root_path}")

    # ** Search recursive *.cif files
    cif_files = list(root_path.rglob("*.cif"))
    
    if not cif_files:
        logging.info("未找到任何 .cif 文件。")
        return

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for cif_path in cif_files:
        ini_path = cif_path.with_suffix(".ini")

        # 检查 INI 是否已存在
        if ini_path.exists():
            logging.warning(f"[SKIPPED] 已存在 INI 文件，跳过转换: {ini_path}")
            skipped_count += 1
            continue

        try:
            bytes_obj = cif_path.read_bytes()
            ini_bytes = cif2ini_content(bytes_obj)
            
            ini_path.write_bytes(ini_bytes)
            logging.info(f"[SUCCESS] 成功转换: {cif_path.relative_to(root_path)} -> {ini_path.name}")
            success_count += 1

        except Exception as e:
            logging.error(f"[FAILED] 转换失败 {cif_path.relative_to(root_path)}: {e}")
            failed_count += 1

    logging.info(f"\n--- 转换完成统计 ---")
    logging.info(f"成功: {success_count} | 跳过: {skipped_count} | 失败: {failed_count}")


if __name__ == "__main__":
    batch_convert_cif_to_ini()
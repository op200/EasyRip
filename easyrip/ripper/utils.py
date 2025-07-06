import codecs
from pathlib import Path
import string
import time

from ..easyrip_log import log


BASE62 = string.digits + string.ascii_letters


def int_to_base62(num: int) -> str:
    if num == 0:
        return "0"
    s = []
    while num > 0:
        num, rem = divmod(num, 62)
        s.append(BASE62[rem])
    return "".join(reversed(s))


def get_base62_time() -> str:
    return int_to_base62(time.time_ns())


def read_text(path: Path) -> str:
    data = path.read_bytes()

    if data.startswith(codecs.BOM_UTF8):
        return data.decode("utf-8-sig")
    elif data.startswith(codecs.BOM_UTF16_LE):
        return data.decode("utf-16-le")
    elif data.startswith(codecs.BOM_UTF16_BE):
        return data.decode("utf-16-be")
    elif data.startswith(codecs.BOM_UTF32_LE):
        return data.decode("utf-32-le")
    elif data.startswith(codecs.BOM_UTF32_BE):
        return data.decode("utf-32-be")
    else:
        log.warning("Can not find the BOM from {}. Defaulting to UTF-8", path)
        return data.decode("utf-8")


def uuencode_ssa(data: bytes) -> str:
    encoded = []
    line = []
    line_count = 0

    def append_chars(chars):
        nonlocal line, line_count
        for c in chars:
            line.append(c)
            line_count += 1
            if line_count == 80:
                encoded.append("".join(line))
                line = []
                line_count = 0

    i = 0
    n = len(data)

    # 处理完整的3字节组
    while i + 2 < n:
        b0, b1, b2 = data[i], data[i + 1], data[i + 2]
        # 将24位分为4个6位的组
        group0 = b0 >> 2
        group1 = ((b0 & 0x03) << 4) | (b1 >> 4)
        group2 = ((b1 & 0x0F) << 2) | (b2 >> 6)
        group3 = b2 & 0x3F

        # 每6位组加上33后转ASCII字符
        chars = [chr(group0 + 33), chr(group1 + 33), chr(group2 + 33), chr(group3 + 33)]
        append_chars(chars)
        i += 3

    # 处理尾部剩余字节
    if i < n:
        remaining = n - i
        if remaining == 1:  # 剩余1个字节
            b = data[i]
            # 左移4位得12位数据
            value = b * 0x100
            group0 = (value >> 6) & 0x3F
            group1 = value & 0x3F
            chars = [chr(group0 + 33), chr(group1 + 33)]
            append_chars(chars)
        else:  # 剩余2个字节
            b0, b1 = data[i], data[i + 1]
            # 左移2位得18位数据（实际效果是组合后左移2位）
            value = (b0 << 10) | (b1 << 2)
            group0 = (value >> 12) & 0x3F
            group1 = (value >> 6) & 0x3F
            group2 = value & 0x3F
            chars = [chr(group0 + 33), chr(group1 + 33), chr(group2 + 33)]
            append_chars(chars)

    # 添加最后一行
    if line:
        encoded.append("".join(line))

    return "\n".join(encoded)


def uudecode_ssa(s: str) -> bytes:
    # 合并所有行并移除可能的空行
    chars = []
    for line in s.splitlines():
        if line:  # 跳过空行
            chars.extend(line)

    decoded = bytearray()
    i = 0
    n = len(chars)

    # 处理完整4字符组
    while i + 3 < n:
        groups = [
            ord(chars[i]) - 33,
            ord(chars[i + 1]) - 33,
            ord(chars[i + 2]) - 33,
            ord(chars[i + 3]) - 33,
        ]
        # 4个6位组还原为3字节
        b0 = (groups[0] << 2) | (groups[1] >> 4)
        b1 = ((groups[1] & 0x0F) << 4) | (groups[2] >> 2)
        b2 = ((groups[2] & 0x03) << 6) | groups[3]
        decoded.extend([b0, b1, b2])
        i += 4

    # 处理尾部剩余字符
    remaining = n - i
    if remaining == 2:  # 对应1字节原始数据
        groups = [ord(chars[i]) - 33, ord(chars[i + 1]) - 33]
        # 2个6位组还原为1字节（取group1高4位忽略）
        b0 = (groups[0] << 2) | (groups[1] >> 4)
        decoded.append(b0)
    elif remaining == 3:  # 对应2字节原始数据
        groups = [ord(chars[i]) - 33, ord(chars[i + 1]) - 33, ord(chars[i + 2]) - 33]
        # 3个6位组还原为2字节
        b0 = (groups[0] << 2) | (groups[1] >> 4)
        b1 = ((groups[1] & 0x0F) << 4) | (groups[2] >> 2)
        decoded.extend([b0, b1])

    return bytes(decoded)

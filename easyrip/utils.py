import codecs
import ctypes
import os
import re
import string
import sys
import time
from itertools import zip_longest
from pathlib import Path
from typing import Any, Final, TypeGuard, get_args, get_origin

from Crypto.Cipher import AES as CryptoAES
from Crypto.Util.Padding import pad, unpad

BASE62 = string.digits + string.ascii_letters


class AES:
    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> bytes:
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC)  # 使用 CBC 模式
        ciphertext = cipher.encrypt(pad(plaintext, CryptoAES.block_size))  # 加密并填充
        return bytes(cipher.iv) + ciphertext  # 返回 IV 和密文

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes) -> bytes:
        iv = ciphertext[:16]  # 提取 IV
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC, iv=iv)
        return unpad(
            cipher.decrypt(ciphertext[16:]), CryptoAES.block_size
        )  # 解密并去除填充


def change_title(title: str) -> None:
    if os.name == "nt":
        # os.system(f"title {title}")
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    elif os.name == "posix":
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


def check_ver(new_ver_str: str, old_ver_str: str) -> bool:
    new_ver = list(re.sub(r"^\D*(\d.*\d)\D*$", r"\1", new_ver_str).split("."))
    new_ver_add_num = list(str(new_ver[-1]).split("+"))
    new_ver = (
        [int(v) for v in (*new_ver[:-1], new_ver_add_num[0])],
        [int(v) for v in new_ver_add_num[1:]],
    )

    old_ver = list(re.sub(r"^\D*(\d.*\d)\D*$", r"\1", old_ver_str).split("."))
    old_ver_add_num = list(str(old_ver[-1]).split("+"))
    old_ver = (
        [int(v) for v in (*old_ver[:-1], old_ver_add_num[0])],
        [int(v) for v in old_ver_add_num[1:]],
    )

    for i in range(2):
        for new, old in zip_longest(new_ver[i], old_ver[i], fillvalue=0):
            if new > old:
                return True
            if new < old:
                break
        else:
            continue
        break
    return False


def int_to_base62(num: int) -> str:
    if num == 0:
        return "0"
    s: list[str] = []
    while num > 0:
        num, rem = divmod(num, 62)
        s.append(BASE62[rem])
    return "".join(reversed(s))


def get_base62_time() -> str:
    return int_to_base62(time.time_ns())


def read_text(path: Path) -> str:
    from .easyrip_log import log

    data = path.read_bytes()

    if data.startswith(codecs.BOM_UTF8):
        return data.decode("utf-8-sig")
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        return data.decode("utf-32")

    log.warning("Can not find the BOM from {}. Defaulting to UTF-8", path)
    return data.decode("utf-8")


def uuencode_ssa(data: bytes) -> str:
    encoded: list[str] = []
    line: list[str] = []
    line_count: int = 0

    def append_chars(chars: list[str]) -> None:
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
    chars: list[str] = []
    for line in s.splitlines():
        if line:  # 跳过空行
            chars.extend(line)

    decoded: Final[bytearray] = bytearray()
    i: int = 0
    n: int = len(chars)

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


def time_str_to_sec(s: str) -> float:
    return sum(float(t) * 60**i for i, t in enumerate(s.split(":")[::-1]))


def non_ascii_str_len(s: str) -> int:
    """非 ASCII 字符算作 2 宽度"""
    return sum(2 - int(ord(c) < 256) for c in s)


def type_match[T](val: Any, t: type[T]) -> TypeGuard[T]:
    """
    检查值是否匹配给定的类型（支持泛型）

    支持的类型包括：
    - 基本类型: int, str, list, dict, tuple, set
    - 泛型类型: list[str], dict[str, int], tuple[int, ...]
    - 联合类型: int | str, Union[int, str]
    - 可选类型: Optional[str]
    - 嵌套泛型: list[list[str]], dict[str, list[int]]

    Args:
        val: 要检查的值
        t: 目标类型，可以是普通类型或泛型

    Returns:
        bool: 值是否匹配目标类型

    """
    t_org = get_origin(t)

    # 如果不是泛型类型，直接使用 isinstance
    if t_org is None:
        return isinstance(val, t)

    # 首先检查是否是 b_org 的实例
    if not isinstance(val, t_org):
        return False

    # 获取类型参数
    args = get_args(t)
    if not args:  # 没有类型参数，如 List
        return True

    # 根据不同的原始类型进行检查
    if t_org is list:
        # list[T] 检查
        if len(args) == 1:
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)

    elif t_org is tuple:
        # tuple[T1, T2, ...] 或 tuple[T, ...] 检查
        if len(args) == 2 and args[1] is ...:  # 可变长度元组
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)
        # 固定长度元组
        if len(val) != len(args):
            return False
        return all(type_match(item, t) for item, t in zip(val, args, strict=False))

    elif t_org is dict:
        # dict[K, V] 检查
        if len(args) == 2:
            key_type, value_type = args
            return all(
                type_match(k, key_type) and type_match(v, value_type)
                for k, v in val.items()
            )

    elif t_org is set:
        # set[T] 检查
        if len(args) == 1:
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)

    elif t_org is frozenset:
        # frozenset[T] 检查
        if len(args) == 1:
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)

    elif hasattr(t_org, "__name__") and t_org.__name__ == "Union":
        # Union[T1, T2, ...] 或 T1 | T2 检查
        return any(type_match(val, t) for t in args)

    return True

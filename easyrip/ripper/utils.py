import codecs
from pathlib import Path
import string
import time

from ..easyrip_log import log

UTF8_BOM = b"\xef\xbb\xbf"

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

import codecs
import ctypes
import enum
import os
import re
import shlex
import shutil
import string
import sys
import time
import types
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Collection,
    Container,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Sized,
)
from collections.abc import (
    Set as AbstractSet,
)
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Final,
    Literal,
    LiteralString,
    Never,
    NoReturn,
    NotRequired,
    Required,
    TypeAliasType,
    TypeGuard,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

import Crypto.Cipher.AES
import Crypto.Util.Padding

from .global_val import PROJECT_TITLE

if TYPE_CHECKING:
    from pathlib import Path

BASE62 = string.digits + string.ascii_letters


class AES:
    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> bytes:
        cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC)  # 使用 CBC 模式
        ciphertext = cipher.encrypt(
            Crypto.Util.Padding.pad(plaintext, Crypto.Cipher.AES.block_size)
        )  # 加密并填充
        return bytes(cipher.iv) + ciphertext  # 返回 IV 和密文

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes) -> bytes:
        iv = ciphertext[:16]  # 提取 IV
        cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv=iv)
        return Crypto.Util.Padding.unpad(
            cipher.decrypt(ciphertext[16:]), Crypto.Cipher.AES.block_size
        )  # 解密并去除填充


class terminal_progress:
    ESC = "\x1b"

    class State(enum.Enum):
        clear = 0
        normal = 1
        error = 2
        indeterminate = 3
        warning = 4

    @classmethod
    def update(cls, state: State, persent: int = 0, /):
        """:param persent: [0, 100]"""
        sys.stdout.write(f"{cls.ESC}]9;4;{state.value};{persent}{cls.ESC}\\")
        sys.stdout.flush()

    @classmethod
    def clear(cls):
        cls.update(cls.State.clear)

    @classmethod
    def indeterminate(cls):
        cls.update(cls.State.indeterminate)

    @classmethod
    def set(cls, persent: int, /):
        cls.update(cls.State.normal, max(1, persent))

    @classmethod
    def error(cls, persent: int = 0, /):
        cls.update(cls.State.error, persent)

    @classmethod
    def warning(cls, persent: int = 0, /):
        cls.update(cls.State.warning, persent)


class Title:
    @staticmethod
    def change_title(title: str) -> None:
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        elif os.name == "posix":
            sys.stdout.write(f"\x1b]2;{title}\x07")
            sys.stdout.flush()

    type Log_num = tuple[int, int]
    """(warn, err)"""

    def __init__(self, project_title: str | None = None, /) -> None:
        self.project_title: str | None = project_title
        self._temp_status: str | None = None
        self._progress: str | None = None
        self._log_num_base: Title.Log_num = (0, 0)
        self._log_num: Title.Log_num = (0, 0)

    @property
    def temp_status(self):
        return self._temp_status

    @temp_status.setter
    def temp_status(self, value: str | None) -> None:
        if self._temp_status != value:
            self._temp_status = value
            self.refresh_title()

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value: str | None) -> None:
        if self._progress != value:
            self._progress = value
            self.refresh_title()

    @property
    def log_num_base(self):
        return self._log_num_base

    @log_num_base.setter
    def log_num_base(self, value: Log_num) -> None:
        if self._log_num_base != value:
            self._log_num_base = value
            self.refresh_title()

    @property
    def log_num(self):
        return self._log_num

    @log_num.setter
    def log_num(self, value: Log_num) -> None:
        if self._log_num != value:
            self._log_num = value
            self.refresh_title()

    def refresh_title(self):
        from .easyrip_log import log

        res_log = ""
        if n := log.warning_num - self.log_num_base[0]:
            res_log += f"{n}W"
        if n := log.error_num - self.log_num_base[1]:
            res_log += f"{n}E"

        self.change_title(
            " - ".join(
                s
                for s in (self.temp_status, self.progress, res_log, PROJECT_TITLE)
                if s
            )
        )


title = Title()
"""本项目用的单例"""


def shlex_split(command: str) -> list[str]:
    return shlex.split(command.replace("\\", "\\\\") if os.name == "nt" else command)


def check_ver(new_ver_str: str, old_ver_str: str) -> bool:
    """
    Compare software versions. (AI)

    Supported:
        1.2.3
        v1.2.3
        version 1.2.3
        1.2.3-alpha
        1.2.3-alpha.1
        1.2.3-rc1
        1.2.3+build.1

    Return:
        True if new_ver_str > old_ver_str

    """

    def parse(ver: str) -> tuple[tuple[int, ...], tuple[int | str, ...] | None]:
        match = re.fullmatch(
            r"(?ix)"
            r"\s*(?:version|ver|v)?\s*"
            r"(\d+(?:\.\d+)*)"
            r"(?:-([0-9a-z.-]+))?"
            r"(?:\+[0-9a-z.-]+)?"
            r"\s*",
            ver,
        )

        if match is None:
            raise ValueError(f"Invalid version: {ver}")

        core = tuple(int(x) for x in match.group(1).split("."))

        # 1.2 == 1.2.0
        core += (0,) * (3 - len(core))

        pre = match.group(2)

        if pre is None:
            return core, None

        return (
            core,
            tuple(int(x) if x.isdigit() else x for x in pre.split(".")),
        )

    new_core, new_pre = parse(new_ver_str)
    old_core, old_pre = parse(old_ver_str)

    # 主版本比较
    if new_core != old_core:
        return new_core > old_core

    # 正式版 > 预发布版
    if new_pre is None:
        return old_pre is not None

    if old_pre is None:
        return False

    for new, old in zip(new_pre, old_pre, strict=True):
        if new == old:
            continue

        # int 和 str 混合时，SemVer 规定数字标识符优先级低
        if isinstance(new, int) and isinstance(old, str):
            return False

        if isinstance(new, str) and isinstance(old, int):
            return True

        if isinstance(new, int) and isinstance(old, int):
            return new > old

        if isinstance(new, str) and isinstance(old, str):
            return new > old

        raise AssertionError("unreachable")

    # 前缀相同，长度更长优先
    return len(new_pre) > len(old_pre)


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


def read_text(path: "Path") -> str:
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


@overload
def type_match[T](val: Any, t: type[T] | TypeAliasType) -> TypeGuard[T]: ...
@overload
def type_match(val: Any, t: object) -> bool: ...
def type_match(val: Any, t: object) -> bool:
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
    # Any 表示不限制值的类型，不能直接传给 isinstance。
    if t is Any:
        return True

    # None 可以作为 typing.Optional 的参数，也允许直接传入。
    if t is None:
        return val is None

    # Never/NoReturn 没有合法的值。
    if t is Never or t is NoReturn:
        return False

    # LiteralString 在运行时只能可靠地检查为 str。
    if t is LiteralString:
        return isinstance(val, str)

    # TypeVar：无约束时等价于 Any；有约束时满足任意约束即可；有上界时
    # 必须满足上界。TypeVar 的具体绑定值在运行时不可得。
    if type(t).__name__ == "TypeVar" and hasattr(t, "__constraints__"):
        constraints = getattr(t, "__constraints__", ())
        if constraints:
            return any(type_match(val, constraint) for constraint in constraints)
        bound = getattr(t, "__bound__", None)
        return True if bound is None else type_match(val, bound)

    # NewType 的运行时对象带有 __supertype__，其值本身仍是基础类型。
    supertype = getattr(t, "__supertype__", None)
    if supertype is not None:
        return type_match(val, supertype)

    # TypeAliasType 的实际目标类型保存在 __value__ 中；别名本身不能
    # 直接传给 isinstance，应先递归检查其目标类型。
    if isinstance(t, TypeAliasType):
        return type_match(val, t.__value__)

    # TypedDict 在运行时是普通 dict 的伪类型，使用其字段定义进行检查。
    if isinstance(t, type) and hasattr(t, "__required_keys__"):
        if not isinstance(val, dict):
            return False

        typed_dict = cast("type[Any]", t)
        try:
            annotations = get_type_hints(typed_dict, include_extras=True)
        except (NameError, TypeError):
            annotations = getattr(typed_dict, "__annotations__", {})

        required_keys = getattr(typed_dict, "__required_keys__", frozenset())
        if not required_keys.issubset(val):
            return False

        return all(
            key not in val or type_match(val[key], value_type)
            for key, value_type in annotations.items()
        )

    t_org = get_origin(t)

    # 联合类型必须在 isinstance 之前处理；PEP 604 和 typing.Union 的
    # origin 不同，且两者都不能直接作为 isinstance 的第二个参数。
    from typing import Union

    if t_org in (types.UnionType, Union):
        return any(type_match(val, arg) for arg in get_args(t))

    # Literal 比较值而不是比较类型。额外检查类型以区分 True 和 1。
    if t_org is Literal:
        return any(
            type(val) is type(literal) and val == literal for literal in get_args(t)
        )

    # Annotated、Final、ClassVar、Required、NotRequired 的运行时检查都
    # 应检查其第一个实际类型参数，后续参数只是元数据或限定信息。
    if t_org in (Annotated, Final, ClassVar, Required, NotRequired):
        args = get_args(t)
        return not args or type_match(val, args[0])

    # 如果不是泛型类型，直接使用 isinstance
    if t_org is None:
        if isinstance(t, str):
            # 未解析的前向引用缺少命名空间，无法可靠地运行时解析。
            return False
        try:
            return isinstance(val, cast("type[Any]", t))
        except TypeError:
            return False

    args = get_args(t)

    # type[T] / typing.Type[T] 检查传入值是否为 T 的子类。
    if t_org is type:
        if not isinstance(val, type):
            return False
        if not args or args[0] is Any:
            return True
        try:
            return issubclass(val, cast("type[Any]", args[0]))
        except TypeError:
            return type_match(val, args[0])

    # Callable 的参数和返回值签名无法通过 isinstance 完整验证；这里
    # 检查其可调用性，Callable[..., T] 也遵循相同规则。
    if t_org is Callable:
        return callable(val)

    # re.Pattern[T] / re.Match[T] 的参数表示 str 或 bytes。
    if t_org is re.Pattern:
        return isinstance(val, re.Pattern) and (
            not args or type_match(val.pattern, args[0])
        )
    if t_org is re.Match:
        return isinstance(val, re.Match) and (
            not args or type_match(val.string, args[0])
        )

    try:
        is_instance = isinstance(val, t_org)
    except TypeError:
        return False
    if not is_instance:
        return False

    if not args:  # 没有类型参数，如 list、List
        return True

    if t_org is list:
        if len(args) == 1:
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)

    elif t_org is tuple:
        # tuple[()] 表示空元组；它的 get_args() 在不同版本中可能为空。
        if len(args) == 1 and args[0] == ():
            return not val
        if len(args) == 2 and args[1] is ...:  # 可变长度元组
            elem_type = args[0]
            return all(type_match(item, elem_type) for item in val)
        if len(val) != len(args):
            return False
        return all(type_match(item, t) for item, t in zip(val, args, strict=False))

    elif isinstance(t_org, type) and issubclass(t_org, Mapping):
        # dict[K, V]、defaultdict[K, V]、Counter[K] 等映射类型检查。
        if len(args) == 2:
            key_type, value_type = args
            return all(
                type_match(k, key_type) and type_match(v, value_type)
                for k, v in val.items()
            )

    elif t_org in (set, frozenset):
        if len(args) == 1:
            return all(type_match(item, args[0]) for item in val)

    elif t_org in (Mapping, MutableMapping):
        if len(args) == 2:
            key_type, value_type = args
            return all(
                type_match(key, key_type) and type_match(value, value_type)
                for key, value in val.items()
            )

    elif isinstance(t_org, type) and issubclass(
        t_org,
        (
            Sequence,
            MutableSequence,
            Collection,
            Iterable,
            Container,
            AbstractSet,
            MutableSet,
        ),
    ):
        if len(args) == 1:
            return all(type_match(item, args[0]) for item in val)

    elif t_org in (Iterator, AsyncIterable, AsyncIterator):
        # 迭代器是一次性对象，遍历它会改变程序状态；这里只能可靠
        # 检查其外层类型，不能为了类型检查消耗它。
        return True

    elif t_org is Sized:
        return True

    # 对自定义泛型类，运行时通常无法从实例恢复类型参数；但 origin 的
    # 实例检查已经完成，因此将其视为外层类型匹配。
    return True


def obj_fmt(
    obj: object,
    /,
    indent: int = 2,
    width: int | None = None,
    *,
    default_color: int = 0,
    bracket_color: int = 32,
    str_color: int = 33,
    obj_color: int = 36,
    _layer: int = 0,
    _llen: int = 0,
) -> str:
    """
    部分情况下替代 pformat

    - str 不换行
    - dict 绝对换行
    - list 等视长度换行
    - 优先使用 str 而不是 repr
    """
    width = shutil.get_terminal_size().columns if width is None else width

    _obj_fmt = partial(
        obj_fmt,
        indent=indent,
        width=width,
        default_color=default_color,
        bracket_color=bracket_color,
        str_color=str_color,
        obj_color=obj_color,
    )

    def_cs = f"\x1b[{default_color}m"
    bracket_cs = f"\x1b[{bracket_color}m"

    if isinstance(obj, str | bytes):
        return f"\x1b[{str_color}m{obj!r}{def_cs}"

    if is_dataclass(obj) and not isinstance(obj, type):
        obj = asdict(obj)

    if isinstance(obj, Mapping):
        indent_str = " " * indent * (_layer + 1)
        if not obj:
            return f"{bracket_cs}{obj}{def_cs}"
        return "\n".join(
            (
                f"{bracket_cs}{{{def_cs}",
                *(
                    (
                        indent_str
                        + (
                            _k_str := _obj_fmt(
                                k,
                                _layer=_layer + 1,
                                _llen=len(indent_str),
                            )
                        )
                        + ": "
                        + _obj_fmt(
                            v,
                            _layer=_layer + 1,
                            _llen=len(indent_str) + len(_k_str.rsplit("\n", 1)) + 2,
                        )
                        + ","
                    )
                    for k, v in obj.items()
                ),
                " " * indent * _layer + f"{bracket_cs}}}{def_cs}",
            )
        )

    if isinstance(obj, Iterable):
        obj_str = str(obj)
        match obj:
            case tuple():
                bracket = "()"
            case set() | frozenset():
                bracket = "{}"
            case list():
                bracket = "[]"
            case _:
                return f"\x1b[{obj_color}m{obj!r}{def_cs}"
        if len(obj_str) + _llen > width:
            obj_str = "\n".join(
                (
                    bracket_cs + bracket[0] + def_cs,
                    *(
                        (
                            " " * indent * (_layer + 1)
                            + _obj_fmt(
                                v,
                                _layer=_layer + 1,
                            )
                            + ","
                        )
                        for v in obj
                    ),
                    " " * indent * _layer + bracket_cs + bracket[1] + def_cs,
                )
            )
        else:
            obj_str = (
                bracket_cs
                + bracket[0]
                + def_cs
                + f"{def_cs}, ".join(map(_obj_fmt, obj))
                + bracket_cs
                + bracket[1]
                + def_cs
            )
        return obj_str

    return f"\x1b[{obj_color}m{obj}{def_cs}"

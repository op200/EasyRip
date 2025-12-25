import ctypes
import datetime
import enum
import os
import sys
import traceback
from ctypes import wintypes
from typing import TextIO

from prompt_toolkit import ANSI, print_formatted_text

from . import easyrip_web
from .easyrip_mlang import gettext

__all__ = ["log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str], /) -> None: ...


class log:
    @classmethod
    def init(cls) -> None:
        """
        初始化日志功能

        1. 获取终端颜色
        2. 写入 \\</div> 以闭合已有日志
        """
        # 获取终端颜色
        if os.name == "nt":

            class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes._COORD),
                    ("dwCursorPosition", wintypes._COORD),
                    ("wAttributes", wintypes.WORD),
                    ("srWindow", wintypes.SMALL_RECT),
                    ("dwMaximumWindowSize", wintypes._COORD),
                ]

            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            hOut = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.FlushConsoleInputBuffer(hOut)
            ctypes.windll.kernel32.GetConsoleScreenBufferInfo(hOut, ctypes.byref(csbi))
            attributes = csbi.wAttributes
            color_map = {
                0: 0,  # 黑色
                1: 4,  # 蓝色
                2: 2,  # 绿色
                3: 6,  # 青色
                4: 1,  # 红色
                5: 5,  # 紫红色
                6: 3,  # 黄色
                7: 7,  # 白色
            }

            cls.default_foreground_color = (
                30
                + color_map.get(attributes & 0x0007, 9)
                + 60 * ((attributes & 0x0008) != 0)
            )
            cls.default_background_color = (
                40
                + color_map.get((attributes >> 4) & 0x0007, 9)
                + 60 * ((attributes & 0x0080) != 0)
            )

            if cls.default_foreground_color == 37:
                cls.default_foreground_color = 39
            if cls.default_background_color == 40:
                cls.default_background_color = 49

            if cls.default_background_color == 42:
                cls.debug_color = cls.time_color = 92

            if cls.default_background_color == 44 or cls.default_foreground_color == 34:
                cls.info_color = 96

            if cls.default_background_color == 43 or cls.default_foreground_color == 33:
                cls.warning_color = 93

            if cls.default_background_color == 41 or cls.default_foreground_color == 31:
                cls.error_color = 91

            if cls.default_background_color == 45 or cls.default_foreground_color == 35:
                cls.send_color = 95

        # 写入 </div>
        if os.path.isfile(cls.html_filename) and os.path.getsize(cls.html_filename):
            cls.write_html_log("</div></div></div>")

    class LogLevel(enum.Enum):
        _detail = enum.auto()
        debug = enum.auto()
        send = enum.auto()
        info = enum.auto()
        warning = enum.auto()
        error = enum.auto()
        none = enum.auto()

    class LogMode(enum.Enum):
        normal = enum.auto()
        only_print = enum.auto()
        only_write = enum.auto()

    html_filename: str = "EasyRip_log.html"  # 在调用前覆写
    print_level: LogLevel = LogLevel.send
    write_level: LogLevel = LogLevel.send

    default_foreground_color: int = 39
    default_background_color: int = 49
    time_color: int = 32
    debug_color: int = 32
    info_color: int = 34
    warning_color: int = 33
    error_color: int = 31
    send_color: int = 35

    debug_num: int = 0
    info_num: int = 0
    warning_num: int = 0
    error_num: int = 0
    send_num: int = 0

    @staticmethod
    def print(
        value: str,
        end: str = "",
        file: TextIO = sys.stdout,
    ) -> None:
        try:
            print_formatted_text(
                ANSI(value),
                end=end,
                file=file,
            )
        except Exception:
            print(
                value,
                end=end,
                file=file,
            )

    @classmethod
    def _do_log(
        cls,
        log_level: LogLevel,
        mode: LogMode,
        message: object,
        *fmt_args: object,
        stream: TextIO,
        print_level: LogLevel,
        write_level: LogLevel,
        is_format: bool = True,
        is_deep: bool = False,
        is_server: bool = False,
        http_send_header: str = "",
        **fmt_kwargs: object,
    ) -> None:
        if log_level == cls.LogLevel.none:
            return

        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        message = gettext(
            str(message),
            *fmt_args,
            **fmt_kwargs,
            is_format=is_format,
        )

        if is_deep:
            message = f"{traceback.format_exc()}\n{message}"

        time_str = f"\033[{cls.time_color}m{time_now}"

        match log_level:
            case cls.LogLevel.debug:
                cls.debug_num += 1

                if (
                    mode != cls.LogMode.only_write
                    and cls.print_level.value <= cls.LogLevel.debug.value
                    and cls.print_level.value <= print_level.value
                ):
                    cls.print(
                        f"{time_str}\033[{cls.debug_color}m [DEBUG] {message}\033[{cls.default_foreground_color}m\n",
                        end="",
                        file=stream,
                    )

                if (
                    mode != cls.LogMode.only_print
                    and cls.write_level.value <= cls.LogLevel.debug.value
                    and cls.write_level.value <= write_level.value
                ):
                    cls.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:green;">[DEBUG] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "DEBUG", message))

            case cls.LogLevel.info:
                cls.info_num += 1

                if (
                    mode != cls.LogMode.only_write
                    and cls.print_level.value <= cls.LogLevel.info.value
                    and cls.print_level.value <= print_level.value
                ):
                    cls.print(
                        f"{time_str}\033[{cls.info_color}m [INFO] {message}\033[{cls.default_foreground_color}m\n",
                        end="",
                        file=stream,
                    )

                if (
                    mode != cls.LogMode.only_print
                    and cls.write_level.value <= cls.LogLevel.info.value
                    and cls.write_level.value <= write_level.value
                ):
                    cls.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case cls.LogLevel.warning:
                cls.warning_num += 1

                if (
                    mode != cls.LogMode.only_write
                    and cls.print_level.value <= cls.LogLevel.warning.value
                    and cls.print_level.value <= print_level.value
                ):
                    cls.print(
                        f"{time_str}\033[{cls.warning_color}m [WARNING] {message}\033[{cls.default_foreground_color}m\n",
                        end="",
                        file=stream,
                    )

                if (
                    mode != cls.LogMode.only_print
                    and cls.write_level.value <= cls.LogLevel.warning.value
                    and cls.write_level.value <= write_level.value
                ):
                    cls.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case cls.LogLevel.error:
                cls.error_num += 1

                if (
                    mode != cls.LogMode.only_write
                    and cls.print_level.value <= cls.LogLevel.error.value
                    and cls.print_level.value <= print_level.value
                ):
                    cls.print(
                        f"{time_str}\033[{cls.error_color}m [ERROR] {message}\033[{cls.default_foreground_color}m\n",
                        end="",
                        file=stream,
                    )

                if (
                    mode != cls.LogMode.only_print
                    and cls.write_level.value <= cls.LogLevel.error.value
                    and cls.write_level.value <= write_level.value
                ):
                    cls.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case cls.LogLevel.send:
                cls.send_num += 1

                if is_server or easyrip_web.http_server.Event.is_run_command:
                    if (
                        mode != cls.LogMode.only_write
                        and cls.print_level.value <= cls.LogLevel.send.value
                        and cls.print_level.value <= print_level.value
                    ):
                        cls.print(
                            f"{time_str}\033[{cls.send_color}m [Send] {message}\033[{cls.default_foreground_color}m\n",
                            end="",
                            file=stream,
                        )

                    if (
                        mode != cls.LogMode.only_print
                        and cls.write_level.value <= cls.LogLevel.send.value
                        and cls.write_level.value <= write_level.value
                    ):
                        cls.write_html_log(
                            f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                        )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                elif cls.print_level.value <= cls.LogLevel.send.value:
                    cls.print(
                        f"\033[{cls.send_color}m{message}\033[{cls.default_foreground_color}m\n",
                        end="",
                    )

    @classmethod
    def debug(
        cls,
        message: object,
        /,
        *fmt_args: object,
        stream: TextIO = sys.stderr,
        print_level: LogLevel = LogLevel.debug,
        write_level: LogLevel = LogLevel.debug,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        **fmt_kwargs: object,
    ) -> None:
        cls._do_log(
            log.LogLevel.debug,
            mode,
            message,
            *fmt_args,
            stream=stream,
            print_level=print_level,
            write_level=write_level,
            is_format=is_format,
            is_deep=deep,
            is_server=False,
            http_send_header="",
            **fmt_kwargs,
        )

    @classmethod
    def info(
        cls,
        message: object,
        /,
        *fmt_args: object,
        stream: TextIO = sys.stderr,
        print_level: LogLevel = LogLevel.info,
        write_level: LogLevel = LogLevel.info,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        **fmt_kwargs: object,
    ) -> None:
        cls._do_log(
            log.LogLevel.info,
            mode,
            message,
            *fmt_args,
            stream=stream,
            print_level=print_level,
            write_level=write_level,
            is_format=is_format,
            is_deep=deep,
            is_server=False,
            http_send_header="",
            **fmt_kwargs,
        )

    @classmethod
    def warning(
        cls,
        message: object,
        /,
        *fmt_args: object,
        stream: TextIO = sys.stderr,
        print_level: LogLevel = LogLevel.warning,
        write_level: LogLevel = LogLevel.warning,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        **fmt_kwargs: object,
    ) -> None:
        cls._do_log(
            log.LogLevel.warning,
            mode,
            message,
            *fmt_args,
            stream=stream,
            print_level=print_level,
            write_level=write_level,
            is_format=is_format,
            is_deep=deep,
            is_server=False,
            http_send_header="",
            **fmt_kwargs,
        )

    @classmethod
    def error(
        cls,
        message: object,
        /,
        *fmt_args: object,
        stream: TextIO = sys.stderr,
        print_level: LogLevel = LogLevel.error,
        write_level: LogLevel = LogLevel.error,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        **fmt_kwargs: object,
    ) -> None:
        cls._do_log(
            log.LogLevel.error,
            mode,
            message,
            *fmt_args,
            stream=stream,
            print_level=print_level,
            write_level=write_level,
            is_format=is_format,
            is_deep=deep,
            is_server=False,
            http_send_header="",
            **fmt_kwargs,
        )

    @classmethod
    def send(
        cls,
        message: object,
        /,
        *fmt_args: object,
        stream: TextIO = sys.stdout,
        print_level: LogLevel = LogLevel.send,
        write_level: LogLevel = LogLevel.send,
        is_format: bool = True,
        mode: LogMode = LogMode.normal,
        is_server: bool = False,
        http_send_header: str = "",
        **fmt_kwargs: object,
    ) -> None:
        cls._do_log(
            log.LogLevel.send,
            mode,
            message,
            *fmt_args,
            stream=stream,
            print_level=print_level,
            write_level=write_level,
            is_format=is_format,
            is_deep=False,
            is_server=is_server,
            http_send_header=http_send_header,
            **fmt_kwargs,
        )

    @classmethod
    def write_html_log(
        cls,
        message: str,
    ) -> None:
        try:
            with open(cls.html_filename, "at", encoding="utf-8") as f:
                f.write(message)
        except Exception as e:
            _level = cls.write_level
            cls.write_level = cls.LogLevel.none
            cls.error(f"{e!r} {e}", deep=True)
            cls.write_level = _level

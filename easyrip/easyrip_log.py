import ctypes
import datetime
import enum
import os
import sys
import traceback
from ctypes import wintypes
from pathlib import Path
from typing import Self, TextIO

from prompt_toolkit import ANSI, print_formatted_text

from . import easyrip_web
from .easyrip_mlang import gettext

__all__ = ["Log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str], /) -> None: ...


class Log:
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

    def __init__(self) -> None:
        self.html_file: Path = Path("EasyRip_log.html")  # 在调用前覆写
        self.print_level: Log.LogLevel = Log.LogLevel.send
        self.write_level: Log.LogLevel = Log.LogLevel.send

        self.default_foreground_color: int = 39
        self.default_background_color: int = 49
        self.time_color: int = 32
        self.debug_color: int = 32
        self.info_color: int = 34
        self.warning_color: int = 33
        self.error_color: int = 31
        self.send_color: int = 35

        self.debug_num: int = 0
        self.info_num: int = 0
        self.warning_num: int = 0
        self.error_num: int = 0
        self.send_num: int = 0

    def init(self) -> Self:
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

            self.default_foreground_color = (
                30
                + color_map.get(attributes & 0x0007, 9)
                + 60 * ((attributes & 0x0008) != 0)
            )
            self.default_background_color = (
                40
                + color_map.get((attributes >> 4) & 0x0007, 9)
                + 60 * ((attributes & 0x0080) != 0)
            )

            if self.default_foreground_color == 37:
                self.default_foreground_color = 39
            if self.default_background_color == 40:
                self.default_background_color = 49

            if self.default_background_color == 42:
                self.debug_color = self.time_color = 92

            if (
                self.default_background_color == 44
                or self.default_foreground_color == 34
            ):
                self.info_color = 96

            if (
                self.default_background_color == 43
                or self.default_foreground_color == 33
            ):
                self.warning_color = 93

            if (
                self.default_background_color == 41
                or self.default_foreground_color == 31
            ):
                self.error_color = 91

            if (
                self.default_background_color == 45
                or self.default_foreground_color == 35
            ):
                self.send_color = 95

        # 写入 </div>
        if self.html_file.is_file() and self.html_file.stat().st_size:
            self.write_html_log("</div></div></div>")

        return self

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

    def _do_log(
        self,
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
        if log_level == self.LogLevel.none:
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

        time_str = f"\033[{self.time_color}m{time_now}"

        match log_level:
            case self.LogLevel.debug:
                self.debug_num += 1

                if (
                    mode != self.LogMode.only_write
                    and self.print_level.value <= self.LogLevel.debug.value
                    and self.print_level.value <= print_level.value
                ):
                    self.print(
                        f"{time_str}\033[{self.debug_color}m [DEBUG] {message}\033[{self.default_foreground_color}m\n",
                        file=stream,
                    )

                if (
                    mode != self.LogMode.only_print
                    and self.write_level.value <= self.LogLevel.debug.value
                    and self.write_level.value <= write_level.value
                ):
                    self.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:green;">[DEBUG] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "DEBUG", message))

            case self.LogLevel.info:
                self.info_num += 1

                if (
                    mode != self.LogMode.only_write
                    and self.print_level.value <= self.LogLevel.info.value
                    and self.print_level.value <= print_level.value
                ):
                    self.print(
                        f"{time_str}\033[{self.info_color}m [INFO] {message}\033[{self.default_foreground_color}m\n",
                        file=stream,
                    )

                if (
                    mode != self.LogMode.only_print
                    and self.write_level.value <= self.LogLevel.info.value
                    and self.write_level.value <= write_level.value
                ):
                    self.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case self.LogLevel.warning:
                self.warning_num += 1

                if (
                    mode != self.LogMode.only_write
                    and self.print_level.value <= self.LogLevel.warning.value
                    and self.print_level.value <= print_level.value
                ):
                    self.print(
                        f"{time_str}\033[{self.warning_color}m [WARNING] {message}\033[{self.default_foreground_color}m\n",
                        file=stream,
                    )

                if (
                    mode != self.LogMode.only_print
                    and self.write_level.value <= self.LogLevel.warning.value
                    and self.write_level.value <= write_level.value
                ):
                    self.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case self.LogLevel.error:
                self.error_num += 1

                if (
                    mode != self.LogMode.only_write
                    and self.print_level.value <= self.LogLevel.error.value
                    and self.print_level.value <= print_level.value
                ):
                    self.print(
                        f"{time_str}\033[{self.error_color}m [ERROR] {message}\033[{self.default_foreground_color}m\n",
                        file=stream,
                    )

                if (
                    mode != self.LogMode.only_print
                    and self.write_level.value <= self.LogLevel.error.value
                    and self.write_level.value <= write_level.value
                ):
                    self.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case self.LogLevel.send:
                self.send_num += 1

                if is_server or easyrip_web.http_server.Event.is_run_command:
                    if (
                        mode != self.LogMode.only_write
                        and self.print_level.value <= self.LogLevel.send.value
                        and self.print_level.value <= print_level.value
                    ):
                        self.print(
                            f"{time_str}\033[{self.send_color}m [Send] {message}\033[{self.default_foreground_color}m\n",
                            file=stream,
                        )

                    if (
                        mode != self.LogMode.only_print
                        and self.write_level.value <= self.LogLevel.send.value
                        and self.write_level.value <= write_level.value
                    ):
                        self.write_html_log(
                            f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                        )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                elif self.print_level.value <= self.LogLevel.send.value:
                    self.print(
                        f"\033[{self.send_color}m{message}\033[{self.default_foreground_color}m\n",
                    )

    def debug(
        self,
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
        self._do_log(
            self.LogLevel.debug,
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

    def info(
        self,
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
        self._do_log(
            self.LogLevel.info,
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

    def warning(
        self,
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
        self._do_log(
            self.LogLevel.warning,
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

    def error(
        self,
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
        self._do_log(
            self.LogLevel.error,
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

    def send(
        self,
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
        self._do_log(
            self.LogLevel.send,
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

    def write_html_log(
        self,
        message: str,
    ) -> None:
        try:
            with self.html_file.open("at", encoding="utf-8") as f:
                f.write(message)
        except Exception as e:
            _level = self.write_level
            self.write_level = self.LogLevel.none
            self.error(f"{e!r} {e}", deep=True)
            self.write_level = _level


log = Log()
"""Easy Rip 内部使用的 log 单例，用于向前兼容"""

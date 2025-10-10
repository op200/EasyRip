import ctypes
import datetime
import enum
import os
import sys
import traceback
from ctypes import wintypes

from . import easyrip_web
from .easyrip_mlang import Global_lang_val, gettext

__all__ = ["Event", "log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str]):
        pass


class log:
    @staticmethod
    def init():
        """
        1. 获取终端颜色
        2. 写入 \\</div>
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

            log.default_foreground_color = (
                30
                + color_map.get(attributes & 0x0007, 9)
                + 60 * ((attributes & 0x0008) != 0)
            )
            log.default_background_color = (
                40
                + color_map.get((attributes >> 4) & 0x0007, 9)
                + 60 * ((attributes & 0x0080) != 0)
            )

            if log.default_foreground_color == 37:
                log.default_foreground_color = 39
            if log.default_background_color == 40:
                log.default_background_color = 49

            if log.default_background_color == 42:
                log.debug_color = log.time_color = 92

            if log.default_background_color == 44 or log.default_foreground_color == 34:
                log.info_color = 96

            if log.default_background_color == 43 or log.default_foreground_color == 33:
                log.warning_color = 93

            if log.default_background_color == 41 or log.default_foreground_color == 31:
                log.error_color = 91

            if log.default_background_color == 45 or log.default_foreground_color == 35:
                log.send_color = 95

        # 写入 </div>
        if os.path.isfile(log.html_filename) and os.path.getsize(log.html_filename):
            log.write_html_log("</div></div></div>")

    class LogLevel(enum.Enum):
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

    html_filename: str = "encoding_log.html"  # 在调用前覆写
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

    hr = "———————————————————————————————————"

    @staticmethod
    def _do_log(
        log_level: LogLevel,
        mode: LogMode,
        message: object,
        *vals: object,
        is_format: bool = True,
        is_deep: bool = False,
        is_server: bool = False,
        http_send_header: str = "",
    ):
        if log_level == log.LogLevel.none:
            return

        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        message = gettext(
            message
            if type(message) is Global_lang_val.Extra_text_index
            else str(message),
            *vals,
            is_format=is_format,
        )

        if is_deep:
            message = f"{traceback.format_exc()}\n{message}"

        time_str = f"\033[{log.time_color}m{time_now}"

        match log_level:
            case log.LogLevel.debug:
                log.debug_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.print_level.value <= log.LogLevel.debug.value
                ):
                    print(
                        f"{time_str}\033[{log.debug_color}m [DEBUG] {message}\033[{log.default_foreground_color}m"
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.write_level.value <= log.LogLevel.debug.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:green;">[DEBUG] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.info:
                log.info_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.print_level.value <= log.LogLevel.info.value
                ):
                    print(
                        f"{time_str}\033[{log.info_color}m [INFO] {message}\033[{log.default_foreground_color}m"
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.write_level.value <= log.LogLevel.info.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.warning:
                log.warning_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.print_level.value <= log.LogLevel.warning.value
                ):
                    print(
                        f"{time_str}\033[{log.warning_color}m [WARNING] {message}\033[{log.default_foreground_color}m",
                        file=sys.stderr,
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.write_level.value <= log.LogLevel.warning.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case log.LogLevel.error:
                log.error_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.print_level.value <= log.LogLevel.error.value
                ):
                    print(
                        f"{time_str}\033[{log.error_color}m [ERROR] {message}\033[{log.default_foreground_color}m",
                        file=sys.stderr,
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.write_level.value <= log.LogLevel.error.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case log.LogLevel.send:
                log.send_num += 1

                if is_server or easyrip_web.http_server.Event.is_run_command:
                    if log.print_level.value <= log.LogLevel.send.value:
                        print(
                            f"{time_str}\033[{log.send_color}m [Send] {message}\033[{log.default_foreground_color}m"
                        )

                    if log.write_level.value <= log.LogLevel.send.value:
                        log.write_html_log(
                            f'<div style="background-color:#b4b4b4;margin-bottom:2px;white-space:pre-wrap;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                        )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                elif log.print_level.value <= log.LogLevel.send.value:
                    print(
                        f"\033[{log.send_color}m{message}\033[{log.default_foreground_color}m"
                    )

    @staticmethod
    def debug(
        message: object,
        /,
        *vals: object,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        level: LogLevel = LogLevel.debug,
    ):
        log._do_log(
            level,
            mode,
            message,
            *vals,
            is_format=is_format,
            is_deep=deep,
        )

    @staticmethod
    def info(
        message: object,
        /,
        *vals: object,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        level: LogLevel = LogLevel.info,
    ):
        log._do_log(
            level,
            mode,
            message,
            *vals,
            is_format=is_format,
            is_deep=deep,
        )

    @staticmethod
    def warning(
        message: object,
        /,
        *vals: object,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        level: LogLevel = LogLevel.warning,
    ):
        log._do_log(
            level,
            mode,
            message,
            *vals,
            is_format=is_format,
            is_deep=deep,
        )

    @staticmethod
    def error(
        message: object,
        /,
        *vals: object,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
        level: LogLevel = LogLevel.error,
    ):
        log._do_log(
            level,
            mode,
            message,
            *vals,
            is_format=is_format,
            is_deep=deep,
        )

    @staticmethod
    def send(
        message: object,
        /,
        *vals: object,
        is_format: bool = True,
        mode: LogMode = LogMode.normal,
        is_server: bool = False,
        http_send_header: str = "",
        level: LogLevel = LogLevel.send,
    ):
        log._do_log(
            level,
            mode,
            message,
            *vals,
            http_send_header=http_send_header,
            is_format=is_format,
            is_server=is_server,
            is_deep=False,
        )

    @staticmethod
    def write_html_log(message: str):
        try:
            with open(log.html_filename, "at", encoding="utf-8") as f:
                f.write(message)
        except Exception as e:
            _level = log.write_level
            log.write_level = log.LogLevel.none
            log.error(f"{e!r} {e}", deep=True)
            log.write_level = _level

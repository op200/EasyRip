import sys
import enum
import datetime
import traceback

from .easyrip_mlang import gettext, GlobalLangVal
from . import easyrip_web


__all__ = ["Event", "log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str]):
        pass


class log:
    class LogLevel(enum.Enum):
        send = enum.auto()
        info = enum.auto()
        warning = enum.auto()
        error = enum.auto()
        none = enum.auto()

    class LogMode(enum.Enum):
        normal = enum.auto()
        only_print = enum.auto()
        only_write = enum.auto()

    html_log_file: str = "encoding_log.html"  # 在调用前覆写
    log_print_level: LogLevel = LogLevel.send
    log_write_level: LogLevel = LogLevel.send

    default_foreground_color: int = 39
    default_background_color: int = 49

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
        *vals,
        **kwargs,
    ):
        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        message = gettext(
            message if type(message) is GlobalLangVal.ExtraTextIndex else str(message),
            *vals,
            is_format=kwargs.get("is_format", True),
        )
        if kwargs.get("deep"):
            message = f"{traceback.format_exc()}\n{message}"

        time_str = f"\033[{92 if log.default_background_color == 42 else 32}m{time_now}"

        match log_level:
            case log.LogLevel.info:
                log.info_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.log_print_level.value <= log.LogLevel.info.value
                ):
                    print(
                        f"{time_str}\033[{94 if log.default_background_color == 44 else 34}m [INFO] {message}\033[{log.default_foreground_color}m"
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.log_write_level.value <= log.LogLevel.info.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.warning:
                log.warning_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.log_print_level.value <= log.LogLevel.warning.value
                ):
                    print(
                        f"{time_str}\033[{93 if log.default_background_color == 43 else 33}m [WARNING] {message}\033[{log.default_foreground_color}m",
                        file=sys.stderr,
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.log_write_level.value <= log.LogLevel.warning.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case log.LogLevel.error:
                log.error_num += 1

                if (
                    mode != log.LogMode.only_write
                    and log.log_print_level.value <= log.LogLevel.error.value
                ):
                    print(
                        f"{time_str}\033[{91 if log.default_background_color == 41 else 31}m [ERROR] {message}\033[{log.default_foreground_color}m",
                        file=sys.stderr,
                    )

                if (
                    mode != log.LogMode.only_print
                    and log.log_write_level.value <= log.LogLevel.error.value
                ):
                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case log.LogLevel.send:
                log.send_num += 1

                if (
                    kwargs.get("is_server", False)
                    or easyrip_web.http_server.Event.is_run_command[-1]
                ):
                    http_send_header = kwargs.get("http_send_header", "")

                    if log.log_print_level.value <= log.LogLevel.send.value:
                        print(
                            f"{time_str}\033[{95 if log.default_background_color == 45 else 35}m [Send] {message}\033[{log.default_foreground_color}m"
                        )

                    if log.log_write_level.value <= log.LogLevel.send.value:
                        log.write_html_log(
                            f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                        )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                elif log.log_print_level.value <= log.LogLevel.send.value:
                    print(
                        f"\033[{95 if log.default_background_color == 45 else 35}m{message}\033[{log.default_foreground_color}m"
                    )

    @staticmethod
    def info(
        message: object,
        *vals,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
    ):
        log._do_log(
            log.LogLevel.info,
            mode,
            message,
            *vals,
            is_format=is_format,
            deep=deep,
        )

    @staticmethod
    def warning(
        message: object,
        *vals,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
    ):
        print(vals)
        print(mode, type(mode))
        log._do_log(
            log.LogLevel.warning,
            mode,
            message,
            *vals,
            is_format=is_format,
            deep=deep,
        )

    @staticmethod
    def error(
        message: object,
        *vals,
        is_format: bool = True,
        deep: bool = False,
        mode: LogMode = LogMode.normal,
    ):
        log._do_log(
            log.LogLevel.error,
            mode,
            message,
            *vals,
            is_format=is_format,
            deep=deep,
        )

    @staticmethod
    def send(
        header: str,
        message: object,
        *vals,
        is_format: bool = True,
        mode: LogMode = LogMode.normal,
        is_server: bool = False,
    ):
        log._do_log(
            log.LogLevel.send,
            mode,
            message,
            *vals,
            http_send_header=header,
            is_format=is_format,
            is_server=is_server,
            deep=False,
        )

    @staticmethod
    def write_html_log(message: str):
        try:
            with open(log.html_log_file, "at", encoding="utf-8") as f:
                f.write(message)
        except Exception as e:
            _level = log.log_write_level
            log.log_write_level = log.LogLevel.none
            log.error(f"{repr(e)} {e}", deep=True)
            log.log_write_level = _level

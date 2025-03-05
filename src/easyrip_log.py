import sys
from typing import Literal
import enum
import datetime

from easyrip_mlang import gettext, GlobalLangVal

__all__ = ["Event", "print", "log"]


class Event:
    def append_http_server_log_queue(message: tuple[str, str, str]):
        pass


_print = print


def print(
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    # file: SupportsWrite[str] | None = sys.stderr,
    file=sys.stderr,
    flush: Literal[False] = False,
):
    _print(*values, sep=sep, end=end, file=file, flush=flush)


class log:
    html_log_file = gettext("encoding_log.html")

    hr = "———————————————————————————————————"

    class LogLevel(enum.Enum):
        info = enum.auto()
        warning = enum.auto()
        error = enum.auto()
        http_send = enum.auto()

    @staticmethod
    def output(log_level: LogLevel, message, *vals, **kwargs):
        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        if kwargs.get("is_format", True):
            message = gettext(
                message
                if type(message) is GlobalLangVal.ExtraTextIndex
                else str(message),
                *vals,
            )
        else:
            message = str(message)

        match log_level:
            case log.LogLevel.info:
                print(f"\033[32m{time_now}\033[34m [INFO] {message}\033[0m")

                with open("编码日志.html", "a", encoding="utf-8") as f:
                    f.write(
                        rf'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.warning:
                print(f"\033[32m{time_now}\033[33m [WARNING] {message}\033[0m")

                with open("编码日志.html", "a", encoding="utf-8") as f:
                    f.write(
                        rf'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case log.LogLevel.error:
                print(f"\033[32m{time_now}\033[31m [ERROR] {message}\033[0m")

                with open("编码日志.html", "a", encoding="utf-8") as f:
                    f.write(
                        rf'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                    )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case log.LogLevel.http_send:
                print(f"\033[32m{time_now}\033[35m [Send] {message}\033[0m")

                with open("编码日志.html", "a", encoding="utf-8") as f:
                    f.write(
                        rf'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:deeppink;">[Send] {message}</span></div>'
                    )

                Event.append_http_server_log_queue(
                    (kwargs.get("http_send_header", ""), "Send", message)
                )

    @staticmethod
    def info(message, *vals, is_format: bool = True):
        log.output(log.LogLevel.info, message, *vals, is_format=is_format)

    @staticmethod
    def warning(message, *vals, is_format: bool = True):
        log.output(log.LogLevel.warning, message, *vals, is_format=is_format)

    @staticmethod
    def error(message, *vals, is_format: bool = True):
        log.output(log.LogLevel.error, message, *vals, is_format=is_format)

    @staticmethod
    def http_send(header: str, message, *vals, is_format: bool = True):
        log.output(
            log.LogLevel.http_send,
            message,
            *vals,
            http_send_header=header,
            is_format=is_format,
        )

    @staticmethod
    def write_html_log(message: str):
        with open("编码日志.html", "at", encoding="utf-8") as f:
            f.write(message)

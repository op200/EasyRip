import sys
import enum
import datetime

from easyrip_mlang import gettext, GlobalLangVal
import easyrip_web

__all__ = ["Event", "log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str]):
        pass


class log:
    html_log_file = "encoding_log.html"  # 在调用前重定义

    hr = "———————————————————————————————————"

    class LogLevel(enum.Enum):
        info = enum.auto()
        warning = enum.auto()
        error = enum.auto()
        send = enum.auto()

    @staticmethod
    def _print_log(log_level: LogLevel, message: object, *vals, **kwargs):
        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        message = gettext(
            message if type(message) is GlobalLangVal.ExtraTextIndex else str(message),
            *vals,
            is_format=kwargs.get("is_format", True),
        )

        match log_level:
            case log.LogLevel.info:
                print(f"\033[32m{time_now}\033[34m [INFO] {message}\033[0m")

                log.write_html_log(
                    f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.warning:
                print(
                    f"\033[32m{time_now}\033[33m [WARNING] {message}\033[0m",
                    file=sys.stderr,
                )

                log.write_html_log(
                    f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case log.LogLevel.error:
                print(
                    f"\033[32m{time_now}\033[31m [ERROR] {message}\033[0m",
                    file=sys.stderr,
                )

                log.write_html_log(
                    f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>'
                )

                Event.append_http_server_log_queue((time_now, "ERROR", message))

            case log.LogLevel.send:
                if (
                    kwargs.get("is_server", False)
                    or easyrip_web.http_server.Event.is_run_command[-1]
                ):
                    http_send_header = kwargs.get("http_send_header", "")
                    print(f"\033[32m{time_now}\033[35m [Send] {message}\033[0m")

                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                    )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                else:
                    print(f"\033[35m{message}\033[0m")

    @staticmethod
    def info(message: object, *vals, is_format: bool = True):
        log._print_log(log.LogLevel.info, message, *vals, is_format=is_format)

    @staticmethod
    def warning(message: object, *vals, is_format: bool = True):
        log._print_log(log.LogLevel.warning, message, *vals, is_format=is_format)

    @staticmethod
    def error(message: object, *vals, is_format: bool = True):
        log._print_log(log.LogLevel.error, message, *vals, is_format=is_format)

    @staticmethod
    def send(
        header: str,
        message: object,
        *vals,
        is_format: bool = True,
        is_server: bool = False,
    ):
        log._print_log(
            log.LogLevel.send,
            message,
            *vals,
            http_send_header=header,
            is_format=is_format,
            is_server=is_server,
        )

    @staticmethod
    def write_html_log(message: str):
        with open(log.html_log_file, "at", encoding="utf-8") as f:
            f.write(message)

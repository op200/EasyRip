import sys
import enum
import datetime
import traceback

from easyrip_mlang import gettext, GlobalLangVal
import easyrip_web

__all__ = ["Event", "log"]


class Event:
    @staticmethod
    def append_http_server_log_queue(message: tuple[str, str, str]):
        pass


class log:
    html_log_file: str = "encoding_log.html"  # 在调用前重定义
    default_foreground_color: int = 39
    default_background_color: int = 49

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
        if kwargs.get("deep"):
            message = f"{traceback.format_exc()}\n{message}"

        time_str = f"\033[32m{time_now}"
        default_color_str: str = (
            f"\033[{log.default_foreground_color};{log.default_background_color}m"
            if log.default_foreground_color != 39 and log.default_background_color != 49
            else "\033[0m"
        )

        match log_level:
            case log.LogLevel.info:
                print(
                    f"{time_str}\033[{94 if log.default_background_color == 44 else 34}m [INFO] {message}{default_color_str}"
                )

                log.write_html_log(
                    f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>'
                )

                Event.append_http_server_log_queue((time_now, "INFO", message))

            case log.LogLevel.warning:
                print(
                    f"{time_str}\033[{93 if log.default_background_color == 43 else 33}m [WARNING] {message}{default_color_str}",
                    file=sys.stderr,
                )

                log.write_html_log(
                    f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>'
                )

                Event.append_http_server_log_queue((time_now, "WARNING", message))

            case log.LogLevel.error:
                print(
                    f"{time_str}\033[{91 if log.default_background_color == 41 else 31}m [ERROR] {message}{default_color_str}",
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
                    print(
                        f"{time_str}\033[{95 if log.default_background_color == 45 else 35}m [Send] {message}{default_color_str}"
                    )

                    log.write_html_log(
                        f'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;white-space:pre-wrap;">{time_now}</span> <span style="color:deeppink;">[Send] <span style="color:green;">{http_send_header}</span>{message}</span></div>'
                    )

                    Event.append_http_server_log_queue(
                        (http_send_header, "Send", message)
                    )
                else:
                    print(f"\033[35m{message}\033[0m")

    @staticmethod
    def info(message: object, *vals, is_format: bool = True, deep: bool = False):
        log._print_log(
            log.LogLevel.info,
            message,
            *vals,
            is_format=is_format,
            deep_stack=deep,
        )

    @staticmethod
    def warning(message: object, *vals, is_format: bool = True, deep: bool = False):
        log._print_log(
            log.LogLevel.warning,
            message,
            *vals,
            is_format=is_format,
            deep=deep,
        )

    @staticmethod
    def error(message: object, *vals, is_format: bool = True, deep: bool = False):
        log._print_log(
            log.LogLevel.error,
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
        is_server: bool = False,
    ):
        log._print_log(
            log.LogLevel.send,
            message,
            *vals,
            http_send_header=header,
            is_format=is_format,
            is_server=is_server,
            deep=False,
        )

    @staticmethod
    def write_html_log(message: str):
        with open(log.html_log_file, "at", encoding="utf-8") as f:
            f.write(message)

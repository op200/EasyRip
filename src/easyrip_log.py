import sys
from typing import Literal
import enum
import datetime

from easyrip_mlang import gettext

__all__ = ['print', 'log']

_print = print

def print(
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    # file: SupportsWrite[str] | None = sys.stderr,
    file = sys.stderr,
    flush: Literal[False] = False
):
    _print(*values,
           sep = sep,
           end = end,
           file = file,
           flush = flush)


class log:

    hr = '———————————————————————————————————'

    class LogLevel(enum.Enum):
        info = enum.auto()
        warning = enum.auto()
        error = enum.auto()

    @staticmethod
    def output(log_level: LogLevel, message, *vals):
        time_now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]
        message = gettext(message, *vals)

        if log_level == log.LogLevel.info:
            print(f'\033[32m{time_now}\033[34m [INFO] {message}\033[0m')
            with open('编码日志.html', 'a', encoding='utf-8') as f:
                f.write(fr'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:blue;">[INFO] {message}</span></div>')

        if log_level == log.LogLevel.warning:
            print(f'\033[32m{time_now}\033[33m [WARNING] {message}\033[0m')
            with open('编码日志.html', 'a', encoding='utf-8') as f:
                f.write(fr'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:yellow;">[WARNING] {message}</span></div>')

        if log_level == log.LogLevel.error:
            print(f'\033[32m{time_now}\033[31m [ERROR] {message}\033[0m')
            with open('编码日志.html', 'a', encoding='utf-8') as f:
                f.write(fr'<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time_now}</span> <span style="color:red;">[ERROR] {message}</span></div>')

    @staticmethod
    def info(message, *vals):
        log.output(log.LogLevel.info, message, *vals)

    @staticmethod
    def warning(message, *vals):
        log.output(log.LogLevel.warning, message, *vals)

    @staticmethod
    def error(message, *vals):
        log.output(log.LogLevel.error, message, *vals)


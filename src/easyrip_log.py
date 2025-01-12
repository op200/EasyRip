import sys
from typing import Literal

from loguru import logger

logger.remove()

logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")

def html_log_formatter(record):
    if record["level"].name == 'INFO':
        return '<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time:YYYY.MM.DD HH:mm:ss.SS}\\</span> <span style="color:blue;">[{level}] {message}\\</span>\\</div>\n{exception}'

    elif record["level"].name == 'WARNING':
        return '<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time:YYYY.MM.DD HH:mm:ss.SS}\\</span> <span style="color:yellow;">[{level}] {message}\\</span>\\</div>\n{exception}'

    elif record["level"].name == 'ERROR':
        return '<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time:YYYY.MM.DD HH:mm:ss.SS}\\</span> <span style="color:red;">[{level}] {message}\\</span>\\</div>\n{exception}'

    else:
        return '<div style="background-color:#b4b4b4;margin-bottom:2px;"><span style="color:green;">{time:YYYY.MM.DD HH:mm:ss.SS}\\</span> <span>[{level}] {message}\\</span>\\</div>\n{exception}'
logger.add('编码日志.html', format=html_log_formatter)


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

    @staticmethod
    def info( __message: str, *args, **kwargs):
        logger.info(__message, *args, **kwargs)

    @staticmethod
    def warning( __message: str, *args, **kwargs):
        logger.warning(__message, *args, **kwargs)

    @staticmethod
    def error( __message: str, *args, **kwargs):
        logger.error(__message, *args, **kwargs)


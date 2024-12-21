import sys
from typing import Literal

from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")
logger.add('编码日志.log', format="[{level}] {time:YYYY.MM.DD HH:mm:ss.SS} {message}")


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


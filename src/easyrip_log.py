import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")
logger.add('编码日志.log', format="[{level}] {time:YYYY.MM.DD HH:mm:ss.SS} {message}")


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


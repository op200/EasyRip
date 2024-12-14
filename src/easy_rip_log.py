import sys

from loguru import logger as log

log.remove()
log.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")
log.add('编码日志.log', format="[{level}] {time:YYYY.MM.DD HH:mm:ss.SS} {message}")
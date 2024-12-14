import sys

from loguru import logger as log

log.remove()
log.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")
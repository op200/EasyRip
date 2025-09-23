from .easyrip_main import (
    init,
    run_command,
    Ripper,
    log,
    check_env,
    gettext,
    check_ver,
    Global_val,
    Global_lang_val,
)
from .ripper import Media_info

__all__ = [
    "init",
    "run_command",
    "log",
    "Ripper",
    "check_env",
    "gettext",
    "check_ver",
    "Global_val",
    "Global_lang_val",
    "Media_info",
]

__version__ = Global_val.PROJECT_VERSION

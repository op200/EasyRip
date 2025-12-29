import os
import sys
from functools import cache
from pathlib import Path

PROJECT_NAME = "Easy Rip"
PROJECT_VERSION = "4.11.1"
PROJECT_TITLE = f"{PROJECT_NAME} v{PROJECT_VERSION}"
PROJECT_URL = "https://github.com/op200/EasyRip"
PROJECT_RELEASE_API = "https://api.github.com/repos/op200/EasyRip/releases/latest"


@cache
def get_CONFIG_DIR():
    if sys.platform == "win32":
        # Windows: C:\Users\<用户名>\AppData\Roaming\<app_name>
        __config_dir = Path(os.getenv("APPDATA", ""))
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/<app_name>
        __config_dir = Path(os.path.expanduser("~")) / "Library" / "Application Support"
    else:
        # Linux: ~/.config/<app_name>
        __config_dir = Path(os.path.expanduser("~")) / ".config"

    return Path(__config_dir) / PROJECT_NAME


C_D = "\x04"
C_Z = "\x1a"

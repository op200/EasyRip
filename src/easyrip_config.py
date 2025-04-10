import json
import os
import sys

from global_val import GlobalVal
from easyrip_log import log
from easyrip_mlang import gettext


PROJECT_NAME = GlobalVal.PROJECT_NAME
CONFIG_VERSION = "2.9"


class config:
    config_dir: str = ""
    config_pathname: str = ""
    _config: dict | None = None

    @staticmethod
    def init():
        if sys.platform == "win32":
            # Windows: C:\Users\<用户名>\AppData\Roaming\<app_name>
            config.config_dir = os.getenv("APPDATA", "")
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/<app_name>
            config.config_dir = (
                os.path.expanduser("~"),
                "Library",
                "Application Support",
                PROJECT_NAME,
            )
        else:
            # Linux: ~/.config/<app_name>
            config.config_dir = os.path.expanduser("~"), ".config"
        config.config_dir = os.path.join(config.config_dir, PROJECT_NAME)
        config.config_pathname = os.path.join(config.config_dir, "config.json")

        if not os.path.exists(config.config_pathname):
            os.makedirs(config.config_dir, exist_ok=True)
            with open(config.config_pathname, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": CONFIG_VERSION,
                        "user_profile": {
                            "language": "auto",
                            "check_update": True,
                        },
                    },
                    f,
                    ensure_ascii=False,
                    indent=3,
                )
        else:
            with open(config.config_pathname, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data.get("version") != CONFIG_VERSION:
                        log.warning("The config version is not match, use '{}' to regenerate config file", "config clear")
                except json.JSONDecodeError as e:
                    log.error(f"{repr(e)} {e}", deep=True)

        config._read_config()

    @staticmethod
    def open_config_dir():
        if not os.path.exists(config.config_dir):
            config.init()
        os.startfile(config.config_dir)

    @staticmethod
    def regenerate_config():
        if os.path.exists(config.config_dir):
            os.remove(config.config_pathname)
        config.init()

    @staticmethod
    def _read_config() -> bool:
        if not os.path.exists(config.config_dir):
            config.init()
        with open(config.config_pathname, "r", encoding="utf-8") as f:
            try:
                config._config = json.load(f)
                return True
            except json.JSONDecodeError as e:
                log.error(f"{repr(e)} {e}", deep=True)
                return False

    @staticmethod
    def _write_config(new_config: dict | None = None) -> bool:
        if not os.path.exists(config.config_dir):
            config.init()
        if new_config is not None:
            config._config = new_config
        del new_config

        with open(config.config_pathname, "w", encoding="utf-8") as f:
            try:
                json.dump(config._config, f, ensure_ascii=False, indent=3)
                return True
            except json.JSONDecodeError as e:
                log.error(f"{repr(e)} {e}", deep=True)
                return False

    @staticmethod
    def set_user_profile(key: str, val: str | int | float | bool) -> bool:
        if config._config is None:
            if not config._read_config():
                return False

        if config._config is None:
            log.error("Config is None")
            return False

        if "user_profile" not in config._config:
            log.error("User profile is not found in config")
            return False

        if key in config._config["user_profile"]:
            config._config["user_profile"][key] = val
        else:
            log.error("Key {} is not found in user profile", key)
            return False
        return config._write_config()

    @staticmethod
    def get_user_profile(key: str) -> str | int | float | bool | None:
        if config._config is None:
            config._read_config()
        if config._config is None:
            return None
        if not isinstance(config._config["user_profile"], dict):
            log.error("User profile is not a valid dictionary")
            return None
        if key not in config._config["user_profile"]:
            log.error("Key {} is not found in user profile", key)
            return None
        return config._config["user_profile"][key]
    
    @staticmethod
    def show_config_list():
        if config._config is None:
            config.init()
        if config._config is None:
            log.error("Config is None")
            return

        user_profile: dict = config._config["user_profile"]
        length = max(len(k) for k in user_profile.keys())
        for k, v in user_profile.items():
            log.send('', f"{gettext(k):>{length}} = {v}")

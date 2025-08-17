import json
import os
import sys

from .global_val import Global_val
from .easyrip_log import log
from .easyrip_mlang import gettext


PROJECT_NAME = Global_val.PROJECT_NAME
CONFIG_VERSION = "2.9.4"


class config:
    _config_dir: str = ""
    _config_pathname: str = ""
    _config: dict | None = None

    @staticmethod
    def init():
        if sys.platform == "win32":
            # Windows: C:\Users\<用户名>\AppData\Roaming\<app_name>
            config._config_dir = os.getenv("APPDATA", "")
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/<app_name>
            config._config_dir = (
                os.path.expanduser("~"),
                "Library",
                "Application Support",
                PROJECT_NAME,
            )
        else:
            # Linux: ~/.config/<app_name>
            config._config_dir = os.path.expanduser("~"), ".config"
        config._config_dir = os.path.join(config._config_dir, PROJECT_NAME)
        config._config_pathname = os.path.join(config._config_dir, "config.json")

        if not os.path.exists(config._config_pathname):
            os.makedirs(config._config_dir, exist_ok=True)
            with open(
                config._config_pathname, "wt", encoding="utf-8", newline="\n"
            ) as f:
                json.dump(
                    {
                        "version": CONFIG_VERSION,
                        "user_profile": {
                            "language": "auto",
                            "check_update": True,
                            "check_dependent": True,
                            "startup_directory": "",
                            "force_log_file_path": "",
                            "log_print_level": "send",
                            "log_write_level": "send",
                        },
                    },
                    f,
                    ensure_ascii=False,
                    indent=3,
                )
        else:
            with open(config._config_pathname, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data.get("version") != CONFIG_VERSION:
                        log.warning(
                            "The config version is not match, use '{}' to regenerate config file",
                            "config clear",
                        )
                except json.JSONDecodeError as e:
                    log.error(f"{repr(e)} {e}", deep=True)

        config._read_config()

    @staticmethod
    def open_config_dir():
        if not os.path.exists(config._config_dir):
            config.init()
        os.startfile(config._config_dir)

    @staticmethod
    def regenerate_config():
        if os.path.exists(config._config_pathname):
            try:
                os.remove(config._config_pathname)
            except Exception as e:
                log.error(f"{repr(e)} {e}", deep=True)
        config.init()
        log.info("Regenerate config file")

    @staticmethod
    def _read_config() -> bool:
        if not os.path.exists(config._config_dir):
            config.init()
        with open(config._config_pathname, "r", encoding="utf-8") as f:
            try:
                config._config = json.load(f)
                return True
            except json.JSONDecodeError as e:
                log.error(f"{repr(e)} {e}", deep=True)
                return False

    @staticmethod
    def _write_config(new_config: dict | None = None) -> bool:
        if not os.path.exists(config._config_dir):
            config.init()
        if new_config is not None:
            config._config = new_config
        del new_config

        with open(config._config_pathname, "wt", encoding="utf-8", newline="\n") as f:
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
            log.error("Key '{}' is not found in user profile", key)
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
            log.error("Key '{}' is not found in user profile", key)
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
        length_key = max(len(k) for k in user_profile.keys())
        length_val = max(len(str(v)) for v in user_profile.values())
        for k, v in user_profile.items():
            log.send(
                "",
                f"{k:>{length_key}} = {str(v):<{length_val}} - {config._get_config_about(k)}",
            )

    @staticmethod
    def _get_config_about(key: str) -> str:
        return (
            {
                "language": gettext(
                    "Easy Rip's language, support: {}", "auto, en, zh-CN"
                ),
                "check_update": gettext("Auto check the update of Easy Rip"),
                "check_dependent": gettext(
                    "Auto check the versions of all dependent programs"
                ),
                "startup_directory": gettext(
                    "Program startup directory, when the value is empty, starts in the working directory"
                ),
                "force_log_file_path": gettext(
                    "Force change of log file path, when the value is empty, it is the working directory"
                ),
                "log_print_level": gettext(
                    "Logs this level and above will be printed, and if the value is 'none', they will not be printed, support: {}",
                    "none, error, warning, info, send, debug",
                ),
                "log_write_level": gettext(
                    "Logs this level and above will be written, and if the value is 'none', they will not be written, support: {}",
                    "none, error, warning, info, send, debug",
                ),
            }
            | (config._config or dict())
        ).get(key, "None about")

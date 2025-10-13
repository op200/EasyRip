import json
import os
import sys
from pathlib import Path

from . import global_val
from .easyrip_log import log
from .easyrip_mlang import all_supported_lang_map, gettext

PROJECT_NAME = global_val.PROJECT_NAME
CONFIG_VERSION = "2.9.4"


class config:
    _config_dir: Path
    _config_file: Path
    _config: dict | None = None

    @classmethod
    def init(cls):
        if sys.platform == "win32":
            # Windows: C:\Users\<用户名>\AppData\Roaming\<app_name>
            cls._config_dir = Path(os.getenv("APPDATA", ""))
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/<app_name>
            cls._config_dir = (
                Path(os.path.expanduser("~")) / "Library" / "Application Support"
            )
        else:
            # Linux: ~/.config/<app_name>
            cls._config_dir = Path(os.path.expanduser("~")) / ".config"
        cls._config_dir = Path(cls._config_dir) / PROJECT_NAME
        cls._config_file = Path(cls._config_dir) / "config.json"

        if not cls._config_file.is_file():
            cls._config_dir.mkdir(exist_ok=True)
            with cls._config_file.open("wt", encoding="utf-8", newline="\n") as f:
                json.dump(
                    {
                        "version": CONFIG_VERSION,
                        "user_profile": {
                            "language": "auto",
                            "check_update": True,
                            "check_dependent": True,
                            "startup_directory": "",
                            "force_log_file_path": "",
                            "log_print_level": log.LogLevel.send.name,
                            "log_write_level": log.LogLevel.send.name,
                        },
                    },
                    f,
                    ensure_ascii=False,
                    indent=3,
                )
        else:
            with cls._config_file.open("rt", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data.get("version") != CONFIG_VERSION:
                        log.warning(
                            "The config version is not match, use '{}' to regenerate config file",
                            "config clear",
                        )
                except json.JSONDecodeError as e:
                    log.error(f"{e!r} {e}", deep=True)

        cls._read_config()

    @classmethod
    def open_config_dir(cls):
        if not cls._config_dir.is_dir():
            cls.init()
        os.startfile(cls._config_dir)

    @classmethod
    def regenerate_config(cls):
        cls._config_file.unlink(missing_ok=True)

        cls.init()
        log.info("Regenerate config file")

    @classmethod
    def _read_config(cls) -> bool:
        try:
            if not cls._config_dir.is_dir():
                raise AttributeError
        except AttributeError:
            cls.init()

        with cls._config_file.open("rt", encoding="utf-8") as f:
            try:
                cls._config = json.load(f)
            except json.JSONDecodeError as e:
                log.error(f"{e!r} {e}", deep=True)
                return False
            return True

    @classmethod
    def _write_config(cls, new_config: dict | None = None) -> bool:
        if not cls._config_dir.is_dir():
            cls.init()
        if new_config is not None:
            cls._config = new_config
        del new_config

        with cls._config_file.open("wt", encoding="utf-8", newline="\n") as f:
            try:
                json.dump(cls._config, f, ensure_ascii=False, indent=3)
            except json.JSONDecodeError as e:
                log.error(f"{e!r} {e}", deep=True)
                return False
            return True

    @classmethod
    def set_user_profile(cls, key: str, val: str | int | float | bool) -> bool:
        if cls._config is None:
            if not cls._read_config():
                return False

        if cls._config is None:
            log.error("Config is None")
            return False

        if "user_profile" not in cls._config:
            log.error("User profile is not found in config")
            return False

        if key in cls._config["user_profile"]:
            cls._config["user_profile"][key] = val
        else:
            log.error("Key '{}' is not found in user profile", key)
            return False
        return cls._write_config()

    @classmethod
    def get_user_profile(cls, key: str) -> str | int | float | bool | None:
        if cls._config is None:
            cls._read_config()
        if cls._config is None:
            return None
        if not isinstance(cls._config["user_profile"], dict):
            log.error("User profile is not a valid dictionary")
            return None
        if key not in cls._config["user_profile"]:
            log.error("Key '{}' is not found in user profile", key)
            return None
        return cls._config["user_profile"][key]

    @classmethod
    def show_config_list(cls):
        if cls._config is None:
            cls.init()
        if cls._config is None:
            log.error("Config is None")
            return

        user_profile: dict = cls._config["user_profile"]
        length_key = max(len(k) for k in user_profile.keys())
        length_val = max(len(str(v)) for v in user_profile.values())
        for k, v in user_profile.items():
            log.send(
                f"{k:>{length_key}} = {v!s:<{length_val}} - {cls._get_config_about(k)}",
            )

    @classmethod
    def _get_config_about(cls, key: str) -> str:
        return (
            {
                "language": gettext(
                    "Easy Rip's language, support incomplete matching. Support: {}",
                    ", ".join(
                        ("auto", *(str(tag) for tag in all_supported_lang_map.keys()))
                    ),
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
                    "Logs this level and above will be printed, and if the value is '{}', they will not be printed. Support: {}",
                    log.LogLevel.none.name,
                    ", ".join(log.LogLevel._member_names_),
                ),
                "log_write_level": gettext(
                    "Logs this level and above will be written, and if the value is '{}', the '{}' only be written when 'server', they will not be written. Support: {}",
                    log.LogLevel.none.name,
                    log.LogLevel.send.name,
                    ", ".join(log.LogLevel._member_names_),
                ),
            }
            | (cls._config or dict())
        ).get(key, "None about")

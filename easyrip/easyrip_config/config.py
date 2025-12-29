import json
import os
from pathlib import Path
from typing import Literal, get_origin, overload

from ..easyrip_log import log
from ..easyrip_mlang import all_supported_lang_map, gettext
from ..global_val import get_CONFIG_DIR
from ..utils import type_match
from .config_key import CONFIG_TYPE_DICT, CONFIG_VERSION, Config_key

CONFIG_DEFAULT_DICT: dict[Config_key, str | bool | list[str]] = {
    Config_key.language: "auto",
    Config_key.check_update: True,
    Config_key.check_dependent: True,
    Config_key.startup_dir: "",
    Config_key.startup_dir_blacklist: [],
    Config_key.force_log_file_path: "",
    Config_key.log_print_level: log.LogLevel.send.name,
    Config_key.log_write_level: log.LogLevel.send.name,
    Config_key.save_prompt_history: True,
}

assert all(k in CONFIG_DEFAULT_DICT for k in Config_key), [
    k.name for k in Config_key if k not in CONFIG_DEFAULT_DICT
]


class config:
    _config_dir: Path
    _config_file: Path
    _config: dict | None = None

    @classmethod
    def init(cls) -> None:
        cls._config_dir = get_CONFIG_DIR()
        cls._config_file = cls._config_dir / "config.json"

        if not cls._config_file.is_file():
            cls._config_dir.mkdir(exist_ok=True)
            with cls._config_file.open("wt", encoding="utf-8", newline="\n") as f:
                config_default_dict: dict[str, str | bool | list[str]] = {
                    k.name: v for k, v in CONFIG_DEFAULT_DICT.items()
                }
                json.dump(
                    {
                        "version": CONFIG_VERSION,
                        "user_profile": config_default_dict,
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
    def open_config_dir(cls) -> None:
        if not cls._config_dir.is_dir():
            cls.init()
        os.startfile(cls._config_dir)

    @classmethod
    def regenerate_config(cls) -> None:
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
    def set_user_profile(
        cls,
        key: str,
        val: str | bool | list[str],
    ) -> bool:
        if cls._config is None and not cls._read_config():
            return False

        if cls._config is None:
            log.error("Config is None")
            return False

        if "user_profile" not in cls._config:
            log.error("User profile is not found in config file")
            return False

        if key in Config_key._member_map_:
            need_type = CONFIG_TYPE_DICT[Config_key[key]]
            if not type_match(val, need_type):
                log.error(
                    "Type mismatch: need '{}'",
                    need_type if get_origin(need_type) else need_type.__name__,
                )
                return False
            cls._config["user_profile"][key] = val
        else:
            log.error("Key '{}' is not found in user profile", key)
            return False
        return cls._write_config()

    @overload
    @classmethod
    def get_user_profile(
        cls,
        config_key: Literal[
            Config_key.language,
            Config_key.startup_dir,
            Config_key.force_log_file_path,
            Config_key.log_print_level,
            Config_key.log_write_level,
        ],
    ) -> str | None: ...

    @overload
    @classmethod
    def get_user_profile(
        cls,
        config_key: Literal[
            Config_key.check_update,
            Config_key.check_dependent,
            Config_key.save_prompt_history,
        ],
    ) -> bool | None: ...

    @overload
    @classmethod
    def get_user_profile(
        cls,
        config_key: Literal[Config_key.startup_dir_blacklist],
    ) -> list[str] | None: ...

    @overload
    @classmethod
    def get_user_profile(
        cls,
        config_key: str,
    ) -> str | bool | list[str] | None: ...

    @classmethod
    def get_user_profile(
        cls,
        config_key: Config_key | str,
    ) -> str | bool | list[str] | None:
        key = config_key.name if isinstance(config_key, Config_key) else config_key

        if key not in Config_key._member_map_:
            log.error("The key '{}' is not a config", key)
            return None

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
    def show_config_list(cls) -> None:
        if cls._config is None:
            cls.init()
        if cls._config is None:
            log.error("Config is None")
            return

        user_profile: dict = cls._config["user_profile"]
        length_key = max(len(k) for k in user_profile)
        length_val = max(len(str(v)) for v in user_profile.values())
        for k, v in user_profile.items():
            log.send(
                f"{k:>{length_key}} = {v!s:<{length_val}} - {cls._get_config_about(k)}",
            )

    @classmethod
    def _get_config_about(cls, key: str) -> str:
        return (
            {
                Config_key.language.name: gettext(
                    "Easy Rip's language, support incomplete matching. Default: {}. Supported: {}",
                    CONFIG_DEFAULT_DICT[Config_key.language],
                    ", ".join(("auto", *(str(tag) for tag in all_supported_lang_map))),
                ),
                Config_key.check_update.name: gettext(
                    "Auto check the update of Easy Rip. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.check_update],
                ),
                Config_key.check_dependent.name: gettext(
                    "Auto check the versions of all dependent programs. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.check_dependent],
                ),
                Config_key.startup_dir.name: gettext(
                    "Program startup directory, when the value is empty, starts in the working directory. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.startup_dir] or '""',
                ),
                Config_key.startup_dir_blacklist.name: gettext(
                    "Directory list. When the startup directory is a blacklisted directory, rollback to startup directory. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.startup_dir] or '""',
                ),
                Config_key.force_log_file_path.name: gettext(
                    "Force change of log file path, when the value is empty, it is the working directory. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.force_log_file_path] or '""',
                ),
                Config_key.log_print_level.name: gettext(
                    "Logs this level and above will be printed, and if the value is '{}', they will not be printed. Default: {}. Supported: {}",
                    log.LogLevel.none.name,
                    CONFIG_DEFAULT_DICT[Config_key.log_print_level],
                    ", ".join(log.LogLevel._member_names_),
                ),
                Config_key.log_write_level.name: gettext(
                    "Logs this level and above will be written, and if the value is '{}', the '{}' only be written when 'server', they will not be written. Default: {}. Supported: {}",
                    log.LogLevel.none.name,
                    log.LogLevel.send.name,
                    CONFIG_DEFAULT_DICT[Config_key.log_write_level],
                    ", ".join(log.LogLevel._member_names_),
                ),
                Config_key.save_prompt_history.name: gettext(
                    "Save prompt history to config directory, otherwise save to memory. Take effect after reboot. Default: {}",
                    CONFIG_DEFAULT_DICT[Config_key.save_prompt_history],
                ),
            }
            | (cls._config or {})
        ).get(key, "None about")

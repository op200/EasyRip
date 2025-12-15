import enum

CONFIG_VERSION = "4.6.0"


class Config_key(enum.Enum):
    language = enum.auto()
    check_update = enum.auto()
    check_dependent = enum.auto()
    startup_dir = enum.auto()
    startup_dir_blacklist = enum.auto()
    force_log_file_path = enum.auto()
    log_print_level = enum.auto()
    log_write_level = enum.auto()
    save_prompt_history = enum.auto()


CONFIG_TYPE_DICT: dict[Config_key, type] = {
    Config_key.language: str,
    Config_key.check_update: bool,
    Config_key.check_dependent: bool,
    Config_key.startup_dir: str,
    Config_key.startup_dir_blacklist: list[str],
    Config_key.force_log_file_path: str,
    Config_key.log_print_level: str,
    Config_key.log_write_level: str,
    Config_key.save_prompt_history: bool,
}

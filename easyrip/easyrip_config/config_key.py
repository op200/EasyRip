import enum

CONFIG_VERSION = "4.2.0"


class Config_key(enum.Enum):
    language = "language"
    check_update = "check_update"
    check_dependent = "check_dependent"
    startup_directory = "startup_directory"
    force_log_file_path = "force_log_file_path"
    log_print_level = "log_print_level"
    log_write_level = "log_write_level"
    prompt_history_save_file = "prompt_history_file"

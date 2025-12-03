from prompt_toolkit.history import FileHistory

from .global_val import C_Z, CONFIG_DIR


class easyrip_prompt:
    PROMPT_HISTORY_FILE = CONFIG_DIR / "prompt_history.txt"

    @classmethod
    def clear(cls) -> None:
        cls.PROMPT_HISTORY_FILE.unlink(True)


class ConfigFileHistory(FileHistory):
    def store_string(self, string: str) -> None:
        if not string.startswith(C_Z):
            super().store_string(string)

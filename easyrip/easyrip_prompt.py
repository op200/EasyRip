import os
from collections.abc import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory

from .global_val import C_Z, get_CONFIG_DIR


class easyrip_prompt:
    PROMPT_HISTORY_FILE = get_CONFIG_DIR() / "prompt_history.txt"

    @classmethod
    def clear(cls) -> None:
        cls.PROMPT_HISTORY_FILE.unlink(True)


class ConfigFileHistory(FileHistory):
    def store_string(self, string: str) -> None:
        if not string.startswith(C_Z):
            super().store_string(string)


class SmartPathCompleter(Completer):
    def __init__(self) -> None:
        pass

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,  # noqa: ARG002
    ) -> Iterable[Completion]:
        text = document.text_before_cursor.strip("\"'")

        try:
            directory = (
                os.path.dirname(os.path.join(".", text))
                if os.path.dirname(text)
                else "."
            )

            prefix = os.path.basename(text)

            filenames: list[tuple[str, str]] = (
                [
                    (directory, filename)
                    for filename in os.listdir(directory)
                    if filename.startswith(prefix)
                ]
                if os.path.isdir(directory)
                else []
            )

            for directory, filename in sorted(filenames, key=lambda k: k[1]):
                completion = filename[len(prefix) :]
                full_name = os.path.join(directory, filename)

                if os.path.isdir(full_name):
                    filename += "/"

                yield Completion(
                    text=(
                        f'{"" if any(c in text for c in "\\/") else '"'}{completion}"'
                        if any(c in r"""!$%&()*:;<=>?[]^`{|}~""" for c in completion)
                        else completion
                    ),
                    start_position=0,
                    display=filename,
                )

        except OSError:
            pass

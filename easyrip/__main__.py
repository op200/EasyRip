import itertools
import sys
from typing import Final, NoReturn

import Crypto
import fontTools
import prompt_toolkit
from prompt_toolkit import ANSI, prompt
from prompt_toolkit.completion import (
    FuzzyWordCompleter,
    NestedCompleter,
    PathCompleter,
    merge_completers,
)
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from .easyrip_command import Cmd_type, Cmd_type_val, Opt_type
from .easyrip_main import Ripper, get_input_prompt, init, log, run_command


def run() -> NoReturn:
    init(True)

    log.debug(f"Python: v{sys.version}")
    log.debug(f"prompt-toolkit: v{prompt_toolkit.__version__}")
    log.debug(f"fonttools: v{fontTools.__version__}")
    log.debug(f"pycryptodome: v{Crypto.__version__}")

    if len(sys.argv) > 1:
        run_command(sys.argv[1:])
        if len(Ripper.ripper_list) == 0:
            sys.exit(0)

    key_bindings = KeyBindings()

    @key_bindings.add("c-d")
    def _(event) -> None:
        event.app.current_buffer.insert_text("\x04")

    path_completer = PathCompleter()

    def _ctv_to_nc(ctv_tuple: tuple[Cmd_type_val, ...]) -> NestedCompleter:
        return NestedCompleter(
            {
                name: (
                    merge_completers(completer_tuple)
                    if (
                        completer_tuple := (
                            *((_ctv_to_nc(ctv.childs),) if ctv.childs else ()),
                            *(
                                (path_completer,)
                                if name
                                in {
                                    *Cmd_type.cd.value.names,
                                    *Cmd_type.mediainfo.value.names,
                                    *Opt_type._i.value.names,
                                    *Opt_type._o_dir.value.names,
                                    *Opt_type._o.value.names,
                                    *Opt_type._sub.value.names,
                                    *Opt_type._only_mux_sub_path.value.names,
                                    *Opt_type._soft_sub.value.names,
                                    *Opt_type._subset_font_dir.value.names,
                                    *Opt_type._chapters.value.names,
                                }
                                else ()
                            ),
                        )
                    )
                    else None
                )
                for ctv in ctv_tuple
                for name in ctv.names
            }
        )

    all_ctv: Final = tuple(
        ct.value
        for ct in itertools.chain(Cmd_type, Opt_type)
        if ct not in {Cmd_type.Option}
    )
    merged_completer: Final = merge_completers(
        (
            FuzzyWordCompleter(
                words=tuple(name for ctv in all_ctv for name in ctv.names),
                WORD=True,
            ),
            _ctv_to_nc(all_ctv),
        )
    )

    prompt_history = InMemoryHistory()
    while True:
        try:
            command = prompt(
                ANSI(get_input_prompt(is_color=True)),
                key_bindings=key_bindings,
                completer=merged_completer,
                history=prompt_history,
                complete_while_typing=True,
            )
            if command.startswith("\x1a"):
                raise EOFError
            # sys.stdout.flush()
            # sys.stderr.flush()
        except KeyboardInterrupt:
            # print(
            #     f"\033[{91 if log.default_background_color == 41 else 31}m^C\033[{log.default_foreground_color}m\n",
            #     end="",
            # )
            continue
        except EOFError:
            log.debug("Manually force exit")
            sys.exit(0)

        if not run_command(command):
            log.warning("Stop run command")


if __name__ == "__main__":
    run()

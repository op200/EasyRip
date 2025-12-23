import sys
from collections.abc import Coroutine, Iterable
from typing import Any, NoReturn

import Crypto
import fontTools
import prompt_toolkit
from prompt_toolkit import ANSI, prompt
from prompt_toolkit.completion import merge_completers
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input.ansi_escape_sequences import ANSI_SEQUENCES
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.key_binding.bindings import named_commands
from prompt_toolkit.keys import Keys

from .easyrip_command import (
    Cmd_type,
    Cmd_type_val,
    CmdCompleter,
    Opt_type,
    OptCompleter,
    nested_dict,
)
from .easyrip_config.config import Config_key, config
from .easyrip_main import Ripper, get_input_prompt, init, log, run_command
from .easyrip_prompt import ConfigFileHistory, SmartPathCompleter, easyrip_prompt
from .global_val import C_D, C_Z


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

    @key_bindings.add(Keys.ControlC)
    def _(event: KeyPressEvent) -> None:
        event.app.exit(exception=KeyboardInterrupt, style="class:exiting")

    @key_bindings.add(Keys.ControlD)
    def _(event: KeyPressEvent) -> None:
        event.app.current_buffer.insert_text(C_D)

    ANSI_SEQUENCES["\x08"] = Keys.F24

    @key_bindings.add(Keys.F24)
    def _(
        event: KeyPressEvent,
    ) -> object | Coroutine[Any, Any, object]:
        return named_commands.get_by_name("unix-word-rubout").handler(event)

    path_completer = SmartPathCompleter()

    def _ctv_to_nc(ctvs: Iterable[Cmd_type_val]) -> CmdCompleter:
        return CmdCompleter(
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
                                    *Cmd_type.fontinfo.value.names,
                                }
                                else ()
                            ),
                        )
                    )
                    else None
                )
                for ctv in ctvs
                for name in ctv.names
            }
        )

    def _ctv_to_nd(ctvs: Iterable[Cmd_type_val]) -> nested_dict:
        return {
            name: (
                merge_completers(
                    (OptCompleter(opt_tree=_ctv_to_nd(ctv.childs)), path_completer)
                )
                if name
                in {
                    *Opt_type._i.value.names,
                    *Opt_type._o_dir.value.names,
                    *Opt_type._o.value.names,
                    *Opt_type._sub.value.names,
                    *Opt_type._only_mux_sub_path.value.names,
                    *Opt_type._soft_sub.value.names,
                    *Opt_type._subset_font_dir.value.names,
                    *Opt_type._chapters.value.names,
                }
                else _ctv_to_nd(ctv.childs)
            )
            for ctv in ctvs
            for name in ctv.names
        }

    cmd_ctv_tuple = tuple(ct.value for ct in Cmd_type if ct != Cmd_type.Option)
    prompt_history = (
        ConfigFileHistory(easyrip_prompt.PROMPT_HISTORY_FILE)
        if config.get_user_profile(Config_key.save_prompt_history)
        else InMemoryHistory()
    )

    while True:
        try:
            command = prompt(
                ANSI(get_input_prompt(is_color=True)),
                key_bindings=key_bindings,
                completer=merge_completers(
                    (
                        _ctv_to_nc(cmd_ctv_tuple),
                        OptCompleter(opt_tree=_ctv_to_nd(ct.value for ct in Opt_type)),
                    )
                ),
                history=prompt_history,
                complete_while_typing=True,
            )
            if command.startswith(C_Z):
                raise EOFError
        except KeyboardInterrupt:
            continue
        except EOFError:
            log.debug("Manually force exit")
            sys.exit(0)

        try:
            if not run_command(command):
                log.warning("Stop run command")
        except KeyboardInterrupt:
            log.warning("Manually stop run command")


if __name__ == "__main__":
    run()

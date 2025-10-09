import sys
from typing import NoReturn

import Crypto
import fontTools

from .easyrip_main import Ripper, get_input_prompt, init, log, run_command


def run() -> NoReturn:
    init(True)

    log.debug(f"pycryptodome: v{Crypto.__version__}")
    log.debug(f"fonttools: v{fontTools.__version__}")

    Ripper.ripper_list = []

    if len(sys.argv) > 1:
        run_command(sys.argv[1:])
        if len(Ripper.ripper_list) == 0:
            sys.exit()

    while True:
        try:
            command = input(get_input_prompt(is_color=True))
            sys.stdout.flush()
            sys.stderr.flush()
        except KeyboardInterrupt:
            print(
                f"\033[{91 if log.default_background_color == 41 else 31}m^C\033[{log.default_foreground_color}m"
            )
            continue
        except EOFError:
            log.debug("Manually force exit")
            sys.exit()

        if not run_command(command):
            log.warning("Stop run command")


run()

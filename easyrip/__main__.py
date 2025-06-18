import sys

from .easyrip_main import init, run_command, Ripper, log, get_input_prompt


def run():
    init(True)

    Ripper.ripper_list = []

    if len(sys.argv) > 1:
        run_command(sys.argv[1:])
        if len(Ripper.ripper_list) == 0:
            sys.exit()

    while True:
        try:
            command = input(get_input_prompt())
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            log.info("Manually force exit")
            sys.exit()
        except KeyboardInterrupt:
            print(
                f"\033[{91 if log.default_background_color == 41 else 31}m^C\033[{log.default_foreground_color}m"
            )
            continue

        if not run_command(command):
            log.warning("Stop run command")


run()

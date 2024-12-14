import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shlex
import re

from easyrip_log import log
from ripper import Ripper


os.system('title Easy Rip')

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    log.warning("Windows DPI Aware failed")



PROJECT_NAME = "Easy Rip"
PROJECT_VERSION = "0.3.1"
PROJECT_URL = "https://github.com/op200/EasyRip"


def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def run_ripper_list(is_exit_when_runned: bool = False):
    total = len(Ripper.ripper_list)
    for i, ripper in enumerate(Ripper.ripper_list):
        progress = f'{i+1} / {total} in Easy Rip'
        log.info(progress)
        os.system('title ' + progress)
        ripper.run()
    Ripper.ripper_list = []

    if is_exit_when_runned:
        sys.exit()

    os.system('title End in Easy Rip')


def run_command(cmd_list: list[str]) -> bool:

    os.system('title Easy Rip')

    cmd_list.append('')

    if cmd_list[0] == "help":

        print(
            f"{PROJECT_NAME}\nVersion: {PROJECT_VERSION}\n{PROJECT_URL}\n"
            "\n"
            "Help:\n"
            "  You can input command or use the argument value to run\n"
            "\n"
            "Commands:\n"
            "  help\n"
            "    Show help\n"
            "  exit\n"
            "    Exit this program\n"
            "  cd <string>\n"
            "    Change current path\n"
            "  cls / clear\n"
            "    Clear screen\n"
            "  list\n"
            "    Show ripper list\n"
            "  clear list\n"
            "    Clear ripper list\n"
            "  run\n"
            "    Run ripper list\n"
            "  <Option>\n"
            "    -i <input> -o <output> -preset <preset name> [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-run [<run option>]]\n"
            "      Add a new ripper to the ripper list, you can set the values of the options in preset individually, you can run ripper list when use -run\n"
            "\n"
            "Easy Rip options:\n"
            "  -i <string | 'fd'>\n"
            "    Input file's pathname or use file dialog\n"
            "  -o <string>\n"
            "    Output file's basename\n"
            "  -preset <string>\n"
            "    Preset name:\n"
            "      flac\n"
            "      x264sub\n"
            "      x265veryfastsub x265fast x265slow x265full\n"
            "  -pipe <string>\n"
            "    Select a vpy file as pipe to input, this vpy must can input\n"
            "    The input in vspipe: vspipe -a input=<input> xxx.vpy\n"
            "  -sub <string>\n"
            "    It makes libass work correctly, input a subtitle pathname when you need hard subtitle\n"
            "    If you are not using it when you use hard subtitle preset, program will error\n"
            "  -run [<string>]\n"
            "    Run the ripper in the ripper list\n"
            "    Default:\n"
            "      Only run\n"
            "    exit:\n"
            "      Close program when runned\n"
            "\n"
            "Codec options:\n"
            "    -hwaccel <string>\n"
            "      Use FFmpeg hwaccel (See 'ffmpeg -hwaccels' for details)\n"
            "    -deinterlacing <bool 0..1>\n"
            "      Use the filter yadif to deinterlacing\n"
        )


    elif cmd_list[0] == "exit":
        sys.exit()


    elif cmd_list[0] == "cd":
        os.chdir(cmd_list[1])


    elif cmd_list[0] in ("cls", "clear") and cmd_list[1] == '':
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')


    elif cmd_list[0] == "list":
        print(f'ripper list ({len(Ripper.ripper_list)}):')
        for i, ripper in enumerate(Ripper.ripper_list):
            print(f'  {i+1}.\n  {ripper}\n  {log.hr}')


    elif cmd_list[0] == "clear" and cmd_list[1] == "list":
        Ripper.ripper_list = []


    elif cmd_list[0] == "run":
        run_ripper_list(cmd_list[1] == 'exit')


    else:

        input_pathname_list = []
        output_basename = None
        preset_name = None
        vpy_pathname = None
        subtitle_pathname = None
        option_map = {}
        is_run = False
        is_exit_when_runned = False

        for i in range(0, len(cmd_list)):

            if cmd_list[i] == '-i':
                if cmd_list[i+1] == 'fd':
                    input_pathname_list += file_dialog()
                else:
                    input_pathname_list.append(cmd_list[i+1])

            if cmd_list[i] == '-o':
                output_basename = cmd_list[i+1]
                if re.search(r'[<>:"/\\|?*]', output_basename):
                    log.error(f'Illegal char in -o "{output_basename}"')
                    return False

            if cmd_list[i] == '-preset':
                preset_name = cmd_list[i+1]

            if cmd_list[i] == '-pipe':
                vpy_pathname = cmd_list[i+1]

            if cmd_list[i] == '-sub':
                subtitle_pathname = cmd_list[i+1]

            if cmd_list[i] == '-run':
                is_run = True
                if cmd_list[i+1] == 'exit':
                    is_exit_when_runned = True

            elif match := re.search(r'\-(.+)', cmd_list[i]):
                option_map[match.group(1)] = cmd_list[i+1]

        if not preset_name:
            log.error("Missing -preset")
            return False

        option_map['pipe'] = vpy_pathname
        option_map['sub'] = subtitle_pathname
        for input_pathname in input_pathname_list:
            Ripper.ripper_list.append(Ripper(
                input_pathname, output_basename, preset_name, option_map))


        if is_run:
            run_ripper_list(is_exit_when_runned)

    return True



if __name__ == "__main__":

    Ripper.ripper_list = []

    if sys.argv[1:] != []:
        run_command(sys.argv[1:])

    while True:
        try:
            command = input(f'{os.getcwd()}> Easy Rip command>')
        except:
            log.info("Manually force exit")
            sys.exit()
        if not run_command([cmd.replace('\\\\', '\\') for cmd in shlex.split(command, posix=False)]):
            log.warning('Stop run command')


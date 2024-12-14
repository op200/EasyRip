import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shlex
import re

from easy_rip_log import log
from ripper import Ripper


try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    log.warning("Windows DPI Aware failed")

root = tk.Tk()
root.withdraw()


PROJECT_NAME = "Easy Rip"
PROJECT_VERSION = "0.2"
PROJECT_URL = "https://github.com/op200/"


def file_dialog():
    file_paths = filedialog.askopenfilenames()
    root.destroy()
    return file_paths


def run_command(cmd_list: list[str]):

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
            "  list\n"
            "    Show ripper list\n"
            "  <Option>\n"
            "    -i <input> -o <output> -preset <preset name> [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-run [<run option>]]\n"
            "      Add a new ripper to the ripper list, you can set the values of the options in preset individually, you can run ripper list when use -run\n"
            "    -run [<run option>]\n"
            "      Run ripper list\n"
            "\n"
            "Options:\n"
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
        )


    elif cmd_list[0] == "list":

        print('ripper list:')
        for ripper in Ripper.ripper_list:
            print(f'  {ripper}')


    else:

        input_pathname_list = []
        output_basename = None
        preset_name = None
        vpy_pathname = None
        subtitle_pathname = None
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
                    log.error(f'Illegal character in -o {output_basename}')
                    sys.exit()

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

        if not preset_name:
            log.error("Missing -preset")
            return

        for input_pathname in input_pathname_list:
            Ripper.ripper_list.append(Ripper(
                input_pathname, output_basename, preset_name,
                {'pipe': vpy_pathname, 'sub': subtitle_pathname}))


        if is_run:

            for ripper in Ripper.ripper_list:
                ripper.run()
            Ripper.ripper_list = []

            if is_exit_when_runned:
                sys.exit()


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
        run_command(shlex.split(command))


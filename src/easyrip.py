import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shlex
import re
from threading import Thread

from easyrip_log import log, print
from ripper import Ripper



PROJECT_NAME = "Easy Rip"
PROJECT_VERSION = "1.0"
PROJECT_TITLE = f'{PROJECT_NAME} v{PROJECT_VERSION}'
PROJECT_URL = "https://github.com/op200/EasyRip"


os.system(f'title {PROJECT_TITLE}')

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    log.warning("Windows DPI Aware failed")



def get_input_prompt():
    return f'{os.getcwd()}> Easy Rip command>'


def check_evn():

    if os.system('ffmpeg -version > nul 2> nul'):
        print()
        log.warning('FFmpeg not found')
        print(get_input_prompt(), end='')

    # elif os.system('ffmpeg -version | findstr "/C:ffmpeg version 7.1-full" > nul'):
    #     print()
    #     log.warning('FFmpeg version is not 7.1-full')
    #     print(get_input_prompt(), end='')


    if os.system('flac -v > nul 2> nul'):
        print()
        log.warning('flac not found')
        print(get_input_prompt(), end='')

    # elif os.system('flac -v | findstr "/C:flac 1.4.3" > nul'):
    #     print()
    #     log.warning('flac version is not 1.4.3')
    #     print(get_input_prompt(), end='')


    if os.system('mp4box -version > nul 2> nul'):
        print()
        log.warning('MP4Box not found')
        print(get_input_prompt(), end='')

    # elif os.system('mp4box -version 2>&1 | findstr "/C:MP4Box - GPAC version 2.4" > nul'):
    #     print()
    #     log.warning('MP4Box version is not GPAC 2.4')
    #     print(get_input_prompt(), end='')


    if os.system('mkvpropedit --version > nul 2> nul'):
        print()
        log.warning('mkvpropedit not found')
        print(get_input_prompt(), end='')


    if os.system('mkvmerge --version > nul 2> nul'):
        print()
        log.warning('mkvmerge not found')
        print(get_input_prompt(), end='')


def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def run_ripper_list(is_exit_when_runned: bool = False):
    total = len(Ripper.ripper_list)
    for i, ripper in enumerate(Ripper.ripper_list):
        progress = f'{i+1} / {total} - {PROJECT_TITLE}'
        log.info(progress)
        os.system(f'title {progress}')
        try:
            ripper.run()
        except Exception as e:
            log.error(e)
            log.warning('Stop run ripper')
    Ripper.ripper_list = []

    if is_exit_when_runned:
        sys.exit()

    os.system(f'title End - {PROJECT_TITLE}')
    log.info('Run completed')


def run_command(cmd_list: list[str] | str) -> bool:

    if type(cmd_list) is str:
        cmd_list = [cmd_list]

    if len(cmd_list) == 0:
        return True

    os.system(f'title {PROJECT_TITLE}')

    cmd_list.append('')

    if cmd_list[0] in ('h', 'help'):

        print(
            f"{PROJECT_NAME}\nVersion: {PROJECT_VERSION}\n{PROJECT_URL}\n"
            "\n"
            "Help:\n"
            "  You can input command or use the argument value to run\n"
            "\n"
            "Commands:\n"
            "  h / help\n"
            "    Show help\n"
            "  v / version\n"
            "    Show version\n"
            "  $ <code>\n"
            "    Run code directly from the internal environment\n"
            "    Execute the code string directly after the $\n"
            '    The string "\\N" will be changed to real "\\n"\n'
            "  exit\n"
            "    Exit this program\n"
            "  cd <string>\n"
            "    Change current path\n"
            "  cls / clear\n"
            "    Clear screen\n"
            "  list <list option>\n"
            "    Operate ripper list\n"
            "    Default:\n"
            "      Show ripper list\n"
            "    clear / clean:\n"
            "      Clear ripper list\n"
            "    del / pop <index>:\n"
            "      Delete a ripper from ripper list\n"
            "  run [<run option>]\n"
            "    Run the ripper in the ripper list\n"
            "    Default:\n"
            "      Only run\n"
            "    exit:\n"
            "      Close program when runned\n"
            "  <Option>\n"
            "    -i <input> -o <output> -preset <preset name> [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-c:a <audio codec> -b:a <audio bitrate>] [-muxer <muxer> [-r <fps>]] [-run [<run option>]]\n"
            "      Add a new ripper to the ripper list, you can set the values of the options in preset individually, you can run ripper list when use -run\n"
            "\n"
            "Easy Rip options:\n"
            "  -i <string | 'fd'>\n"
            "    Input file's pathname or use file dialog\n"
            "  -o <string>\n"
            "    Output file's basename\n"
            "  -preset <string>\n"
            "    Preset name:\n"
            "      custom\n"
            "      flac\n"
            "      x264sub\n"
            "      x265veryfastsub x265fast x265slow x265full\n"
            "  -pipe <string>\n"
            "    Select a vpy file as pipe to input, this vpy must can input\n"
            "    The input in vspipe: vspipe -a input=<input> xxx.vpy\n"
            "  -sub <string>\n"
            "    It makes libass work correctly, input a subtitle pathname when you need hard subtitle\n"
            "    If you are not using it when you use hard subtitle preset, program will error\n"
            "  -c:a <string>\n"
            "    Audio encoder:\n"
            "      copy\n"
            "      libopus\n"
            "  -b:a <string>\n"
            "    Setting audio bitrate. Default '160k'\n"
            "  -muxer <string>\n"
            "    Muxer:\n"
            "      mp4\n"
            "      mkv\n"
            "  -r / -fps <string>\n"
            "    Setting FPS when muxing\n"
            "  -custom:format / -custom:template <string>\n"
            "    When -preset custom, this option will run\n"
            "    The string \\34/ -> \", \\39/ -> '\n"
            "  -custom:suffix <string>\n"
            "    When -preset custom, this option will be used as a suffix for the output\n"
            "    Default: mkv\n"
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


    elif cmd_list[0] in ('v', 'version'):
        print(f'{PROJECT_NAME} version {PROJECT_VERSION}')


    elif cmd_list[0][0] == "$":
        try:
            exec(' '.join(cmd_list)[1:].lstrip().replace(r"\N","\n"))
        except Exception as e:
            log.error("Your input command has error:")
            print(repr(e))


    elif cmd_list[0] == "exit":
        sys.exit()


    elif cmd_list[0] == "cd":
        try:
            os.chdir(cmd_list[1])
        except OSError as e:
            log.error(e)


    elif cmd_list[0] in ('cls', 'clear') and cmd_list[1] == '':
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')


    elif cmd_list[0] == "list":
        if cmd_list[1] in ('clear', 'clean'):
            Ripper.ripper_list = []
        elif cmd_list[1] in ('del', 'pop'):
            try:
                del Ripper.ripper_list[int(cmd_list[2])-1]
            except Exception as e:
                log.error(e)
            else:
                log.info(f'Delete the {cmd_list[2]}th ripper success')
        else:
            print(f'ripper list ({len(Ripper.ripper_list)}):')
            for i, ripper in enumerate(Ripper.ripper_list):
                print(f'  {i+1}.\n  {ripper}\n  {log.hr}')


    elif cmd_list[0] == "clear" and cmd_list[1] == "list":
        log.warning("'clear list' is deprecated, you should use 'list clear', see 'help' for details")
        Ripper.ripper_list = []


    elif cmd_list[0] == "run":
        run_ripper_list(cmd_list[1] == 'exit')


    else:

        input_pathname_list = []
        output_basename = None
        output_dir = None
        preset_name = None
        vpy_pathname = None
        subtitle_pathname = None
        audio_codec = None
        audio_bitrate = None
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

            if cmd_list[i] == '-o:dir':
                output_dir = cmd_list[i+1]
                if not os.path.isdir(output_dir):
                    log.error(f'The directory "{output_dir}" does not exist')
                    return False

            if cmd_list[i] == '-preset':
                preset_name = cmd_list[i+1]

            if cmd_list[i] == '-pipe':
                vpy_pathname = cmd_list[i+1]

            if cmd_list[i] == '-sub':
                subtitle_pathname = cmd_list[i+1]

            if cmd_list[i] == '-c:a':
                audio_codec = cmd_list[i+1]

            if cmd_list[i] == '-b:a':
                audio_bitrate = cmd_list[i+1]

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
        option_map['c:a'] = audio_codec
        option_map['b:a'] = audio_bitrate
        try:
            for input_pathname in input_pathname_list:
                if not os.path.exists(input_pathname):
                    log.warning(f'The file "{input_pathname}" does not exist')
                Ripper.ripper_list.append(Ripper(
                    input_pathname, output_basename, output_dir, preset_name, option_map))
        except KeyError as e:
            log.error(f'Unsupported option: {e}')
            return False


        if is_run:
            run_ripper_list(is_exit_when_runned)

    return True



if __name__ == "__main__":

    Thread(target=check_evn).start()

    Ripper.ripper_list = []

    if sys.argv[1:] != []:
        run_command(sys.argv[1:])

    while True:
        try:
            command = input(get_input_prompt())
        except:
            log.info("Manually force exit")
            sys.exit()

        try:
            cmd_list = [cmd.strip('"').strip("'").replace('\\\\', '\\')
                        for cmd in shlex.split(command, posix=False)]
        except ValueError as e:
            cmd_list = None
            log.error(e)
        if cmd_list == None or not run_command(cmd_list):
            log.warning('Stop run command')


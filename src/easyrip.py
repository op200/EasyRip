import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shutil
import shlex
import re
from threading import Thread
from itertools import zip_longest

from global_val import GlobalVal
from easyrip_log import log, print, Event as LogEvent
from ripper import Ripper
from easyrip_mlang import GlobalLangVal, get_system_language, gettext, Event as MlangEvent
import easyrip_web


PROJECT_NAME = GlobalVal.PROJECT_NAME
__version__ = PROJECT_VERSION = GlobalVal.PROJECT_VERSION
PROJECT_TITLE = GlobalVal.PROJECT_TITLE
PROJECT_URL = GlobalVal.PROJECT_URL


MlangEvent.log = easyrip_web.http_server.Event.log = log


def change_title(title):
    if os.name == 'nt':
        os.system(f'title {title}')
    elif os.name == 'posix':
        sys.stdout.write(f'\x1b]2;{title}\x07')
        sys.stdout.flush()


change_title(PROJECT_TITLE)


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

    # elif os.system('flac -v | findstr "/C:flac 1.5.0" > nul'):
    #     print()
    #     log.warning('flac version is not 1.5.0')
    #     print(get_input_prompt(), end='')


    if not shutil.which('mp4fpsmod'):
        print()
        log.warning('mp4fpsmod not found')
        print(get_input_prompt(), end='')


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


    if new_ver_str := easyrip_web.get_easyrip_ver():
        new_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", new_ver_str).split(".")]
        new_ver_add_num = [v for v in str(new_ver[-1]).split("+")]
        new_ver = (
            [int(v) for v in (*new_ver[:-1], new_ver_add_num[0])],
            [int(v) for v in new_ver_add_num[1:]]
        )

        old_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", PROJECT_VERSION).split(".")]
        old_ver_add_num = [v for v in str(old_ver[-1]).split("+")]
        old_ver = (
            [int(v) for v in (*old_ver[:-1], old_ver_add_num[0])],
            [int(v) for v in old_ver_add_num[1:]]
        )

        for i in range(2):
            for new, old in zip_longest(new_ver[i], old_ver[i], fillvalue=0):
                if new > old:
                    print()
                    log.info(GlobalLangVal.ExtraTextIndex.NEW_VER_TIP, new_ver_str)
                    print(get_input_prompt(), end='')
                    break
                elif new < old:
                    break
            else:
                continue
            break


if __name__ == "__main__":
    GlobalLangVal.gettext_target_lang = get_system_language() # 获取系统语言

    Thread(target=check_evn).start()


if os.name == 'nt':
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:  # noqa: E722
        log.warning("Windows DPI Aware failed")


def get_input_prompt():
    return f'{os.getcwd()}> {gettext("Easy Rip command")}>'
get_input_prompt()

def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def run_ripper_list(is_exit_when_runned: bool = False, shutdow_sec_str: str | None = None):

    shutdown_sec: int | None = None
    if shutdow_sec_str is not None:
        try:
            shutdown_sec = int(shutdow_sec_str)
        except ValueError:
            log.warning('Wrong sec in -shutdown, change to default 60s')
            shutdown_sec = 60

    total = len(Ripper.ripper_list)
    for i, ripper in enumerate(Ripper.ripper_list):
        progress = f'{i+1} / {total} - {PROJECT_TITLE}'
        log.info(progress)
        change_title(progress)
        try:
            ripper.run()
        except Exception as e:
            log.error(e)
            log.warning("Stop run ripper")
    Ripper.ripper_list = []

    if shutdown_sec:
        if os.name == 'nt':
            os.system(f"shutdown -s -t {shutdown_sec}")
        elif os.name == 'posix':
            os.system(f"shutdown -h +{shutdown_sec // 60}")

    if is_exit_when_runned:
        sys.exit()

    change_title(f'End - {PROJECT_TITLE}')
    log.info("Run completed")


def run_command(command: list[str] | str) -> bool:

    if type(command) is list:
        cmd_list = command

    elif type(command) is str:
        try:
            cmd_list = [cmd.strip('"').strip("'").replace('\\\\', '\\')
                        for cmd in shlex.split(command, posix=False)]
        except ValueError as e:
            log.error(e)
            return False

    if len(cmd_list) == 0:
        return True

    change_title(PROJECT_TITLE)

    cmd_list.append('')

    match cmd_list[0]:

        case "h" | "help":
            print(gettext(GlobalLangVal.ExtraTextIndex.HELP_DOC), file=sys.stdout)
            if cmd_list[1] == 'exit':
                sys.exit()


        case "v" | "ver" | "version":
            print(f'{PROJECT_NAME} version {PROJECT_VERSION}\n{PROJECT_URL}', file=sys.stdout)

            if cmd_list[1] == 'exit':
                sys.exit()


        case "log":
            msg = ' '.join(cmd_list[2:])
            match cmd_list[1]:
                case "info":
                    log.info(msg)
                case "warning" | "warn":
                    log.warning(msg)
                case "error" | "err":
                    log.error(msg)
                case _:
                    log.info(f"{cmd_list[1]} {msg}")


        case str() as s if s[0] == '$':
            try:
                exec(' '.join(cmd_list)[1:].lstrip().replace(r"\N","\n"))
            except Exception as e:
                log.error("Your input command has error:\n{}", e)


        case "exit":
            sys.exit()


        case "cd":
            try:
                os.chdir(cmd_list[1])
            except OSError as e:
                log.error(e)


        case "dir":
            files = os.listdir(os.getcwd())
            for f in files:
                print(f)
            log.http_send('', ' | '.join(files))


        case "cls" | "clear":
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')


        case "list":
            if cmd_list[1] in {'clear', 'clean'}:
                Ripper.ripper_list = []
            elif cmd_list[1] in {'del', 'pop'}:
                try:
                    del Ripper.ripper_list[int(cmd_list[2])-1]
                except Exception as e:
                    log.error(e)
                else:
                    log.info('Delete the {}th ripper success', cmd_list[2])
            else:
                print(f'ripper list ({len(Ripper.ripper_list)}):')
                for i, ripper in enumerate(Ripper.ripper_list):
                    print(f'  {i+1}.\n  {ripper}\n  {log.hr}')


        case "run":
            run_ripper_list(cmd_list[1] == 'exit', cmd_list[2] or '60' if cmd_list[1] == 'shutdown' else None)


        case "server":
            if easyrip_web.http_server.Event.is_run_command:
                log.error("Can not start multiple services")
                return False
            cmd_list.extend([None] * 4)
            easyrip_web.run_server(cmd_list[1], int(cmd_list[2]), cmd_list[3])


        case _:

            input_pathname_list = []
            output_basename = None
            output_dir = None
            preset_name = None
            option_map = {}
            is_run = False
            is_exit_when_runned = False
            shutdown_sec_str: str | None = None

            _skip:bool = False
            for i in range(0, len(cmd_list)):

                if _skip:
                    _skip = False
                    continue

                _skip = True

                if cmd_list[i] == '-i':
                    if cmd_list[i+1] == 'fd':
                        input_pathname_list += file_dialog()
                    else:
                        input_pathname_list.append(cmd_list[i+1])

                elif cmd_list[i] == '-o':
                    output_basename = cmd_list[i+1]
                    if re.search(r'[<>:"/\\|?*]', output_basename):
                        log.error('Illegal char in -o "{}"',output_basename)
                        return False

                elif cmd_list[i] == '-o:dir':
                    output_dir = cmd_list[i+1]
                    if not os.path.isdir(output_dir):
                        log.error('The directory "{}" does not exist', output_dir)
                        return False

                elif cmd_list[i] == '-preset':
                    preset_name = cmd_list[i+1]

                elif cmd_list[i] == '-run':
                    is_run = True
                    if cmd_list[i+1] == 'exit':
                        is_exit_when_runned = True
                    elif cmd_list[i+1] == 'shutdown':
                        shutdown_sec_str = cmd_list[i+2] or '60'
                    else:
                        _skip = False

                elif match := re.search(r'^\-(.+)', cmd_list[i]):
                    option_map[match.group(1)] = cmd_list[i+1]

                else:
                    _skip = False

            if not preset_name:
                log.error("Missing -preset")
                return False

            try:
                if len(input_pathname_list) == 0:
                    log.warning("Input file number == 0")
                    return False

                for input_pathname in input_pathname_list:
                    if not os.path.exists(input_pathname):
                        log.warning('The file "{}" does not exist', input_pathname)

                    if sub_map := option_map.get('sub'):
                        sub_map: str
                        sub_list: list[str]
                        
                        if sub_map == 'auto':
                            sub_list = []

                            _input_basename = os.path.splitext(os.path.basename(input_pathname))
                            while _input_basename[1] != '':
                                _input_basename = os.path.splitext(_input_basename[0])
                            _input_prefix: str = _input_basename[0]

                            _dir = output_dir or os.getcwd()
                            for _file_basename in os.listdir(_dir):
                                if os.path.splitext(_file_basename)[1] in {'.ass', '.ssa'} and _file_basename.startswith(f'{_input_prefix}.'):
                                    sub_list.append(os.path.join(_dir, _file_basename))

                        else:
                            sub_list = sub_map.split('::')

                        sub_list_len = len(sub_list)
                        if sub_list_len > 1:
                            for sub_path in sub_list:
                                _new_option_map = option_map.copy()
                                _new_option_map['sub'] = sub_path

                                Ripper.ripper_list.append(Ripper(
                                    input_pathname,
                                    f'{output_basename}.{os.path.splitext(os.path.basename(sub_path))[0]}',
                                    output_dir,
                                    preset_name,
                                    _new_option_map))

                        elif sub_list_len == 0:
                            log.warning("No subtitle file exist as -sub auto when -i {} -o:dir {}", input_pathname, output_dir or os.getcwd())

                        else:
                            _new_option_map = option_map.copy()
                            _new_option_map['sub'] = sub_list[0]
                            Ripper.ripper_list.append(Ripper(
                                input_pathname,
                                output_basename,
                                output_dir,
                                preset_name,
                                _new_option_map))

                    else:
                        Ripper.ripper_list.append(Ripper(
                            input_pathname,
                            output_basename,
                            output_dir,
                            preset_name,
                            option_map))

            except KeyError as e:
                log.error('Unsupported option: {}', e)
                return False


            if is_run:
                run_ripper_list(is_exit_when_runned, shutdown_sec_str)

    easyrip_web.http_server.Event.is_run_command = False

    return True



if __name__ == "__main__":

    LogEvent.append_http_server_log_queue = lambda message: easyrip_web.http_server.Event.log_queue.append(message)
    easyrip_web.http_server.Event.post_event = lambda cmd: run_command(cmd)
    
    Ripper.ripper_list = []

    if sys.argv[1:] != []:
        run_command(sys.argv[1:])

    while True:
        try:
            command = input(get_input_prompt())
        except:  # noqa: E722
            log.info("Manually force exit")
            sys.exit()

        if not run_command(command):
            log.warning("Stop run command")


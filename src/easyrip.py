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
import subprocess

from global_val import GlobalVal
from easyrip_log import log, print, Event as LogEvent
from ripper import Ripper
from easyrip_mlang import GlobalLangVal, get_system_language, gettext, Event as MlangEvent
import easyrip_web


__all__ = ["init", "run_command", "log", "Ripper"]


PROJECT_NAME = GlobalVal.PROJECT_NAME
__version__ = PROJECT_VERSION = GlobalVal.PROJECT_VERSION
PROJECT_TITLE = GlobalVal.PROJECT_TITLE
PROJECT_URL = GlobalVal.PROJECT_URL



def change_title(title):
    if os.name == 'nt':
        os.system(f'title {title}')
    elif os.name == 'posix':
        sys.stdout.write(f'\x1b]2;{title}\x07')
        sys.stdout.flush()


def check_ver(new_ver_str: str, old_ver_str: str) -> bool:
    new_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", new_ver_str).split(".")]
    new_ver_add_num = [v for v in str(new_ver[-1]).split("+")]
    new_ver = (
        [int(v) for v in (*new_ver[:-1], new_ver_add_num[0])],
        [int(v) for v in new_ver_add_num[1:]]
    )

    old_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", old_ver_str).split(".")]
    old_ver_add_num = [v for v in str(old_ver[-1]).split("+")]
    old_ver = (
        [int(v) for v in (*old_ver[:-1], old_ver_add_num[0])],
        [int(v) for v in old_ver_add_num[1:]]
    )

    for i in range(2):
        for new, old in zip_longest(new_ver[i], old_ver[i], fillvalue=0):
            if new > old:
                return True
            elif new < old:
                break
        else:
            continue
        break
    return False


def log_new_ver(new_ver: str | None, old_ver: str, program_name: str, dl_url: str):
    if new_ver is None:
        return
    try:
        if check_ver(new_ver, old_ver):
            print()
            log.info(GlobalLangVal.ExtraTextIndex.NEW_VER_TIP,
                     program_name, new_ver, dl_url)
            print(get_input_prompt(), end='')
    except Exception as e:
        log.warning(e)


def check_evn():

    _name, _url = 'FFmpeg', 'https://ffmpeg.org/download.html'
    if not shutil.which(_name):
        print()
        log.error('{} not found, download it: {}', _name, f'(full build ver) {_url}')
        print(get_input_prompt(), end='')
    else:
        log_new_ver(
            '7.1',
            subprocess.run('ffmpeg -version', capture_output=True, text=True).stdout.split(maxsplit=3)[2].split('_')[0],
            _name, _url)


    _name, _url = 'flac', 'https://github.com/xiph/flac/releases'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, f'(ver >= 1.5.0) {_url}')
        print(get_input_prompt(), end='')

    elif check_ver('1.5.0', (old_ver_str:=subprocess.run('flac -v', capture_output=True, text=True).stdout.split()[1])):
        log.error("flac ver ({}) must >= 1.5.0", old_ver_str)

    else:
        log_new_ver(
            easyrip_web.get_github_api_ver("https://api.github.com/repos/xiph/flac/releases/latest"),
            old_ver_str,
            _name, _url)


    _name, _url = 'mp4fpsmod', 'https://github.com/nu774/mp4fpsmod/releases'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, _url)
        print(get_input_prompt(), end='')
    else:
        log_new_ver(
            easyrip_web.get_github_api_ver("https://api.github.com/repos/nu774/mp4fpsmod/releases/latest"),
            subprocess.run(_name, capture_output=True, text=True).stderr.split(maxsplit=2)[1],
            _name, _url)


    _name, _url = 'MP4Box', 'https://gpac.io/downloads/gpac-nightly-builds/'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, _url)
        print(get_input_prompt(), end='')
    else:
        log_new_ver(
            '2.5',
            subprocess.run('mp4box -version', capture_output=True, text=True).stderr.split('-', 2)[1].strip().split()[2],
            _name, _url)


    _name, _url = 'mkvpropedit', 'https://mkvtoolnix.download/downloads.html'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, _url)
        print(get_input_prompt(), end='')
    else:
        log_new_ver(
            '90',
            subprocess.run('mkvpropedit --version', capture_output=True, text=True).stdout.split(maxsplit=2)[1],
            _name, _url)


    _name = 'mkvmerge'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, _url)
        print(get_input_prompt(), end='')
    else:
        log_new_ver(
            '90',
            subprocess.run('mkvmerge --version', capture_output=True, text=True).stdout.split(maxsplit=2)[1],
            _name, _url)


    _name, _url = 'MediaInfo', 'https://mediaarea.net/en/MediaInfo/Download'
    if not shutil.which(_name):
        print()
        log.warning('{} not found, download it: {}', _name, f'(CLI ver) {_url}')
        print(get_input_prompt(), end='')
    elif not subprocess.run('mediainfo --version', capture_output=True, text=True).stdout:
        log.error("The MediaInfo must be CLI ver")


    log_new_ver(
        easyrip_web.get_github_api_ver(GlobalVal.PROJECT_RELEASE_API),
        PROJECT_VERSION, PROJECT_NAME,
        GlobalVal.PROJECT_RELEASE_URL)


def get_input_prompt():
    return f'{os.getcwd()}> {gettext("Easy Rip command")}>'


if os.name == 'nt':
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:  # noqa: E722
        log.warning("Windows DPI Aware failed")


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

    if isinstance(command, list):
        cmd_list = command

    elif isinstance(command, str):
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


        case str() as s if len(s) > 0 and s[0] == '$':
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


        case "mkdir" | "makedir":
            try:
                os.makedirs(cmd_list[1])
            except Exception as e:
                log.warning(e)


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
                msg = f'ripper list ({len(Ripper.ripper_list)}):'
                if Ripper.ripper_list:
                    msg += '\n' + f'\n  {log.hr}\n'.join([f'  {i+1}.\n  {ripper}' for i, ripper in enumerate(Ripper.ripper_list)])
                log.http_send('', msg, is_format=False)


        case "run":
            run_ripper_list(cmd_list[1] == 'exit', cmd_list[2] or '60' if cmd_list[1] == 'shutdown' else None)


        case "server":
            if easyrip_web.http_server.Event.is_run_command[-1]:
                log.error("Can not start multiple services")
                return False

            address, password = None, None

            for i in range(1, len(cmd_list)):
                match cmd_list[i]:
                    case '-a' | '-address':
                        address = cmd_list[i+1]
                    case '-p' | 'password':
                        password = cmd_list[i+1]
                    case _:
                        if address is None:
                            address = cmd_list[i]
                        elif password is None:
                            password = cmd_list[i]
            if address:
                res = re.match(
                    r"^([a-zA-Z0-9.-]+)(:(\d+))?$",
                    address,
                )
                if res:
                    host = res.group(1)
                    port = res.group(2)
                    if port:
                        port = int(port)
                    elif host.isdigit():
                        port = int(host)
                        host = None
                    else:
                        port = None
                        host = None
                else:
                    host, port = "localhost", 0
            else:
                host, port = "localhost", 0

            easyrip_web.run_server(host=host or "",port=port or 0, password=password)


        case _:

            input_pathname_list = []
            output_basename = None
            output_dir = None
            preset_name = None
            option_map: dict[str, str] = {}
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
                        if easyrip_web.http_server.Event.is_run_command:
                            log.error("Disable the use of 'fd' on the web")
                            return False
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

    return True


def init():
    new_path = os.getcwd()
    if os.pathsep in (current_path := os.environ.get("PATH", "")):
        if new_path not in current_path.split(os.pathsep):
            updated_path = f"{new_path}{os.pathsep}{current_path}"
            os.environ["PATH"] = updated_path

    change_title(PROJECT_TITLE)

    log.html_log_file = gettext("encoding_log.html")
    MlangEvent.log = easyrip_web.http_server.Event.log = log # type: ignore

    GlobalLangVal.gettext_target_lang = get_system_language()
    Thread(target=check_evn).start()

    LogEvent.append_http_server_log_queue = lambda message: easyrip_web.http_server.Event.log_queue.append(message)

    def _post_run_event(cmd: str):
        run_command(cmd)
        easyrip_web.http_server.Event.is_run_command.append(False)
        easyrip_web.http_server.Event.is_run_command.popleft()

    easyrip_web.http_server.Event.post_run_event = _post_run_event


if __name__ == "__main__":

    init()

    Ripper.ripper_list = []

    if len(sys.argv) > 1:
        run_command(sys.argv[1:])

    while True:
        try:
            command = input(get_input_prompt())
        except:  # noqa: E722
            log.info("Manually force exit")
            sys.exit()

        if not run_command(command):
            log.warning("Stop run command")


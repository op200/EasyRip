from datetime import datetime
import json
from pathlib import Path
from time import sleep
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
from multiprocessing import shared_memory


from .global_val import Global_val
from .easyrip_log import log, Event as LogEvent
from .ripper import Ripper
from .easyrip_mlang import (
    Global_lang_val,
    Language,
    Region,
    get_system_language,
    gettext,
    Event as MlangEvent,
)
from . import easyrip_web
from .easyrip_config import config


__all__ = ["init", "run_command", "log", "Ripper"]


PROJECT_NAME = Global_val.PROJECT_NAME
__version__ = PROJECT_VERSION = Global_val.PROJECT_VERSION
PROJECT_TITLE = Global_val.PROJECT_TITLE
PROJECT_URL = Global_val.PROJECT_URL


def change_title(title):
    if os.name == "nt":
        os.system(f"title {title}")
    elif os.name == "posix":
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


def check_ver(new_ver_str: str, old_ver_str: str) -> bool:
    new_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", new_ver_str).split(".")]
    new_ver_add_num = [v for v in str(new_ver[-1]).split("+")]
    new_ver = (
        [int(v) for v in (*new_ver[:-1], new_ver_add_num[0])],
        [int(v) for v in new_ver_add_num[1:]],
    )

    old_ver = [v for v in re.sub(r"^\D*(\d.*\d)\D*$", r"\1", old_ver_str).split(".")]
    old_ver_add_num = [v for v in str(old_ver[-1]).split("+")]
    old_ver = (
        [int(v) for v in (*old_ver[:-1], old_ver_add_num[0])],
        [int(v) for v in old_ver_add_num[1:]],
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
            log.info(
                Global_lang_val.Extra_text_index.NEW_VER_TIP,
                program_name,
                new_ver,
                dl_url,
            )
            print(get_input_prompt(True), end="")
    except Exception as e:
        print()
        log.warning(e, deep=True)
        print(get_input_prompt(True), end="")


def check_env():
    try:
        change_title(f"{gettext('Check env...')} {PROJECT_TITLE}")

        if config.get_user_profile("check_dependent"):
            _url = "https://ffmpeg.org/download.html"
            for _name in {"FFmpeg", "FFprobe"}:
                if not shutil.which(_name):
                    print()
                    log.error(
                        "{} not found, download it: {}",
                        _name,
                        f"(full build ver) {_url}",
                    )
                    print(get_input_prompt(True), end="")
                else:
                    _new_ver = (
                        subprocess.run(
                            f"{_name} -version", capture_output=True, text=True
                        )
                        .stdout.split(maxsplit=3)[2]
                        .split("_")[0]
                    )

                    if "." in _new_ver:
                        log_new_ver("8.0", _new_ver.split("-")[0], _name, _url)
                    else:
                        log_new_ver(
                            "2025.08.22", ".".join(_new_ver.split("-")[:3]), _name, _url
                        )

            _name, _url = "flac", "https://github.com/xiph/flac/releases"
            if not shutil.which(_name):
                print()
                log.warning(
                    "{} not found, download it: {}", _name, f"(ver >= 1.5.0) {_url}"
                )
                print(get_input_prompt(True), end="")

            elif check_ver(
                "1.5.0",
                (
                    old_ver_str := subprocess.run(
                        "flac -v", capture_output=True, text=True
                    ).stdout.split()[1]
                ),
            ):
                log.error("flac ver ({}) must >= 1.5.0", old_ver_str)

            else:
                log_new_ver(
                    easyrip_web.get_github_api_ver(
                        "https://api.github.com/repos/xiph/flac/releases/latest"
                    ),
                    old_ver_str,
                    _name,
                    _url,
                )

            _name, _url = "mp4fpsmod", "https://github.com/nu774/mp4fpsmod/releases"
            if not shutil.which(_name):
                print()
                log.warning("{} not found, download it: {}", _name, _url)
                print(get_input_prompt(True), end="")
            else:
                log_new_ver(
                    easyrip_web.get_github_api_ver(
                        "https://api.github.com/repos/nu774/mp4fpsmod/releases/latest"
                    ),
                    subprocess.run(_name, capture_output=True, text=True).stderr.split(
                        maxsplit=2
                    )[1],
                    _name,
                    _url,
                )

            _name, _url = "MP4Box", "https://gpac.io/downloads/gpac-nightly-builds/"
            if not shutil.which(_name):
                print()
                log.warning("{} not found, download it: {}", _name, _url)
                print(get_input_prompt(True), end="")
            else:
                log_new_ver(
                    "2.5",
                    subprocess.run("mp4box -version", capture_output=True, text=True)
                    .stderr.split("-", 2)[1]
                    .strip()
                    .split()[2],
                    _name,
                    _url,
                )

            _url = "https://mkvtoolnix.download/downloads.html"
            for _name in {"mkvpropedit", "mkvmerge"}:
                if not shutil.which(_name):
                    print()
                    log.warning("{} not found, download it: {}", _name, _url)
                    print(get_input_prompt(True), end="")
                else:
                    log_new_ver(
                        "94",
                        subprocess.run(
                            f"{_name} --version", capture_output=True, text=True
                        ).stdout.split(maxsplit=2)[1],
                        _name,
                        _url,
                    )

            # _name, _url = 'MediaInfo', 'https://mediaarea.net/en/MediaInfo/Download'
            # if not shutil.which(_name):
            #     print()
            #     log.warning('{} not found, download it: {}', _name, f'(CLI ver) {_url}')
            #     print(get_input_prompt(), end='')
            # elif not subprocess.run('mediainfo --version', capture_output=True, text=True).stdout:
            #     log.error("The MediaInfo must be CLI ver")

        if config.get_user_profile("check_update"):
            log_new_ver(
                easyrip_web.get_github_api_ver(Global_val.PROJECT_RELEASE_API),
                PROJECT_VERSION,
                PROJECT_NAME,
                f"{Global_val.PROJECT_URL} {gettext("or run '{}' when you use pip", 'pip install -U easyrip')}",
            )

        sys.stdout.flush()
        sys.stderr.flush()
        change_title(PROJECT_TITLE)

    except Exception as e:
        log.error(f"The def check_env error: {repr(e)} {e}", deep=True)


def get_input_prompt(is_color: bool = False) -> str:
    cmd_prompt = f"{gettext('Easy Rip command')}>"
    if is_color:
        cmd_prompt = (
            f"\033[{log.send_color}m{cmd_prompt}\033[{log.default_foreground_color}m"
        )
    return f"{os.path.realpath(os.getcwd())}> {cmd_prompt}"


if os.name == "nt":
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        log.warning("Windows DPI Aware failed")


def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def run_ripper_list(
    is_exit_when_run_finished: bool = False, shutdow_sec_str: str | None = None
):
    shutdown_sec: int | None = None
    if shutdow_sec_str is not None:
        try:
            shutdown_sec = int(shutdow_sec_str)
        except ValueError:
            log.warning("Wrong sec in -shutdown, change to default 60s")
            shutdown_sec = 60

    _name = ("EasyRip:dir:" + os.path.realpath(os.getcwd())).encode().hex()
    _size = 16384
    try:
        path_lock_shm = shared_memory.SharedMemory(
            name=_name,
            create=True,
            size=_size,
        )
    except FileExistsError:
        _shm = shared_memory.SharedMemory(name=_name)
        _res: dict = json.loads(
            bytes(_shm.buf[: len(_shm.buf)]).decode("utf-8").rstrip("\0")
        )
        _shm.unlink()
        log.error(
            "Current work directory has an other Easy Rip is running: {}",
            f"version: {_res.get('project_version')}, start_time: {_res.get('start_time')}",
        )
        return
    else:
        _data = json.dumps(
            {
                "size": _size,
                "project_name": PROJECT_NAME,
                "project_version": PROJECT_VERSION,
                "start_time": datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")[:-4],
            }
        ).encode("utf-8")
        path_lock_shm.buf[: len(_data)] = _data

    total = len(Ripper.ripper_list)
    warning_num = log.warning_num
    error_num = log.error_num
    for i, ripper in enumerate(Ripper.ripper_list, 1):
        progress = f"{i} / {total} - {PROJECT_TITLE}"
        log.info(progress)
        change_title(progress)
        try:
            if ripper.run() is False:
                log.error("Run {} failed", "ripper")
        except Exception as e:
            log.error(e, deep=True)
            log.warning("Stop run ripper")
        sleep(1)
    if log.warning_num > warning_num:
        log.warning(
            "There are {} {} during run", log.warning_num - warning_num, "warning"
        )
    if log.error_num > error_num:
        log.error("There are {} {} during run", log.error_num - error_num, "error")
    Ripper.ripper_list = []
    path_lock_shm.close()

    if shutdown_sec:
        log.info("Execute shutdown in {}s", shutdown_sec)
        if os.name == "nt":
            _cmd = (
                f'shutdown /s /t {shutdown_sec} /c "{gettext("{} run completed, shutdown in {}s", PROJECT_TITLE, shutdown_sec)}"',
            )
        elif os.name == "posix":
            _cmd = (f"shutdown -h +{shutdown_sec // 60}",)
        # 防 Windows Defender
        os.system(_cmd[0])

    if is_exit_when_run_finished:
        sys.exit()

    change_title(f"End - {PROJECT_TITLE}")
    log.info("Run completed")


def run_command(command: list[str] | str) -> bool:
    if isinstance(command, list):
        cmd_list = command

    elif isinstance(command, str):
        try:
            cmd_list = [
                cmd.strip('"').strip("'").replace("\\\\", "\\")
                for cmd in shlex.split(command, posix=False)
            ]
        except ValueError as e:
            log.error(e)
            return False

    if len(cmd_list) == 0:
        return True

    change_title(PROJECT_TITLE)

    cmd_list.append("")

    match cmd_list[0]:
        case "h" | "help":
            log.send("", Global_lang_val.Extra_text_index.HELP_DOC, is_format=False)

        case "v" | "ver" | "version":
            log.send("", f"{PROJECT_NAME} version {PROJECT_VERSION}\n{PROJECT_URL}")

        case "log":
            msg = " ".join(cmd_list[2:])
            match cmd_list[1]:
                case "info":
                    log.info(msg)
                case "warning" | "warn":
                    log.warning(msg)
                case "error" | "err":
                    log.error(msg)
                case "send":
                    log.send("", msg)
                case "debug":
                    log.debug(msg)
                case _:
                    log.info(f"{cmd_list[1]} {msg}")

        case str() as s if len(s) > 0 and s.startswith("$"):
            try:
                exec(" ".join(cmd_list)[1:].lstrip().replace(r"\N", "\n"))
            except Exception as e:
                log.error("Your input command has error:\n{}", e)

        case "exit":
            sys.exit()

        case "cd":
            try:
                _path = None

                if isinstance(command, str):
                    _path = command.split(" ", maxsplit=1)
                    if len(_path) <= 1:
                        _path = None
                    else:
                        _path = _path[1].strip('"').strip("'")

                if _path is None:
                    _path = cmd_list[1]

                os.chdir(_path)
            except OSError as e:
                log.error(e)

        case "dir":
            files = os.listdir(os.getcwd())
            for f in files:
                print(f)
            log.send("", " | ".join(files))

        case "mkdir" | "makedir":
            try:
                os.makedirs(cmd_list[1])
            except Exception as e:
                log.warning(e)

        case "cls" | "clear":
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")

        case "list":
            match cmd_list[1]:
                case "clear" | "clean":
                    Ripper.ripper_list = []
                case "del" | "pop":
                    try:
                        del Ripper.ripper_list[int(cmd_list[2]) - 1]
                    except Exception as e:
                        log.error(e)
                    else:
                        log.info("Delete the {}th ripper success", cmd_list[2])
                case "sort":
                    reverse = "r" in cmd_list[2]
                    if "n" in cmd_list[2]:
                        Ripper.ripper_list.sort(
                            key=lambda ripper: [
                                int(text) if text.isdigit() else text.lower()
                                for text in re.split(
                                    r"(\d+)", str(ripper.input_path_list)
                                )
                            ],
                            reverse=reverse,
                        )
                    else:
                        Ripper.ripper_list.sort(
                            key=lambda ripper: str(ripper.input_path_list),
                            reverse=reverse,
                        )
                case "":
                    msg = f"ripper list ({len(Ripper.ripper_list)}):"
                    if Ripper.ripper_list:
                        msg += "\n" + f"\n  {log.hr}\n".join(
                            [
                                f"  {i}.\n  {ripper}"
                                for i, ripper in enumerate(Ripper.ripper_list, 1)
                            ]
                        )
                    log.send("", msg, is_format=False)
                case _:
                    try:
                        i1, i2 = int(cmd_list[1]), int(cmd_list[2])
                        if i1 > 0:
                            i1 -= 1
                        if i2 > 0:
                            i2 -= 1
                        Ripper.ripper_list[i1], Ripper.ripper_list[i2] = (
                            Ripper.ripper_list[i2],
                            Ripper.ripper_list[i1],
                        )
                    except Exception as e:
                        log.error(f"{repr(e)} {e}", deep=True)

        case "run":
            is_run_exit = False
            match cmd_list[1]:
                case "exit":
                    is_run_exit = True
                case "shutdown":
                    if _shutdown_sec_str := cmd_list[2] or "60":
                        log.info(
                            "Will shutdown in {}s after run finished", _shutdown_sec_str
                        )
            run_ripper_list(is_run_exit)

        case "server":
            if easyrip_web.http_server.Event.is_run_command[-1]:
                log.error("Can not start multiple services")
                return False

            address, password = None, None

            for i in range(1, len(cmd_list)):
                match cmd_list[i]:
                    case "-a" | "-address":
                        address = cmd_list[i + 1]
                    case "-p" | "password":
                        password = cmd_list[i + 1]
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
                        port = int(port.lstrip(":"))
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

            easyrip_web.run_server(host=host or "", port=port or 0, password=password)

        case "config":
            match cmd_list[1]:
                case "clear" | "clean" | "reset" | "regenerate":
                    config.regenerate_config()
                    init()
                case "open":
                    config.open_config_dir()
                case "set":
                    _val = cmd_list[3]
                    try:
                        _val = int(_val)
                    except ValueError:
                        pass
                    try:
                        _val = float(_val)
                    except ValueError:
                        pass
                    match _val:
                        case "true" | "True":
                            _val = True
                        case "false" | "False":
                            _val = False
                    config.set_user_profile(cmd_list[2], _val)
                    init()
                case "list":
                    config.show_config_list()

        case _:
            input_pathname_org_list: list[str] = []
            output_basename = None
            output_dir = None
            preset_name = None
            option_map: dict[str, str] = {}
            is_run = False
            is_exit_when_run_finished = False
            shutdown_sec_str: str | None = None

            _skip: bool = False
            for i in range(0, len(cmd_list)):
                if _skip:
                    _skip = False
                    continue

                _skip = True

                match cmd_list[i]:
                    case "-i":
                        if cmd_list[i + 1] == "fd":
                            if easyrip_web.http_server.Event.is_run_command[-1]:
                                log.error("Disable the use of 'fd' on the web")
                                return False
                            input_pathname_org_list += file_dialog()
                        else:
                            input_pathname_org_list += [
                                s.strip() for s in cmd_list[i + 1].split("::")
                            ]

                    case "-o":
                        output_basename = cmd_list[i + 1]
                        if re.search(
                            r'[<>:"/\\|?*]',
                            (
                                new_output_basename := re.sub(
                                    r"\?\{[^}]*\}", "", output_basename
                                )
                            ),
                        ):
                            log.error('Illegal char in -o "{}"', new_output_basename)
                            return False

                    case "-o:dir":
                        output_dir = cmd_list[i + 1]
                        if not os.path.isdir(output_dir):
                            try:
                                os.makedirs(output_dir)
                                log.info(
                                    'The directory "{}" did not exist and was created',
                                    output_dir,
                                )
                            except Exception as e:
                                log.error(f"{repr(e)} {e}", deep=True)
                                return False

                    case "-preset" | "-p":
                        preset_name = cmd_list[i + 1]

                    case "-run":
                        is_run = True
                        match cmd_list[i + 1]:
                            case "exit":
                                is_exit_when_run_finished = True
                            case "shutdown":
                                shutdown_sec_str = cmd_list[i + 2] or "60"
                            case _:
                                _skip = False

                    case str() as s if len(s) > 1 and s.startswith("-"):
                        option_map[s[1:]] = cmd_list[i + 1]

                    case _:
                        _skip = False

            if not preset_name:
                log.warning("Missing '-preset' option, set to default value 'custom'")
                preset_name = "custom"

            try:
                if len(input_pathname_org_list) == 0:
                    log.warning("Input file number == 0")
                    return False

                for i, input_pathname in enumerate(input_pathname_org_list):
                    new_option_map = option_map.copy()

                    def _iterator_fmt_replace(match: re.Match[str]):
                        s = match.group(1)
                        match s:
                            case str() as s if s.startswith("time:"):
                                try:
                                    return _time.strftime(s[5:])
                                except Exception as e:
                                    log.error(f"{repr(e)} {e}", deep=True)
                                    return ""
                            case _:
                                try:
                                    d = {
                                        k: v
                                        for s1 in s.split(",")
                                        for k, v in [s1.split("=")]
                                    }
                                    start = int(d.get("start", 0))
                                    padding = int(d.get("padding", 0))
                                    increment = int(d.get("increment", 1))
                                    return str(start + i * increment).zfill(padding)
                                except Exception as e:
                                    log.error(f"{repr(e)} {e}", deep=True)
                                    return ""

                    if output_basename is None:
                        new_output_basename = None
                    else:
                        _time = datetime.now()

                        new_output_basename = re.sub(
                            r"\?\{([^}]*)\}",
                            _iterator_fmt_replace,
                            output_basename,
                        )

                    if chapters := option_map.get("chapters"):
                        chapters = re.sub(
                            r"\?\{([^}]*)\}",
                            _iterator_fmt_replace,
                            chapters,
                        )

                        if not Path(chapters).is_file():
                            log.warning(
                                "The '-chapters' file {} does not exist", chapters
                            )

                        new_option_map["chapters"] = chapters

                    input_pathname_list: list[str] = input_pathname.split("?")
                    for path in input_pathname_list:
                        if not os.path.exists(path):
                            log.warning('The file "{}" does not exist', path)

                    _input_basename = os.path.splitext(
                        os.path.basename(input_pathname_list[0])
                    )

                    if sub_map := option_map.get("sub"):
                        sub_list: list[str]
                        sub_map_list: list[str] = sub_map.split(":")

                        if sub_map_list[0] == "auto":
                            sub_list = []

                            while _input_basename[1] != "":
                                _input_basename = os.path.splitext(_input_basename[0])
                            _input_prefix: str = _input_basename[0]

                            _dir = output_dir or os.path.realpath(os.getcwd())
                            for _file_basename in os.listdir(_dir):
                                _file_basename_list = os.path.splitext(_file_basename)
                                if (
                                    _file_basename_list[1] == ".ass"
                                    and _file_basename_list[0].startswith(_input_prefix)
                                    and (
                                        len(sub_map_list) == 1
                                        or os.path.splitext(_file_basename_list[0])[
                                            1
                                        ].lstrip(".")
                                        in sub_map_list[1:]
                                    )
                                ):
                                    sub_list.append(os.path.join(_dir, _file_basename))

                        else:
                            sub_list = [s.strip() for s in sub_map.split("::")]

                        sub_list_len = len(sub_list)
                        if sub_list_len > 1:
                            for sub_path in sub_list:
                                new_option_map["sub"] = sub_path

                                _output_base_suffix_name = os.path.splitext(
                                    os.path.splitext(os.path.basename(sub_path))[0]
                                )
                                _output_base_suffix_name = (
                                    _output_base_suffix_name[1]
                                    or _output_base_suffix_name[0]
                                )
                                Ripper.add_ripper(
                                    input_pathname_list,
                                    [
                                        f"{new_output_basename or _input_basename[0]}{_output_base_suffix_name}"
                                    ],
                                    output_dir,
                                    Ripper.PresetName(preset_name),
                                    new_option_map,
                                )

                        elif sub_list_len == 0:
                            log.warning(
                                "No subtitle file exist as -sub auto when -i {} -o:dir {}",
                                input_pathname_list,
                                output_dir or os.path.realpath(os.getcwd()),
                            )

                        else:
                            new_option_map["sub"] = sub_list[0]
                            Ripper.add_ripper(
                                input_pathname_list,
                                [new_output_basename],
                                output_dir,
                                Ripper.PresetName(preset_name),
                                new_option_map,
                            )

                    else:
                        Ripper.add_ripper(
                            input_pathname_list,
                            [new_output_basename],
                            output_dir,
                            Ripper.PresetName(preset_name),
                            new_option_map,
                        )

            except KeyError as e:
                log.error("Unsupported option: {}", e)
                return False

            if is_run:
                run_ripper_list(is_exit_when_run_finished, shutdown_sec_str)

    return True


def init(is_first_run: bool = False):
    if is_first_run:
        # 当前路径添加到环境变量
        new_path = os.path.realpath(os.getcwd())
        if os.pathsep in (current_path := os.environ.get("PATH", "")):
            if new_path not in current_path.split(os.pathsep):
                updated_path = f"{new_path}{os.pathsep}{current_path}"
                os.environ["PATH"] = updated_path

    # 设置语言
    _sys_lang = get_system_language()
    Global_lang_val.gettext_target_lang = _sys_lang
    if (_lang_config := config.get_user_profile("language")) not in {"auto", None}:
        _lang = str(_lang_config).split("-")
        if len(_lang) == 1:
            _lang.append("")
        Global_lang_val.gettext_target_lang = (
            getattr(Language, _lang[0], Language.Unknow),
            getattr(Region, _lang[1], Region.Unknow),
        )

    # 设置日志文件路径名
    log.html_filename = gettext("encoding_log.html")
    if _path := str(config.get_user_profile("force_log_file_path") or ""):
        log.html_filename = os.path.join(_path, log.html_filename)

    # 设置日志级别
    try:
        log.print_level = getattr(
            log.LogLevel, str(config.get_user_profile("log_print_level"))
        )
        log.write_level = getattr(
            log.LogLevel, str(config.get_user_profile("log_write_level"))
        )
    except Exception as e:
        log.error(f"{repr(e)} {e}", deep=True)

    if is_first_run:
        # 设置启动目录
        try:
            if _path := str(config.get_user_profile("startup_directory")):
                os.chdir(_path)
        except Exception as e:
            log.error(f"{repr(e)} {e}", deep=True)

    # 获取终端颜色
    log.init()

    if is_first_run:
        # 检测环境
        Thread(target=check_env, daemon=True).start()

        MlangEvent.log = easyrip_web.http_server.Event.log = log  # type: ignore

        LogEvent.append_http_server_log_queue = (
            lambda message: easyrip_web.http_server.Event.log_queue.append(message)
        )

        def _post_run_event(cmd: str):
            run_command(cmd)
            easyrip_web.http_server.Event.is_run_command.append(False)
            easyrip_web.http_server.Event.is_run_command.popleft()

        easyrip_web.http_server.Event.post_run_event = _post_run_event

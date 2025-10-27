import ctypes
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from multiprocessing import shared_memory
from pathlib import Path
from threading import Thread
from time import sleep
from tkinter import filedialog
from typing import Final

import tomllib

from . import easyrip_mlang, easyrip_web, global_val
from .easyrip_command import Cmd_type, Opt_type, get_help_doc
from .easyrip_config import config
from .easyrip_log import Event as LogEvent
from .easyrip_log import log
from .easyrip_mlang import (
    Global_lang_val,
    Lang_tag,
    Lang_tag_language,
    get_system_language,
    gettext,
    translate_subtitles,
)
from .ripper import Media_info, Ripper
from .ripper.ripper import DEFAULT_PRESET_PARAMS
from .utils import change_title, check_ver, read_text

__all__ = ["init", "run_command"]


PROJECT_NAME = global_val.PROJECT_NAME
__version__ = PROJECT_VERSION = global_val.PROJECT_VERSION
PROJECT_TITLE = global_val.PROJECT_TITLE
PROJECT_URL = global_val.PROJECT_URL


def log_new_ver(
    new_ver: str | None, old_ver: str, program_name: str, dl_url: str
) -> None:
    if new_ver is None:
        return
    try:
        if check_ver(new_ver, old_ver):
            log.info(
                "\n"
                + gettext(
                    "{} has new version {}. You can download it: {}",
                    program_name,
                    new_ver,
                    dl_url,
                )
            )
            print(get_input_prompt(True), end="")
    except Exception as e:
        log.warning(f"\n{e}", is_format=False, deep=True)
        print(get_input_prompt(True), end="")


def check_env() -> None:
    try:
        change_title(f"{gettext('Check env...')} {PROJECT_TITLE}")

        if config.get_user_profile("check_dependent"):
            _url = "https://ffmpeg.org/download.html"
            for _name in ("FFmpeg", "FFprobe"):
                if not shutil.which(_name):
                    log.error(
                        "\n"
                        + gettext(
                            "{} not found, download it: {}",
                            _name,
                            f"(full build ver) {_url}",
                        )
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
                log.warning(
                    "\n"
                    + gettext(
                        "{} not found, download it: {}", _name, f"(ver >= 1.5.0) {_url}"
                    )
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
                    easyrip_web.github.get_release_ver(
                        "https://api.github.com/repos/xiph/flac/releases/latest"
                    ),
                    old_ver_str,
                    _name,
                    _url,
                )

            _name, _url = "mp4fpsmod", "https://github.com/nu774/mp4fpsmod/releases"
            if not shutil.which(_name):
                log.warning(
                    "\n" + gettext("{} not found, download it: {}", _name, _url)
                )
                print(get_input_prompt(True), end="")
            else:
                log_new_ver(
                    easyrip_web.github.get_release_ver(
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
                log.warning(
                    "\n" + gettext("{} not found, download it: {}", _name, _url)
                )
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
            for _name in ("mkvpropedit", "mkvmerge"):
                if not shutil.which(_name):
                    log.warning(
                        "\n" + gettext("{} not found, download it: {}", _name, _url)
                    )
                    print(get_input_prompt(True), end="")
                else:
                    log_new_ver(
                        "95",
                        subprocess.run(
                            f"{_name} --version", capture_output=True, text=True
                        ).stdout.split(maxsplit=2)[1],
                        _name,
                        _url,
                    )

            # _name, _url = "MediaInfo", "https://mediaarea.net/en/MediaInfo/Download"
            # if not shutil.which(_name):
            #     log.warning(
            #         "\n"
            #         + gettext(
            #             "{} not found, download it: {}", _name, f"(CLI ver) {_url}"
            #         )
            #     )
            #     print(get_input_prompt(), end="")
            # elif not subprocess.run(
            #     "mediainfo --version", capture_output=True, text=True
            # ).stdout:
            #     log.error("The MediaInfo must be CLI ver")

        if config.get_user_profile("check_update"):
            log_new_ver(
                easyrip_web.github.get_release_ver(global_val.PROJECT_RELEASE_API),
                PROJECT_VERSION,
                PROJECT_NAME,
                f"{global_val.PROJECT_URL} {gettext("or run '{}' when you use pip", 'pip install -U easyrip')}",
            )

        sys.stdout.flush()
        sys.stderr.flush()
        change_title(PROJECT_TITLE)

    except Exception as e:
        log.error(f"The def check_env error: {e!r} {e}", deep=True)


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


def file_dialog(
    *,
    is_askdir: bool = False,
    initialdir=None,
) -> tuple[str, ...]:
    tkRoot = tk.Tk()

    tkRoot.withdraw()
    if is_askdir:
        file_paths = (filedialog.askdirectory(initialdir=initialdir),)
    else:
        file_paths = filedialog.askopenfilenames(initialdir=initialdir)

    tkRoot.destroy()
    return file_paths if file_paths else ()


def run_ripper_list(
    *,
    is_exit_when_run_finished: bool = False,
    shutdow_sec_str: str | None = None,
    enable_multithreading: bool = False,
) -> None:
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
        assert path_lock_shm.buf is not None
    except FileExistsError:
        _shm = shared_memory.SharedMemory(name=_name)
        assert _shm.buf is not None
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

    total: Final[int] = len(Ripper.ripper_list)
    warning_num: Final[int] = log.warning_num
    error_num: Final[int] = log.error_num

    if enable_multithreading:
        threads: list[Thread] = []
        threads_return: dict[int, bool] = {}
        progress_num: list[int] = [0]

        def _run_ripper_thread_target(key: int, ripper: Ripper, /) -> None:
            threads_return[key] = ripper.run()
            progress_num[0] += 1

        for i, ripper in enumerate(Ripper.ripper_list, 1):
            thread = Thread(
                target=_run_ripper_thread_target,
                args=(i, ripper),
                daemon=True,
            )
            log.info("Start Ripper thread {} / {}", i, total)
            thread.start()
            threads.append(thread)

        # 进度打印线程
        def _run_ripper_thread_progress() -> None:
            progress = f"{len(threads_return)} / {total} - {PROJECT_TITLE}"
            log.info(progress)
            change_title(progress)

        Thread(target=_run_ripper_thread_progress, daemon=True)

        for thread in threads:
            thread.join()

    else:
        for i, ripper in enumerate(Ripper.ripper_list, 1):
            progress = f"{i} / {total} - {PROJECT_TITLE}"
            log.info(progress)
            change_title(progress)
            try:
                if ripper.run() is False:
                    log.error("Run {} failed", "Ripper")
            except Exception as e:
                log.error(e, deep=True)
                log.warning("Stop run Ripper")
            sleep(0.5)

    if log.warning_num > warning_num:
        log.warning(
            "There are {} {} during run", log.warning_num - warning_num, "warning"
        )
    if log.error_num > error_num:
        log.error("There are {} {} during run", log.error_num - error_num, "error")
    Ripper.ripper_list.clear()
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

    else:
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

    cmd_type: Cmd_type | None = None
    if cmd_list[0] in Cmd_type._member_map_:
        cmd_type = Cmd_type[cmd_list[0]]
    elif len(cmd_list[0]) > 0 and cmd_list[0].startswith("$"):
        cmd_type = Cmd_type._run_any

    match cmd_type:
        case Cmd_type.help:
            if cmd_list[1]:
                _want_doc_cmd_type: Cmd_type | Opt_type | None = Cmd_type.from_str(
                    cmd_list[1]
                ) or Opt_type.from_str(cmd_list[1])
                match _want_doc_cmd_type:
                    case Opt_type._preset:
                        if not cmd_list[2]:
                            log.send(_want_doc_cmd_type.value.to_doc(), is_format=False)
                        elif cmd_list[2] in Ripper.PresetName._value2member_map_:
                            _preset = Ripper.PresetName(cmd_list[2])
                            if _preset in DEFAULT_PRESET_PARAMS:
                                log.send(
                                    json.dumps(
                                        DEFAULT_PRESET_PARAMS[_preset], indent=2
                                    ),
                                    is_format=False,
                                )
                            else:
                                log.send(
                                    "The preset '{}' has no default val", cmd_list[2]
                                )
                        else:
                            log.error("'{}' is not a preset", cmd_list[2])

                    case None:
                        log.error("'{}' does not exist", cmd_list[1])

                    case _:
                        log.send(_want_doc_cmd_type.value.to_doc(), is_format=False)
            else:
                log.send(get_help_doc(), is_format=False)

        case Cmd_type.version:
            log.send(f"{PROJECT_NAME} version {PROJECT_VERSION}\n{PROJECT_URL}")

        case Cmd_type.init:
            init()

        case Cmd_type.log:
            msg = " ".join(cmd_list[2:])
            match cmd_list[1]:
                case "info":
                    log.info(msg)
                case "warning" | "warn":
                    log.warning(msg)
                case "error" | "err":
                    log.error(msg)
                case "send":
                    log.send(msg)
                case "debug":
                    log.debug(msg)
                case _:
                    log.info(f"{cmd_list[1]} {msg}")

        case Cmd_type._run_any:
            try:
                exec(" ".join(cmd_list)[1:].lstrip().replace(r"\N", "\n"))
            except Exception as e:
                log.error("Your input command has error:\n{}", e)

        case Cmd_type.exit:
            sys.exit()

        case Cmd_type.cd | Cmd_type.mediainfo:
            _path_tuple: tuple[str, ...] | None = None

            match cmd_list[1]:
                case "fd" | "cfd" as fd_param:
                    if easyrip_web.http_server.Event.is_run_command:
                        log.error("Disable the use of '{}' on the web", fd_param)
                        return False
                    _path_tuple = file_dialog(
                        is_askdir=cmd_type is Cmd_type.cd,
                        initialdir=os.getcwd() if fd_param == "cfd" else None,
                    )
                case _:
                    if isinstance(command, str):
                        _path = command.split(" ", maxsplit=1)
                        _path_tuple = (
                            None
                            if len(_path) <= 1
                            else tuple(_path[1].strip('"').strip("'").split("?"))
                        )

                    if _path_tuple is None:
                        _path_tuple = tuple(cmd_list[1].split("?"))

            match cmd_type:
                case Cmd_type.cd:
                    try:
                        os.chdir(_path_tuple[0])
                    except OSError as e:
                        log.error(e)
                case Cmd_type.mediainfo:
                    for _path in _path_tuple:
                        log.send(f"{_path}: {Media_info.from_path(_path)}")

        case Cmd_type.dir:
            files = os.listdir(os.getcwd())
            for f_and_s in files:
                print(f_and_s)
            log.send(" | ".join(files))

        case Cmd_type.mkdir:
            try:
                os.makedirs(cmd_list[1])
            except Exception as e:
                log.warning(e)

        case Cmd_type.cls:
            os.system("cls") if os.name == "nt" else os.system("clear")

        case Cmd_type.list:
            match cmd_list[1]:
                case "clear" | "clean":
                    Ripper.ripper_list.clear()
                case "del" | "pop":
                    try:
                        del Ripper.ripper_list[int(cmd_list[2]) - 1]
                    except Exception as e:
                        log.error(e)
                    else:
                        log.info("Delete the {}th Ripper success", cmd_list[2])
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
                    log.send(
                        f"Ripper list ({len(Ripper.ripper_list)}):"
                        + f"\n {'─' * (shutil.get_terminal_size().columns - 2)}".join(
                            f"\n  {i}.\n  {ripper}"
                            for i, ripper in enumerate(Ripper.ripper_list, 1)
                        ),
                        is_format=False,
                    )
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
                    except ValueError:
                        log.error("2 int must be inputed")
                    except IndexError:
                        log.error("list index out of range")

        case Cmd_type.run:
            is_run_exit = False
            _enable_multithreading: bool = False
            _shutdown_sec_str: str | None = None

            _skip_run_param: int = 0

            for i, cmd in enumerate(cmd_list[1:]):
                if _skip_run_param:
                    _skip_run_param -= 1
                    continue

                match cmd:
                    case "":
                        pass

                    case "exit":
                        is_run_exit = True

                    case "shutdown":
                        _skip_run_param += 1
                        if i + 1 < len(cmd_list[1:]):
                            _shutdown_sec_str = cmd_list[i + 1] or "60"
                            log.info(
                                "Will shutdown in {}s after run finished",
                                _shutdown_sec_str,
                            )
                        else:
                            log.error("{} need param", cmd)
                            return False

                    case "-multithreading":
                        _skip_run_param += 1
                        if i + 1 < len(cmd_list[1:]):
                            _enable_multithreading = cmd_list[i + 1] != "0"
                        else:
                            log.error("{} need param", cmd)
                            return False

                    case _ as param:
                        log.error("Unsupported param: {}", param)
                        return False

            run_ripper_list(
                is_exit_when_run_finished=is_run_exit,
                shutdow_sec_str=_shutdown_sec_str,
                enable_multithreading=_enable_multithreading,
            )

        case Cmd_type.server:
            if easyrip_web.http_server.Event.is_run_command:
                log.error("Can not start multiple services")
                return False

            address, password = None, None

            for i in range(1, len(cmd_list)):
                match cmd_list[i]:
                    case "-a" | "-address":
                        address = cmd_list[i + 1]
                    case "-p" | "-password":
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

        case Cmd_type.config:
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

                    if (_old_val := config.get_user_profile(cmd_list[2])) == _val:
                        log.info(
                            "The new value is the same as the old value, cancel the modification",
                        )
                    elif config.set_user_profile(cmd_list[2], _val):
                        init()
                        log.info(
                            "'config set {}' successful: {} -> {}",
                            cmd_list[2],
                            _old_val,
                            _val,
                        )
                case "list":
                    config.show_config_list()
                case _ as param:
                    log.error("Unsupported param: {}", param)
                    return False

        case Cmd_type.translate:
            if not (_infix := cmd_list[1]):
                log.error("Need target infix")
                return False

            if not (_target_tag_str := cmd_list[2]):
                log.error("Need target language")
                return False

            translate_overwrite: bool = False
            for s in cmd_list[3:]:
                if s == "-overwrite":
                    translate_overwrite = True

            try:
                _file_list = translate_subtitles(
                    directory=Path(os.getcwd()),
                    infix=_infix,
                    target_lang=_target_tag_str,
                )
            except Exception as e:
                log.error(e, is_format=False)
                return False

            for f_and_s in _file_list:
                if translate_overwrite is False and f_and_s[0].is_file():
                    log.error("There is a file with the same name, cancel file writing")
                    return False

            for f_and_s in _file_list:
                with f_and_s[0].open("wt", encoding="utf-8-sig", newline="\n") as f:
                    f.write(f_and_s[1])

            log.info(
                "Successfully translated: {}",
                gettext(
                    "{num} file{s} in total",
                    num=(_len := len(_file_list)),
                    s="s" if _len > 1 else "",
                ),
            )
            return True

        case _:
            input_pathname_org_list: list[str] = []
            output_basename: str | None = None
            output_dir: str | None = None
            preset_name: str | None = None
            option_map: dict[str, str] = {}
            is_run: bool = False
            is_exit_when_run_finished: bool = False
            shutdown_sec_str: str | None = None
            enable_multithreading: bool = False

            _skip: int = 0
            for i in range(len(cmd_list)):
                if _skip:
                    _skip -= 1
                    continue

                _skip += 1

                match cmd_list[i]:
                    case "-i":
                        match cmd_list[i + 1]:
                            case "fd" | "cfd" as fd_param:
                                if easyrip_web.http_server.Event.is_run_command:
                                    log.error(
                                        "Disable the use of '{}' on the web", fd_param
                                    )
                                    return False
                                input_pathname_org_list += file_dialog(
                                    initialdir=(
                                        os.getcwd() if fd_param == "cfd" else None
                                    )
                                )
                            case _:
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
                                log.error(f"{e!r} {e}", deep=True)
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
                                _skip += 1
                            case _:
                                _skip -= 1

                    case "-multithreading":
                        match cmd_list[i + 1]:
                            case "0":
                                enable_multithreading = False
                            case "1":
                                enable_multithreading = True
                            case _:
                                log.error("Unsupported param: {}", cmd_list[i + 1])
                                return False

                    case str() as s if len(s) > 1 and s.startswith("-"):
                        option_map[s[1:]] = cmd_list[i + 1]

                    case _:
                        _skip -= 1

            if not preset_name:
                log.warning("Missing '-preset' option, set to default value 'custom'")
                preset_name = "custom"

            try:
                if len(input_pathname_org_list) == 0:
                    log.warning("Input file number == 0")
                    return False

                for i, input_pathname in enumerate(input_pathname_org_list):
                    new_option_map = option_map.copy()

                    fmt_time = datetime.now()

                    def _create_iterator_fmt_replace(
                        time: datetime, num: int
                    ) -> Callable[[re.Match[str]], str]:
                        def _iterator_fmt_replace(match: re.Match[str]) -> str:
                            s = match.group(1)
                            match s:
                                case str() as s if s.startswith("time:"):
                                    try:
                                        return time.strftime(s[5:])
                                    except Exception as e:
                                        log.error(f"{e!r} {e}", deep=True)
                                        return ""
                                case _:
                                    d = {
                                        k: v
                                        for s1 in s.split(",")
                                        for k, v in [s1.split("=")]
                                    }
                                    start = int(d.get("start", 0))
                                    padding = int(d.get("padding", 0))
                                    increment = int(d.get("increment", 1))
                                    return str(start + num * increment).zfill(padding)

                        return _iterator_fmt_replace

                    try:
                        new_output_basename = (
                            None
                            if output_basename is None
                            else re.sub(
                                r"\?\{([^}]*)\}",
                                _create_iterator_fmt_replace(fmt_time, i),
                                output_basename,
                            )
                        )

                        if chapters := option_map.get("chapters"):
                            chapters = re.sub(
                                r"\?\{([^}]*)\}",
                                _create_iterator_fmt_replace(fmt_time, i),
                                chapters,
                            )

                            if not Path(chapters).is_file():
                                log.warning(
                                    "The '-chapters' file {} does not exist", chapters
                                )

                            new_option_map["chapters"] = chapters

                    except ValueError as e:
                        log.error("Unsupported param: {}", e)
                        return False

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
                run_ripper_list(
                    is_exit_when_run_finished=is_exit_when_run_finished,
                    shutdow_sec_str=shutdown_sec_str,
                    enable_multithreading=enable_multithreading,
                )

    return True


def init(is_first_run: bool = False) -> None:
    if is_first_run:
        # 当前路径添加到环境变量
        new_path = os.path.realpath(os.getcwd())
        if os.pathsep in (
            current_path := os.environ.get("PATH", "")
        ) and new_path not in current_path.split(os.pathsep):
            updated_path = f"{new_path}{os.pathsep}{current_path}"
            os.environ["PATH"] = updated_path

    # 设置语言
    _sys_lang = get_system_language()
    Global_lang_val.gettext_target_lang = _sys_lang
    if (_lang_config := config.get_user_profile("language")) not in {"auto", None}:
        Global_lang_val.gettext_target_lang = Lang_tag.from_str(str(_lang_config))

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
        log.error(f"{e!r} {e}", deep=True)

    if is_first_run:
        # 设置启动目录
        try:
            if _path := str(config.get_user_profile("startup_directory")):
                os.chdir(_path)
        except Exception as e:
            log.error(f"{e!r} {e}", deep=True)

    # 获取终端颜色
    log.init()

    # 扫描额外的翻译文件
    for file in (
        f
        for f in itertools.chain(Path(".").iterdir(), config._config_dir.iterdir())
        if f.stem.startswith("lang_")
    ):
        match file.suffix:
            case ".json":
                lang_map = dict[str, str](json.loads(read_text(file)))
            case ".toml":
                lang_map = dict[str, str](tomllib.loads(read_text(file)))
            case _:
                continue

        if (
            lang_tag := Lang_tag.from_str(file.stem[5:])
        ).language is not Lang_tag_language.Unknown:
            easyrip_mlang.all_supported_lang_map[lang_tag] = lang_map

            log.debug("Loading \"{}\" as '{}' language successfully", file, lang_tag)

    if is_first_run:
        # 检测环境
        Thread(target=check_env, daemon=True).start()

        LogEvent.append_http_server_log_queue = (
            lambda message: easyrip_web.http_server.Event.log_queue.append(message)
        )

        def _post_run_event(cmd: str) -> None:
            run_command(cmd)
            easyrip_web.http_server.Event.is_run_command = False

        easyrip_web.http_server.Event.post_run_event = _post_run_event

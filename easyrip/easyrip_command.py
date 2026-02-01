import enum
import itertools
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Self, final

from prompt_toolkit.completion import (
    Completer,
    FuzzyCompleter,
    NestedCompleter,
    WordCompleter,
    merge_completers,
)
from prompt_toolkit.completion.base import CompleteEvent, Completion
from prompt_toolkit.document import Document

from . import global_val
from .easyrip_config.config_key import Config_key
from .easyrip_prompt import (
    SmartPathCompleter,
    fuzzy_filter_and_sort,
    highlight_fuzzy_match,
)
from .ripper.param import Audio_codec, Muxer, Preset_name


@final
@dataclass(slots=True, init=False, eq=False)
class Cmd_type_val:
    names: tuple[str, ...]
    _param: str
    _description: str
    childs: tuple["Cmd_type_val", ...]
    is_no_prompt_child: bool
    """此项作为父项的子项时，不在自动补全时使用"""
    is_no_doc_child: bool
    """此项作为父项的子项时，不在 doc 时使用"""
    is_all_no_doc_childs: bool
    """此项的所有子项不在 doc 时使用"""

    @property
    def param(self) -> str:
        try:
            from .easyrip_mlang import gettext

            return gettext(self._param, is_format=False)

        except ImportError:  # 启动时，原字符串导入翻译文件
            return self._param

    @param.setter
    def param(self, val: str) -> None:
        self._param = val

    @property
    def description(self) -> str:
        try:
            from .easyrip_mlang import gettext

            return gettext(self._description, is_format=False)

        except ImportError:  # 启动时，原字符串导入翻译文件
            return self._description

    @description.setter
    def description(self, val: str) -> None:
        self._description = val

    def __init__(
        self,
        names: tuple[str, ...],
        *,
        param: str = "",
        description: str = "",
        childs: tuple["Cmd_type_val", ...] = (),
        is_no_prompt_child: bool = False,
        is_no_doc_child: bool = False,
        is_all_no_doc_childs: bool = False,
    ) -> None:
        self.names = names
        self.param = param
        self.description = description
        self.childs = childs
        self.is_no_prompt_child = is_no_prompt_child
        self.is_no_doc_child = is_no_doc_child
        self.is_all_no_doc_childs = is_all_no_doc_childs

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cmd_type_val):
            return self.names == other.names
        return False

    def __hash__(self) -> int:
        return hash(self.names)

    def to_doc(self) -> str:
        description: str = ((f"{self.description}\n") if self.description else "") + (
            ""
            if self.is_all_no_doc_childs
            else "".join(
                f"\n{child.to_doc()}"
                for child in self.childs
                if not child.is_no_doc_child
            )
        )
        return (
            f"{' / '.join(self.names)} {self.param}\n"
            f"{textwrap.indent(description, ' │ ', lambda _: True)}"  # 永远返回 True 才能保证空行前也能加字符
        )


class Cmd_type(enum.Enum):
    help = h = Cmd_type_val(
        ("h", "help"),
        param="[<cmd> [<cmd param>]]",
        description=(
            "Show full help or show the <cmd> help.\n"
            "e.g. help list\n"  # .
            "e.g. h -p x265slow"
        ),
    )
    version = v = ver = Cmd_type_val(
        ("v", "ver", "version"),
        description="Show version info",
    )
    init = Cmd_type_val(
        ("init",),
        description=(
            "Execute initialization function\n"
            "e.g. you can execute it after modifying the dynamic translation file"
        ),
    )
    log = Cmd_type_val(
        ("log",),
        param="[<LogLevel>] <string>",
        description=(
            "Output custom log\n"
            "log level:\n"
            "  info\n"
            "  warning | warn\n"
            "  error | err\n"
            "  send\n"
            "  debug\n"
            "  Default: info"
        ),
        childs=(
            Cmd_type_val(("info",)),
            Cmd_type_val(("warning", "warn")),
            Cmd_type_val(("error", "err")),
            Cmd_type_val(("send",)),
            Cmd_type_val(("debug",)),
        ),
        is_all_no_doc_childs=True,
    )
    _run_any = Cmd_type_val(
        ("$",),
        param="<code>",
        description=(
            "Run code directly from the internal environment.\n"
            "Execute the code string directly after the '$'.\n"
            'The string "\\N" will be changed to real "\\n".\n'
        ),
    )
    exit = Cmd_type_val(
        ("exit",),
        param="exit",
        description="Exit this program",
    )
    cd = Cmd_type_val(
        ("cd",),
        param="<<path> | 'fd' | 'cfd'>",
        description="Change current working directory",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
        is_all_no_doc_childs=True,
    )
    dir = ls = Cmd_type_val(
        ("dir", "ls"),
        description="Print files and folders' name in the current working directory",
    )
    mkdir = makedir = Cmd_type_val(
        ("mkdir", "makedir"),
        param="<string>",
        description="Create a new path",
    )
    cls = clear = Cmd_type_val(
        ("cls", "clear"),
        description="Clear screen",
    )
    list = Cmd_type_val(
        ("list",),
        param="<list option>",
        description="Operate Ripper list",
        childs=(
            Cmd_type_val(
                ("Default",), description="Show Ripper list", is_no_prompt_child=True
            ),
            Cmd_type_val(("clear", "clean"), description="Clear Ripper list"),
            Cmd_type_val(
                ("del", "pop"),
                param="<index>",
                description="Delete a Ripper from Ripper list",
            ),
            Cmd_type_val(
                ("sort",),
                param="[n][r]",
                description=(
                    "Sort list\n"  # .
                    "'n': Natural Sorting\n"
                    "'r': Reverse"
                ),
                childs=(Cmd_type_val(("n", "r", "nr")),),
            ),
            Cmd_type_val(
                ("<int> <int>",),
                description="Exchange specified index",
                is_no_prompt_child=True,
            ),
        ),
    )
    run = Cmd_type_val(
        ("run",),
        param="[<run option>] [-multithreading <0 | 1>]",
        description="Run the Ripper from the Ripper list",
        childs=(
            Cmd_type_val(("Default",), description="Only run", is_no_prompt_child=True),
            Cmd_type_val(("exit",), description="Close program when run finished"),
            Cmd_type_val(
                ("shutdown",),
                param="[<sec>]",
                description=(
                    "Shutdown when run finished\n"  # .
                    "Default: 60"
                ),
            ),
            Cmd_type_val(
                ("server",),
                param="[<address>]:[<port>]@[<password>]",
                description="See the corresponding help for details",
            ),
        ),
    )
    server = Cmd_type_val(
        ("server",),
        param="[<address>]:[<port>]@[<password>]",
        description=(
            "Boot web service\n"
            "Default: server localhost:0\n"
            "Client send command 'kill' can exit Ripper's run, note that FFmpeg needs to accept multiple ^C signals to forcibly terminate, and a single ^C signal will wait for the file output to be complete before terminating"
        ),
    )
    config = Cmd_type_val(
        ("config",),
        param="<config option>",
        childs=(
            Cmd_type_val(
                ("regenerate", "clear", "clean", "reset"),
                description="Regenerate config file",
            ),
            Cmd_type_val(
                ("open",),
                description="Open the directory where the config file is located",
            ),
            Cmd_type_val(("list",), description="Show all config adjustable options"),
            Cmd_type_val(
                ("set",),
                param="<key> <val>",
                description=(
                    "Set config\n"  # .
                    "e.g. config set language zh"
                ),
                childs=tuple(Cmd_type_val((k,)) for k in Config_key._member_map_),
            ),
        ),
    )
    prompt = Cmd_type_val(
        ("prompt",),
        param="<prompt option>",
        childs=(
            Cmd_type_val(("history",), description="Show prompt history"),
            Cmd_type_val(("history_clear",), description="Delete history file"),
            Cmd_type_val(
                ("add",),
                param="<name:string> <cmd:string>",
                description=(
                    "Add a custom prompt\n"  # .
                    "e.g. prompt add myprompt echo my prompt"
                ),
            ),
            Cmd_type_val(
                ("del",), param="<name:string>", description="Delete a custom prompt"
            ),
            Cmd_type_val(("show",), description="Show custom prompt"),
        ),
    )
    translate = Cmd_type_val(
        ("translate",),
        param="<files' infix> <target lang tag> [-overwrite]",
        description=(
            "Translate subtitle files\n"
            "e.g. 'translate zh-Hans zh-Hant' will translate all '*.zh-Hans.ass' files into zh-Hant"
        ),
    )
    mediainfo = Cmd_type_val(
        ("mediainfo",),
        param="<<path> | 'fd' | 'cfd'>",
        description="Get the media info by the Media_info class",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
        is_all_no_doc_childs=True,
    )
    assinfo = Cmd_type_val(
        ("assinfo",),
        param="<<path> | 'fd' | 'cfd'> [-use-libass-spec <0|1>] [-show-chars-len <0|1>]",
        description="Get the ass info by the Ass class",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
        is_all_no_doc_childs=True,
    )
    fontinfo = Cmd_type_val(
        ("fontinfo",),
        param="<<path> | 'fd' | 'cfd'>",
        description="Get the font info by the Font class",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
        is_all_no_doc_childs=True,
    )
    Option = Cmd_type_val(
        ("Option",),
        param="...",
        description=(
            "-i <input> -p <preset name> [-o <output>] [-o:dir <dir>] [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-c:a <audio encoder> -b:a <audio bitrate>] [-muxer <muxer> [-r <fps>]] [-run [<run option>]] [...]\n"
            " \n"
            "Add a new Ripper to the Ripper list, you can set the values of the options in preset individually, you can run Ripper list when use -run"
        ),
    )

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        guess_str = s.replace("-", "_").replace(":", "_")
        if guess_str in cls._member_map_:
            return cls[guess_str]
        return None

    @classmethod
    def to_doc(cls) -> str:
        return "\n".join(ct.value.to_doc() for ct in cls)


class Opt_type(enum.Enum):
    _i = Cmd_type_val(
        ("-i",),
        param="<<path>[::<path>[?<path>...]...] | 'fd' | 'cfd'>",
        description=(
            "Input files' pathname or enter 'fd' to use file dialog, 'cfd' to open from the current directory\n"
            "In some cases, it is allowed to use '?' as a delimiter to input multiple into a Ripper, for example, 'preset subset' allows multiple ASS inputs"
        ),
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
        is_all_no_doc_childs=True,
    )
    _o_dir = Cmd_type_val(
        ("-o:dir",),
        param="<path>",
        description="Destination directory of the output file",
    )
    _o = Cmd_type_val(
        ("-o",),
        param="<path>",
        description=(
            "Output file basename's prefix\n"
            "Allow iterators and time formatting for multiple inputs\n"
            '  e.g. "name--?{start=6,padding=4,increment=2}--?{time:%Y.%m.%S}"'
        ),
    )
    _auto_infix = Cmd_type_val(
        ("-auto-infix",),
        param="<0 | 1>",
        description=(
            "If enable, output file name will add auto infix:\n"
            "  no audio: '.v'\n"
            "  with audio: '.va'"
        ),
        childs=(
            Cmd_type_val(("Default:",), param="1", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _preset = _p = Cmd_type_val(
        ("-p", "-preset"),
        param="<string>",
        description=(
            "Setting preset\n"
            "\n"  # .
            "Preset name:\n"
            f"{Preset_name.to_help_string('  ')}"
        ),
        childs=(
            Cmd_type_val(tuple(Preset_name._value2member_map_), is_no_doc_child=True),
        ),
    )
    _pipe = Cmd_type_val(
        ("-pipe",),
        param="<string>",
        description=(
            "Select a vpy file as pipe to input, this vpy must have input global val\n"
            "The input in vspipe: vspipe -a input=<input> filter.vpy"
        ),
    )
    _pipe_gvar = Cmd_type_val(
        ("-pipe:gvar",),
        param="<key>=<val>[:...]",
        description=(
            "Customize the global variables passed to vspipe, and use ':' intervals for multiple variables\n"
            '  e.g. -pipe:gvar "a=1 2 3:b=abc" -> vspipe -a "a=1 2 3" -a "b=abc"'
        ),
    )
    _vf = Cmd_type_val(
        ("-vf",),
        param="<string>",
        description=(
            "Customize FFmpeg's -vf\nUsing it together with -sub is undefined behavior"
        ),
    )
    _sub = Cmd_type_val(
        ("-sub",),
        param="<<path> | 'auto' | 'auto:...'>",
        description=(
            "It use libass to make hard subtitle, input a subtitle pathname when you need hard subtitle\n"
            'It can add multiple subtitles by "::"\n'
            "  e.g. 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n"
            "If use 'auto', the subtitle files with the same prefix will be used\n"
            "'auto:...' can only select which match infix.\n"
            "  e.g. 'auto:zh-Hans:zh-Hant'"
        ),
        childs=(Cmd_type_val(("auto",), is_no_doc_child=True),),
    )
    _only_mux_sub_path = Cmd_type_val(
        ("-only-mux-sub-path",),
        param="<path>",
        description="All subtitles and fonts in this path will be muxed",
    )
    _soft_sub = Cmd_type_val(
        ("-soft-sub",),
        param="<<path>[?<path>...] | 'auto' | 'auto:...'>",
        description=(
            "Mux ASS subtitles in MKV with subset\n"  # .
            "The usage of 'auto' is detailed in '-sub'"
        ),
        childs=(Cmd_type_val(("auto",), is_no_doc_child=True),),
    )
    _subset_font_dir = Cmd_type_val(
        ("-subset-font-dir",),
        param="<<path>[?<path>...]>",
        description=(
            "The fonts directory when subset\n"
            'Default: Prioritize the current directory, followed by folders containing "font" (case-insensitive) within the current directory'
        ),
    )
    _subset_font_in_sub = Cmd_type_val(
        ("-subset-font-in-sub",),
        param="<0 | 1>",
        description="Encode fonts into ASS file instead of standalone files",
        childs=(
            Cmd_type_val(("Default:",), param="0", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _subset_use_win_font = Cmd_type_val(
        ("-subset-use-win-font",),
        param="<0 | 1>",
        description="Use Windows fonts when can not find font in subset-font-dir",
        childs=(
            Cmd_type_val(("Default:",), param="0", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _subset_use_libass_spec = Cmd_type_val(
        ("-subset-use-libass-spec",),
        param="<0 | 1>",
        description=(
            "Use libass specification when subset\n"
            'e.g. "11\\{22}33" ->\n'
            '       "11\\33"    (VSFilter)\n'
            '       "11{22}33" (libass)'
        ),
        childs=(
            Cmd_type_val(("Default:",), param="1", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _subset_drop_non_render = Cmd_type_val(
        ("-subset-drop-non-render",),
        param="<0 | 1>",
        description=(
            "Drop non rendered content such as Comment lines, Name, Effect, etc. in ASS"
        ),
        childs=(
            Cmd_type_val(("Default:",), param="1", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _subset_drop_unkow_data = Cmd_type_val(
        ("-subset-drop-unkow-data",),
        param="<0 | 1>",
        description=(
            "Drop lines that are not in {[Script Info], [V4+ Styles], [Events]} in ASS"
        ),
        childs=(
            Cmd_type_val(("Default:",), param="1", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _subset_strict = Cmd_type_val(
        ("-subset-strict",),
        param="<0 | 1>",
        description="Some error will interrupt subset",
        childs=(
            Cmd_type_val(("Default:",), param="0", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _translate_sub = Cmd_type_val(
        ("-translate-sub",),
        param="<infix>:<language-tag>",
        description=(
            "Temporary generation of subtitle translation files\n"
            "e.g. 'zh-Hans:zh-Hant' will temporary generation of Traditional Chinese subtitles"
        ),
    )
    _c_a = Cmd_type_val(
        ("-c:a",),
        param="<string>",
        description=(
            "Setting audio encoder\n"
            "\n"  # .
            "Audio encoder:\n"
            f"{Audio_codec.to_help_string('  ')}"
        ),
        childs=(
            Cmd_type_val(tuple(Audio_codec._value2member_map_), is_no_doc_child=True),
        ),
    )
    _b_a = Cmd_type_val(
        ("-b:a",),
        param="<string>",
        description="Setting audio bitrate",
        childs=(Cmd_type_val(("Default:",), param="160k", is_no_prompt_child=True),),
    )
    _muxer = Cmd_type_val(
        ("-muxer",),
        param="<string>",
        description=(
            "Setting muxer\n"
            "\n"  # .
            "Muxer:\n"
            f"{Muxer.to_help_string('  ')}"
        ),
        childs=(Cmd_type_val(tuple(Muxer._value2member_map_), is_no_doc_child=True),),
    )
    _track_name = Cmd_type_val(
        ("-track-name",),
        param="<string>",
        description=(
            "Python list[str] format\n"  # .
            "e.g. \"['0:name1', '1:name2']\""
        ),
    )
    _r = _fps = Cmd_type_val(
        ("-r", "-fps"),
        param="<string | 'auto'>",
        description=(
            "Setting FPS when muxing\n"
            "When using auto, the frame rate is automatically obtained from the input video and adsorbed to the nearest preset point"
        ),
        childs=(Cmd_type_val(("auto",), is_no_doc_child=True),),
    )
    _chapters = Cmd_type_val(
        ("-chapters",),
        param="<path>",
        description=(
            "Specify the chapters file to add\n"
            "Supports the same iteration syntax as '-o'"
        ),
    )
    _custom_template = _custom = _custom_format = Cmd_type_val(
        ("-custom", "-custom:format", "-custom:tempate"),
        param="<string>",
        description=(
            "When -preset custom, this option will run\n"
            "String escape: \\34/ -> \", \\39/ -> ', '' -> \"\n"
            'e.g. -custom:format \'-i "{input}" -map {testmap123} "{output}" \' -custom:suffix mp4 -testmap123 0:v:0'
        ),
    )
    _custom_suffix = Cmd_type_val(
        ("-custom:suffix",),
        param="<string>",
        description=(
            "When -preset custom, this option will be used as a suffix for the output file\n"
            'Default: ""'
        ),
    )
    _run = Cmd_type_val(
        ("-run",),
        param="[<string>]",
        description=("Run the Ripper from the Ripper list"),
        childs=(
            Cmd_type_val(("Default",), description="Only run", is_no_prompt_child=True),
            Cmd_type_val(("exit",), description="Close program when run finished"),
            Cmd_type_val(
                ("shutdown",),
                param="[<sec>]",
                description=(
                    "Shutdown when run finished\n"  # .
                    "Default: 60"
                ),
            ),
            Cmd_type_val(
                ("server",),
                param="[<address>]:[<port>]@[<password>]",
                description="See the corresponding help for details",
            ),
        ),
    )
    _ff_params_ff = _ff_params = Cmd_type_val(
        ("-ff-params", "-ff-params:ff"),
        param="<string>",
        description=(
            "Set FFmpeg global options\n"  # .
            "Same as ffmpeg <option> ... -i ..."
        ),
    )
    _ff_params_in = Cmd_type_val(
        ("-ff-params:in",),
        param="<string>",
        description=(
            "Set FFmpeg input options\n"  # .
            "Same as ffmpeg ... <option> -i ..."
        ),
    )
    _ff_params_out = Cmd_type_val(
        ("-ff-params:out",),
        param="<string>",
        description=(
            "Set FFmpeg output options\n"  # .
            "Same as ffmpeg -i ... <option> ..."
        ),
    )
    _hwaccel = Cmd_type_val(
        ("-hwaccel",),
        param="<string>",
        description="Use FFmpeg hwaccel (See 'ffmpeg -hwaccels' for details)",
        childs=(
            Cmd_type_val(("cuda",)),
            Cmd_type_val(("vaapi",)),
            Cmd_type_val(("dxva2",)),
            Cmd_type_val(("qsv",)),
            Cmd_type_val(("d3d11va",)),
            Cmd_type_val(("opencl",)),
            Cmd_type_val(("vulkan",)),
            Cmd_type_val(("d3d12va",)),
            Cmd_type_val(("amf",)),
        ),
    )
    _ss = Cmd_type_val(
        ("-ss",),
        param="<time>",
        description=(
            "Set FFmpeg input file start time\n"  # .
            "Same as ffmpeg -ss <time> -i ..."
        ),
    )
    _t = Cmd_type_val(
        ("-t",),
        param="<time>",
        description=(
            "Set FFmpeg output file duration\n"  # .
            "Same as ffmpeg -i ... -t <time> ..."
        ),
    )
    _hevc_strict = Cmd_type_val(
        ("-hevc-strict",),
        param="<0 | 1>",
        description="When the resolution >= 4K, close HME, and auto reduce the -ref",
        childs=(
            Cmd_type_val(("Default:",), param="1", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _multithreading = Cmd_type_val(
        ("-multithreading",),
        param="<0 | 1>",
        description=(
            "Use multi-threading to run Ripper list, suitable for situations with low performance occupancy\n"
            "e.g. -p subset or -p copy"
        ),
        childs=(
            Cmd_type_val(("Default:",), param="0", is_no_prompt_child=True),
            Cmd_type_val(("0", "1"), is_no_doc_child=True),
        ),
    )
    _quality_detection = Cmd_type_val(
        ("-quality-detection",),
        param="<algorithm>[:<threshold>]",
        description=(
            "Comparison of quality between detection and source after encoding is completed\n"
            "\n"
            "Algorithm:"
        ),
        childs=(
            Cmd_type_val(("ssim",), description="Default threshold: 0.85"),
            Cmd_type_val(("psnr",), description="Default threshold: 30"),
            Cmd_type_val(("vmaf",), description="Default threshold: 80"),
        ),
    )

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        guess_str = s.replace("-", "_").replace(":", "_")
        if guess_str in cls._member_map_:
            return cls[guess_str]
        return None

    @classmethod
    def to_doc(cls) -> str:
        return "\n".join(ct.value.to_doc() for ct in cls)


Cmd_type.help.value.childs = tuple(
    ct.value for ct in itertools.chain(Cmd_type, Opt_type) if ct is not Cmd_type.help
)
Cmd_type.help.value.is_all_no_doc_childs = True


def get_help_doc() -> str:
    from .easyrip_mlang import gettext

    return (
        f"{global_val.PROJECT_NAME}\n{gettext('Version')}: {global_val.PROJECT_VERSION}\n{global_val.PROJECT_URL}\n"
        "\n"
        "\n"
        f"{gettext('Help')}:\n"
        "\n"
        f"{textwrap.indent(gettext("Enter '<cmd> [<param> ...]' to execute Easy Rip commands or any commands that exist in environment.\nOr enter '<option> <param> [<option> <param> ...]' to add Ripper."), '  ')}\n"
        "\n"
        "\n"
        f"{gettext('Easy Rip Commands')}:\n"
        "\n"
        f"{textwrap.indent(Cmd_type.to_doc(), '  ')}\n"
        "\n"
        "\n"
        f"{gettext('Ripper options')}:\n"
        "\n"
        f"{textwrap.indent(Opt_type.to_doc(), '  ')}"
    )


type nested_dict = dict[str, "nested_dict | Completer"]
META_DICT_OPT_TYPE = {
    name: lambda opt=opt: opt.value.param
    for opt in Opt_type
    for name in opt.value.names
}


def _nested_dict_to_nc(n_dict: nested_dict) -> NestedCompleter:
    return NestedCompleter(
        {
            k: (v if isinstance(v, Completer) else _nested_dict_to_nc(v) if v else None)
            for k, v in n_dict.items()
        }
    )


path_completer = SmartPathCompleter()


class CmdCompleter(Completer):
    def __init__(self) -> None:
        self.root: Final[Cmd_type_val] = Cmd_type_val(
            (), childs=tuple(ct.value for ct in Cmd_type if ct != Cmd_type.Option)
        )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        if (text := document.text_before_cursor.lstrip()).startswith("-"):
            return
        words: Final[list[str]] = text.split()

        node: Cmd_type_val = self.root

        def _refresh_node(word: str) -> bool:
            nonlocal node
            for ctv in node.childs:
                for name in ctv.names:
                    if name == word:
                        node = ctv
                        return True
            return False

        for word in words if text.endswith(" ") else words[:-1]:
            if not _refresh_node(word):
                return

        match_word = "" if text.endswith(" ") else words[-1]
        ctv_tuple: Final[tuple[Cmd_type_val, ...]] = tuple(itertools.chain(node.childs))
        name__ctv: Final[dict[str, Cmd_type_val]] = {
            name: ctv for ctv in ctv_tuple for name in ctv.names
        }
        names: Final[tuple[str, ...]] = tuple(name__ctv)
        if match_word in names:
            ctv = name__ctv[match_word]
            yield Completion(
                text=match_word,
                start_position=-len(match_word),
                display_meta=ctv.param,
            )
            for i, desc in enumerate(ctv.description.split("\n")):
                yield Completion(
                    text="",
                    display="" if i else "✔",
                    display_meta=desc,
                )
        else:
            for name in fuzzy_filter_and_sort(names, match_word):
                yield Completion(
                    text=name,
                    start_position=0 if text.endswith(" ") else -len(words[-1]),
                    display=highlight_fuzzy_match(name, match_word),
                    display_meta=name__ctv[name].param,
                )

        if 1 <= len(words) <= 2 and words[0] in {
            *Cmd_type.cd.value.names,
            *Cmd_type.mediainfo.value.names,
            *Cmd_type.assinfo.value.names,
            *Cmd_type.fontinfo.value.names,
        }:
            yield from path_completer.get_completions(
                Document(words[1] if len(words) > 1 else ""), complete_event
            )


class OptCompleter(Completer):
    def __init__(self, *, opt_tree: nested_dict) -> None:
        self.opt_tree: Final[nested_dict] = opt_tree

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor.lstrip()

        words = text.split()

        if len(words) >= 1 and not text.startswith("-"):
            return

        add_comp_words: set[str] = set()
        add_comp_meta_dict: dict[str, str] = {}
        if _preset := tuple(
            words[i + 1]
            for i, word in enumerate(words[:-1])
            for opt_p_name in Opt_type._preset.value.names
            if word == opt_p_name
        ):
            _preset = _preset[-1]
            _preset_name = None
            if _preset in Preset_name._member_map_:
                _preset_name = Preset_name[_preset]
            if _preset_name is not None:
                add_set: set[str] = {
                    f"-{n}" for n in _preset_name.get_param_name_set(set())
                }
                add_comp_words |= add_set
                add_comp_meta_dict |= dict.fromkeys(add_set, f"{_preset} param")

        opt_tree_pos_list: list[nested_dict | Completer] = [self.opt_tree]
        for word in words:
            if isinstance(opt_tree_pos_list[-1], Completer):
                opt_tree_pos_list.append(self.opt_tree.get(word, self.opt_tree))
            else:
                opt_tree_pos_list.append(
                    opt_tree_pos_list[-1].get(
                        word, self.opt_tree.get(word, self.opt_tree)
                    )
                )

        if (
            (opt_tree_pos_list[-1] is not self.opt_tree)
            or (words and words[-1] in add_comp_words)
        ) and not text.endswith(" "):
            # 不在根(上个单词没让这个单词回退到根) or 匹配额外提示
            # 且尾部不是空格
            # 即当前单词完全匹配，输出匹配成功提示

            yield from (
                Completion(
                    text=words[-1],
                    start_position=-len(words[-1]),
                    display_meta=META_DICT_OPT_TYPE.get(words[-1], ""),
                ),
                Completion(
                    text="",
                    display="✔",
                    display_meta=(
                        add_comp_meta_dict[words[-1]]
                        if words[-1] in add_comp_meta_dict
                        else ""
                        if (_opt := Opt_type.from_str(words[-1])) is None
                        else f"{_desc_list[0]}..."
                        if len(_desc_list := _opt.value.description.split("\n")) > 1
                        else _desc_list[0]
                    ),
                ),
            )

        elif isinstance(opt_tree_pos_list[-1], Completer):
            # 上个单词进入独立提示，意味着当前的提示可能会是路径提示

            # 直接使用 PathCompleter 会因为上下文问题失效，所以将上文套进 NestedCompleter
            new_nd: nested_dict = {}
            new_nd_pos: nested_dict = new_nd
            for word in words[:-1]:
                new_nd_pos[word] = new_nd_pos = {}
            new_nd_pos[words[-1]] = opt_tree_pos_list[-1]

            yield from _nested_dict_to_nc(new_nd).get_completions(
                document=document, complete_event=complete_event
            )

        elif len(words) >= 2 and isinstance(opt_tree_pos_list[-2], Completer):
            # 上上个单词进入独立提示

            new_nd: nested_dict = {}
            new_nd_pos: nested_dict = new_nd
            for word in words[:-2]:
                new_nd_pos[word] = new_nd_pos = {}
            new_nd_pos[words[-2]] = opt_tree_pos_list[-2]

            yield from merge_completers(
                (
                    merge_completers(
                        (
                            _nested_dict_to_nc(new_nd),
                            FuzzyCompleter(_nested_dict_to_nc(new_nd), WORD=True),
                        ),
                        deduplicate=True,
                    ),
                    FuzzyCompleter(
                        WordCompleter(
                            words=tuple(opt_tree_pos_list[-1]),
                            meta_dict=META_DICT_OPT_TYPE,
                            WORD=True,  # 匹配标点
                            match_middle=True,
                        ),
                        WORD=False,
                    ),
                )
            ).get_completions(document=document, complete_event=complete_event)

        else:
            # 没有独立提示

            yield from FuzzyCompleter(
                WordCompleter(
                    words=tuple(
                        set(opt_tree_pos_list[-1])
                        | (
                            set()
                            if text.endswith(" ")
                            or len(words) <= 1
                            or isinstance(opt_tree_pos_list[-2], Completer)
                            else set(opt_tree_pos_list[-2])
                        )
                        | add_comp_words
                    ),
                    meta_dict=META_DICT_OPT_TYPE | add_comp_meta_dict,
                    WORD=True,  # 匹配标点
                    match_middle=True,
                ),
                WORD=not text.endswith(" "),
            ).get_completions(document=document, complete_event=complete_event)

import enum
import textwrap
from dataclasses import dataclass
from typing import Self

from . import global_val


@dataclass(slots=True, init=False, eq=False)
class Cmd_type_val:
    name: str
    opt_str: str
    _description: str

    @property
    def description(self) -> str:
        try:
            from .easyrip_mlang import gettext

            return gettext(self._description, is_format=False)

        except ImportError:  # 启动时，原字符串导入翻译文件
            return self._description

    @description.setter
    def description(self, val: str):
        self._description = val

    def __init__(
        self,
        name: str,
        *,
        opt_str: str,
        description: str = "",
    ) -> None:
        self.name = name
        self.opt_str = opt_str
        self.description = description

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cmd_type_val):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def to_doc(self) -> str:
        return (
            f"{self.opt_str}\n{textwrap.indent(self.description, ' │', lambda _: True)}"
        )


class Cmd_type(enum.Enum):
    help = h = Cmd_type_val(
        "help",
        opt_str="h / help [<cmd>]",
        description="Show full help or show the <cmd> help",
    )
    version = v = ver = Cmd_type_val(
        "version",
        opt_str="v / ver / version",
        description="Show version info",
    )
    init = Cmd_type_val(
        "init",
        opt_str="init",
        description=(
            "Execute initialization function\n"
            "e.g. you can execute it after modifying the dynamic translation file"
        ),
    )
    log = Cmd_type_val(
        "log",
        opt_str="log [<LogLevel>] <string>",
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
    )
    _run_any = Cmd_type_val(
        "$",
        opt_str="$ <code>",
        description=(
            "Run code directly from the internal environment.\n"
            "Execute the code string directly after the '$'.\n"
            'The string "\\N" will be changed to real "\\n".\n'
        ),
    )
    exit = Cmd_type_val(
        "exit",
        opt_str="exit",
        description="Exit this program",
    )
    cd = Cmd_type_val(
        "cd",
        opt_str="cd <string>",
        description="Change current working directory",
    )
    dir = Cmd_type_val(
        "dir",
        opt_str="dir",
        description="Print files and folders' name in the current working directory",
    )
    mkdir = makedir = Cmd_type_val(
        "mkdir",
        opt_str="mkdir / makedir <string>",
        description="Create a new path",
    )
    cls = clear = Cmd_type_val(
        "cls",
        opt_str="cls / clear",
        description="Clear screen",
    )
    list = Cmd_type_val(
        "list",
        opt_str="list <list option>",
        description=(
            "Operate Ripper list\n"
            " \n"
            "Default:\n"
            "  Show Ripper list\n"
            " \n"
            "clear / clean:\n"
            "  Clear Ripper list\n"
            " \n"
            "del / pop <index>:\n"
            "  Delete a Ripper from Ripper list\n"
            " \n"
            "sort [n][r]:\n"
            "  Sort list\n"
            "  'n': Natural Sorting\n"
            "  'r': Reverse\n"
            " \n"
            "<int> <int>:\n"
            "  Exchange specified index"
        ),
    )
    run = Cmd_type_val(
        "run",
        opt_str="run [<run option>]",
        description=(
            "Run the Ripper in the Ripper list\n"
            " \n"
            "Default:\n"
            "  Only run\n"
            " \n"
            "exit:\n"
            "  Close program when run finished\n"
            " \n"
            "shutdown [<sec>]:\n"
            "  Shutdown when run finished\n"
            "  Default: 60"
        ),
    )
    server = Cmd_type_val(
        "server",
        opt_str="server [[-a | -address] <address>[:<port>] [[-p | -password] <password>]]",
        description=(
            "Boot web service\n"
            "Default: server localhost:0\n"
            "Client send command 'kill' can exit Ripper's run, note that FFmpeg needs to accept multiple ^C signals to forcibly terminate, and a single ^C signal will wait for the file output to be complete before terminating"
        ),
    )
    config = Cmd_type_val(
        "config",
        opt_str="config <config option>",
        description=(
            "regenerate | clear | clean | reset\n"
            "  Regenerate config file\n"
            "open\n"
            "  Open the directory where the config file is located\n"
            "list\n"
            "  Show all config adjustable options\n"
            "set <key> <val>\n"
            "  Set config\n"
            "  e.g. config set language zh"
        ),
    )
    translate = Cmd_type_val(
        "translate",
        opt_str="translate <files' infix> <target lang tag> [-overwrite]",
        description=(
            "Translate subtitle files\n"
            "e.g. 'translate zh-Hans zh-Hant' will translate all '*.zh-Hans.ass' files into zh-Hant"
        ),
    )
    mediainfo = Cmd_type_val(
        "mediainfo",
        opt_str="mediainfo <path>",
        description="Get the media info by the Media_info class",
    )
    Option = Cmd_type_val(
        "Option",
        opt_str="<Option> ...",
        description=(
            "-i <input> -p <preset name> [-o <output>] [-o:dir <dir>] [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-c:a <audio encoder> -b:a <audio bitrate>] [-muxer <muxer> [-r <fps>]] [-run [<run option>]] [...]\n"
            " \n"
            "Add a new Ripper to the Ripper list, you can set the values of the options in preset individually, you can run Ripper list when use -run"
        ),
    )

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        guess_str = s.replace("-", "_").replace(":", "_")
        if guess_str in cls._member_map_.keys():
            return cls[guess_str]
        return None

    @classmethod
    def to_doc(cls) -> str:
        return "\n\n".join(ct.value.to_doc() for ct in cls)


class Opt_type(enum.Enum):
    _i = Cmd_type_val(
        "-i",
        opt_str="-i <string[::string[?string...]...] | 'fd' | 'cfd'>",
        description=(
            "Input files' pathname or enter 'fd' to use file dialog, 'cfd' to open from the current directory\n"
            "In some cases, it is allowed to use '?' as a delimiter to input multiple into a Ripper, for example, 'preset subset' allows multiple ASS inputs"
        ),
    )
    _o_dir = Cmd_type_val(
        "-o:dir",
        opt_str="-o:dir <string>",
        description="Destination directory of the output file",
    )
    _o = Cmd_type_val(
        "-o",
        opt_str="-o <string>",
        description=(
            "Output file basename's prefix\n"
            "Allow iterators and time formatting for multiple inputs\n"
            '  e.g. "name--?{start=6,padding=4,increment=2}--?{time:%Y.%m.%S}"'
        ),
    )
    _auto_infix = Cmd_type_val(
        "-auto-infix",
        opt_str="-auto-infix <0 | 1>",
        description=(
            "If enable, output file name will add auto infix:\n"
            "  no audio: '.v'\n"
            "  with audio: '.va'\n"
            "Default: 1"
        ),
    )
    _preset = _p = Cmd_type_val(
        "-preset",
        opt_str="-p / -preset <string>",
        description=(
            "Setting preset\n"
            "Preset name:\n"
            "  custom\n"
            "  subset\n"
            "  copy\n"
            "  flac\n"
            "  x264fast x264slow\n"
            "  x265fast4 x265fast3 x265fast2 x265fast x265slow x265full\n"
            "  h264_amf h264_nvenc h264_qsv\n"
            "  hevc_amf hevc_nvenc hevc_qsv\n"
            "  av1_amf av1_nvenc av1_qsv"
        ),
    )
    _pipe = Cmd_type_val(
        "-pipe",
        opt_str="-pipe <string>",
        description=(
            "Select a vpy file as pipe to input, this vpy must have input global val\n"
            "The input in vspipe: vspipe -a input=<input> filter.vpy"
        ),
    )
    _pipe_gvar = Cmd_type_val(
        "-pipe",
        opt_str="-pipe:gvar <key>=<val>[:...]",
        description=(
            "Customize the global variables passed to vspipe, and use ':' intervals for multiple variables\n"
            '  e.g. -pipe:gvar "a=1 2 3:b=abc" -> vspipe -a "a=1 2 3" -a "b=abc"'
        ),
    )
    _vf = Cmd_type_val(
        "-vf",
        opt_str="-vf <string>",
        description=(
            "Customize FFmpeg's -vf\nUsing it together with -sub is undefined behavior"
        ),
    )
    _sub = Cmd_type_val(
        "-sub",
        opt_str="-sub <string | 'auto' | 'auto:...'>",
        description=(
            "It use libass to make hard subtitle, input a subtitle pathname when you need hard subtitle\n"
            'It can add multiple subtitles by "::"\n'
            "  e.g. 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n"
            "If use 'auto', the subtitle files with the same prefix will be used\n"
            "'auto:...' can only select which match infix.\n"
            "  e.g. 'auto:zh-Hans:zh-Hant'"
        ),
    )
    _only_mux_sub_path = Cmd_type_val(
        "-only-mux-sub-path",
        opt_str="-only-mux-sub-path <string>",
        description="All subtitles and fonts in this path will be muxed",
    )
    _soft_sub = Cmd_type_val(
        "-soft-sub",
        opt_str="-soft-sub <string[?string...] | 'auto' | 'auto:...'>",
        description="Mux ASS subtitles in MKV with subset",
    )
    _subset_font_dir = Cmd_type_val(
        "-subset-font-dir",
        opt_str="-subset-font-dir <string[?string...]>",
        description=(
            "The fonts directory when subset\n"
            'Default: Prioritize the current directory, followed by folders containing "font" (case-insensitive) within the current directory'
        ),
    )
    _subset_font_in_sub = Cmd_type_val(
        "-subset-font-in-sub",
        opt_str="-subset-font-in-sub <0 | 1>",
        description=(
            "Encode fonts into ASS file instead of standalone files\n"  # .
            "Default: 0"
        ),
    )
    _subset_use_win_font = Cmd_type_val(
        "-subset-use-win-font",
        opt_str="-subset-use-win-font <0 | 1>",
        description=(
            "Use Windows fonts when can not find font in subset-font-dir\n"  # .
            "Default: 0"
        ),
    )
    _subset_use_libass_spec = Cmd_type_val(
        "-subset-use-libass-spec",
        opt_str="-subset-use-libass-spec <0 | 1>",
        description=(
            "Use libass specification when subset\n"
            'e.g. "11\\{22}33" ->\n'
            '  "11\\33"   (VSFilter)\n'
            '  "11{22}33" (libass)\n'
            "Default: 0"
        ),
    )
    _subset_drop_non_render = Cmd_type_val(
        "-subset-drop-non-render",
        opt_str="-subset-use-libass-spec <0 | 1>",
        description=(
            "Drop non rendered content such as Comment lines, Name, Effect, etc. in ASS\n"
            "Default: 1"
        ),
    )
    _subset_drop_unkow_data = Cmd_type_val(
        "-subset-drop-unkow-data",
        opt_str="-subset-drop-unkow-data <0 | 1>",
        description=(
            "Drop lines that are not in {[Script Info], [V4+ Styles], [Events]} in ASS\n"
            "Default: 1"
        ),
    )
    _subset_strict = Cmd_type_val(
        "-subset-strict",
        opt_str="-subset-strict <0 | 1>",
        description=(
            "Some error will interrupt subset\n"  # .
            "Default: 0"
        ),
    )
    _translate_sub = Cmd_type_val(
        "-translate-sub",
        opt_str="-translate-sub <infix>:<language-tag>",
        description=(
            "Temporary generation of subtitle translation files\n"
            "e.g. 'zh-Hans:zh-Hant' will temporary generation of Traditional Chinese subtitles"
        ),
    )
    _c_a = Cmd_type_val(
        "-c:a",
        opt_str="-c:a <string>",
        description=(
            "Setting audio encoder\n"
            " \n"  # .
            "Audio encoder:\n"
            "  copy\n"
            "  libopus\n"
            "  flac"
        ),
    )
    _b_a = Cmd_type_val(
        "-b:a",
        opt_str="-b:a <string>",
        description="Setting audio bitrate. Default '160k'",
    )
    _muxer = Cmd_type_val(
        "-muxer",
        opt_str="-muxer <string>",
        description=(
            "Setting muxer\n"
            " \n"  # .
            "Muxer:\n"
            "  mp4\n"
            "  mkv\n"
        ),
    )
    _r = _fps = Cmd_type_val(
        "-r",
        opt_str="-r / -fps <string | 'auto'>",
        description=(
            "Setting FPS when muxing\n"
            "When using auto, the frame rate is automatically obtained from the input video and adsorbed to the nearest preset point"
        ),
    )
    _chapters = Cmd_type_val(
        "-chapters",
        opt_str="-chapters <string>",
        description=(
            "Specify the chapters file to add\n"
            "Supports the same iteration syntax as '-o'"
        ),
    )
    _custom_template = _custom = _custom_format = Cmd_type_val(
        "-custom:format",
        opt_str="-custom / -custom:format / -custom:template <string>",
        description=(
            "When -preset custom, this option will run\n"
            "String escape: \\34/ -> \", \\39/ -> ', '' -> \"\n"
            'e.g. -custom:format \'-i "{input}" -map {testmap123} "{output}" \' -custom:suffix mp4 -testmap123 0:v:0'
        ),
    )
    _custom_suffix = Cmd_type_val(
        "-custom:suffix",
        opt_str="-custom:suffix <string>",
        description=(
            "When -preset custom, this option will be used as a suffix for the output file\n"
            'Default: ""'
        ),
    )
    _run = Cmd_type_val(
        "-run",
        opt_str="-run [<string>]",
        description=(
            "Run the Ripper from the Ripper list\n"
            " \n"
            "Default:\n"
            "  Only run\n"
            " \n"
            "exit:\n"
            "  Close program when run finished\n"
            " \n"
            "shutdown [<sec>]:\n"
            "  Shutdown when run finished\n"
            "  Default: 60\n"
        ),
    )
    _ff_params_ff = _ff_params = Cmd_type_val(
        "-ff-params:ff",
        opt_str="-ff-params / -ff-params:ff <string>",
        description=(
            "Set FFmpeg global options\n"  # .
            "Same as ffmpeg <option> ... -i ..."
        ),
    )
    _ff_params_in = Cmd_type_val(
        "-ff-params:in",
        opt_str="-ff-params:in <string>",
        description=(
            "Set FFmpeg input options\n"  # .
            "Same as ffmpeg ... <option> -i ..."
        ),
    )
    _ff_params_out = Cmd_type_val(
        "-ff-params:out",
        opt_str="-ff-params:out <string>",
        description=(
            "Set FFmpeg output options\n"  # .
            "Same as ffmpeg -i ... <option> ..."
        ),
    )
    _hwaccel = Cmd_type_val(
        "-hwaccel",
        opt_str="-hwaccel <string>",
        description="Use FFmpeg hwaccel (See 'ffmpeg -hwaccels' for details)",
    )
    _ss = Cmd_type_val(
        "-ss",
        opt_str="-ss <time>",
        description=(
            "Set FFmpeg input file start time\n"  # .
            "Same as ffmpeg -ss <time> -i ..."
        ),
    )
    _t = Cmd_type_val(
        "-t",
        opt_str="-t <time>",
        description=(
            "Set FFmpeg output file duration\n"  # .
            "Same as ffmpeg -i ... -t <time> ..."
        ),
    )
    _hevc_strict = Cmd_type_val(
        "-hevc-strict",
        opt_str="-hevc-strict <0 | 1>",
        description=(
            "Auto reduce the --ref\n"  # .
            "When the resolution >= 4k, close HME\n"
            "Default: 1"
        ),
    )

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        guess_str = s.replace("-", "_").replace(":", "_")
        if guess_str in cls._member_map_.keys():
            return cls[guess_str]
        return None

    @classmethod
    def to_doc(cls) -> str:
        return "\n\n".join(ct.value.to_doc() for ct in cls)


def get_help_doc() -> str:
    from .easyrip_mlang import gettext

    return (
        f"{global_val.PROJECT_NAME}\n{gettext('Version')}: {global_val.PROJECT_VERSION}\n{global_val.PROJECT_URL}\n"
        "\n"
        "\n"
        f"{gettext('Help')}:\n"
        "\n"
        f"  {gettext('You can input command or use command-line arguments to run.')}\n"
        "\n"
        "\n"
        f"{gettext('Commands')}:\n"
        "\n"
        f"{textwrap.indent(Cmd_type.to_doc(), '  ')}"
        "\n"
        "\n"
        f"{gettext('Ripper options')}:\n"
        "\n"
        f"{textwrap.indent(Opt_type.to_doc(), '  ')}"
    )

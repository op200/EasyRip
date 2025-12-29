import enum
import itertools
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Self, final

from prompt_toolkit.completion import (
    Completer,
    DeduplicateCompleter,
    FuzzyCompleter,
    FuzzyWordCompleter,
    NestedCompleter,
    WordCompleter,
    merge_completers,
)
from prompt_toolkit.completion.base import CompleteEvent, Completion
from prompt_toolkit.document import Document

from . import global_val
from .easyrip_config.config_key import Config_key
from .ripper.param import PRESET_OPT_NAME, Audio_codec, Preset_name


@final
@dataclass(slots=True, init=False, eq=False)
class Cmd_type_val:
    names: tuple[str, ...]
    _param: str
    _description: str
    childs: tuple["Cmd_type_val", ...]

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
    ) -> None:
        self.names = names
        self.param = param
        self.description = description
        self.childs = childs

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cmd_type_val):
            return self.names == other.names
        return False

    def __hash__(self) -> int:
        return hash(self.names)

    def to_doc(self) -> str:
        return f"{' / '.join(self.names)} {self.param}\n{textwrap.indent(self.description, ' │ ', lambda _: True)}"


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
        childs=(
            Cmd_type_val(("clear", "clean")),
            Cmd_type_val(("del", "pop")),
            Cmd_type_val(("sort",), childs=(Cmd_type_val(("n", "r", "nr")),)),
        ),
    )
    run = Cmd_type_val(
        ("run",),
        param="[<run option>] [-multithreading <0 | 1>]",
        description=(
            "Run the Ripper in the Ripper list\n"
            "\n"
            "Default:\n"
            "  Only run\n"
            "\n"
            "exit:\n"
            "  Close program when run finished\n"
            "\n"
            "shutdown [<sec>]:\n"
            "  Shutdown when run finished\n"
            "  Default: 60\n"
            "\n"
            "server [<address>]:[<port>]@[<password>]:\n"
            "  See the corresponding help for details"
        ),
        childs=(
            Cmd_type_val(("exit",)),
            Cmd_type_val(("shutdown",)),
            Cmd_type_val(("server",)),
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
        description=(
            "regenerate | clear | clean\n"
            "  Regenerate config file\n"
            "open\n"
            "  Open the directory where the config file is located\n"
            "list\n"
            "  Show all config adjustable options\n"
            "set <key> <val>\n"
            "  Set config\n"
            "  e.g. config set language zh"
        ),
        childs=(
            Cmd_type_val(("regenerate", "clear", "clean")),
            Cmd_type_val(("open",)),
            Cmd_type_val(("list",)),
            Cmd_type_val(
                ("set",),
                childs=tuple(Cmd_type_val((k,)) for k in Config_key._member_map_),
            ),
        ),
    )
    prompt = Cmd_type_val(
        ("prompt",),
        param="<prompt option>",
        description=(
            "history\n"  # .
            "  Show prompt history\n"
            "clear | clean\n"
            "  Delete history file"
        ),
        childs=(
            Cmd_type_val(("history",)),
            Cmd_type_val(("clear", "clean")),
        ),
    )
    translate = Cmd_type_val(
        ("translate",),
        param="<files' infix> <target lang tag> [-overwrite]",
        description=(
            "Translate subtitle files\n"
            "e.g. 'translate zh-Hans zh-Hant' will translate all '*.zh-Hans.ass' files into zh-Hant"
        ),
        childs=(Cmd_type_val(("-overwrite",)),),
    )
    mediainfo = Cmd_type_val(
        ("mediainfo",),
        param="<<path> | 'fd' | 'cfd'>",
        description="Get the media info by the Media_info class",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
    )
    fontinfo = Cmd_type_val(
        ("fontinfo",),
        param="<<path> | 'fd' | 'cfd'>",
        description="Get the font info by the Font class",
        childs=(
            Cmd_type_val(("fd",)),
            Cmd_type_val(("cfd",)),
        ),
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
        return "\n\n".join(ct.value.to_doc() for ct in cls)


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
            "  with audio: '.va'\n"
            "Default: 1"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _preset = _p = Cmd_type_val(
        ("-p", "-preset"),
        param="<string>",
        description=(
            "Setting preset\n"
            "Preset name:\n"  # .
            f"{Preset_name.to_help_string('  ')}"
        ),
        childs=(Cmd_type_val(tuple(Preset_name._value2member_map_)),),
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
        childs=(Cmd_type_val(("auto",)),),
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
        childs=(Cmd_type_val(("auto",)),),
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
        description=(
            "Encode fonts into ASS file instead of standalone files\n"  # .
            "Default: 0"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _subset_use_win_font = Cmd_type_val(
        ("-subset-use-win-font",),
        param="<0 | 1>",
        description=(
            "Use Windows fonts when can not find font in subset-font-dir\n"  # .
            "Default: 0"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _subset_use_libass_spec = Cmd_type_val(
        ("-subset-use-libass-spec",),
        param="<0 | 1>",
        description=(
            "Use libass specification when subset\n"
            'e.g. "11\\{22}33" ->\n'
            '  "11\\33"   (VSFilter)\n'
            '  "11{22}33" (libass)\n'
            "Default: 0"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _subset_drop_non_render = Cmd_type_val(
        ("-subset-drop-non-render",),
        param="<0 | 1>",
        description=(
            "Drop non rendered content such as Comment lines, Name, Effect, etc. in ASS\n"
            "Default: 1"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _subset_drop_unkow_data = Cmd_type_val(
        ("-subset-drop-unkow-data",),
        param="<0 | 1>",
        description=(
            "Drop lines that are not in {[Script Info], [V4+ Styles], [Events]} in ASS\n"
            "Default: 1"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _subset_strict = Cmd_type_val(
        ("-subset-strict",),
        param="<0 | 1>",
        description=(
            "Some error will interrupt subset\n"  # .
            "Default: 0"
        ),
        childs=(Cmd_type_val(("0", "1")),),
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
            "Audio encoder:\n"  # .
            f"{Audio_codec.to_help_string('  ')}"
        ),
        childs=(Cmd_type_val(tuple(Audio_codec._value2member_map_)),),
    )
    _b_a = Cmd_type_val(
        ("-b:a",),
        param="<string>",
        description="Setting audio bitrate. Default '160k'",
    )
    _muxer = Cmd_type_val(
        ("-muxer",),
        param="<string>",
        description=(
            "Setting muxer\n"
            " \n"  # .
            "Muxer:\n"
            "  mp4\n"
            "  mkv\n"
        ),
    )
    _r = _fps = Cmd_type_val(
        ("-r", "-fps"),
        param="<string | 'auto'>",
        description=(
            "Setting FPS when muxing\n"
            "When using auto, the frame rate is automatically obtained from the input video and adsorbed to the nearest preset point"
        ),
        childs=(Cmd_type_val(("auto",)),),
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
        description=(
            "Run the Ripper from the Ripper list\n"
            "\n"
            "Default:\n"
            "  Only run\n"
            "\n"
            "exit:\n"
            "  Close program when run finished\n"
            "\n"
            "shutdown [<sec>]:\n"
            "  Shutdown when run finished\n"
            "  Default: 60\n"
            "\n"
            "server [<address>]:[<port>]@[<password>]:\n"
            "  See the corresponding help for details"
        ),
        childs=(
            Cmd_type_val(("exit",)),
            Cmd_type_val(("shutdown",)),
            Cmd_type_val(("server",)),
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
        description=(
            "When the resolution >= 4K, close HME, and auto reduce the -ref\n"  # .
            "Default: 1"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )
    _multithreading = Cmd_type_val(
        ("-multithreading",),
        param="<0 | 1>",
        description=(
            "Use multi-threading to run Ripper list, suitable for situations with low performance occupancy\n"
            "e.g. -p subset or -p copy"
        ),
        childs=(Cmd_type_val(("0", "1")),),
    )

    @classmethod
    def from_str(cls, s: str) -> Self | None:
        guess_str = s.replace("-", "_").replace(":", "_")
        if guess_str in cls._member_map_:
            return cls[guess_str]
        return None

    @classmethod
    def to_doc(cls) -> str:
        return "\n\n".join(ct.value.to_doc() for ct in cls)


Cmd_type.help.value.childs = tuple(
    ct.value for ct in itertools.chain(Cmd_type, Opt_type) if ct is not Cmd_type.help
)


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
META_DICT_CMD_TYPE = {
    name: lambda opt=opt: opt.value.param
    for opt in Cmd_type
    for name in opt.value.names
}


def _nested_dict_to_nc(n_dict: nested_dict) -> NestedCompleter:
    return NestedCompleter(
        {
            k: (v if isinstance(v, Completer) else _nested_dict_to_nc(v) if v else None)
            for k, v in n_dict.items()
        }
    )


class CmdCompleter(NestedCompleter):
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        words = text.split()
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term) :].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                yield from completer.get_completions(new_document, complete_event)

        elif words and (_cmd := Cmd_type.from_str(words[-1])) is not None:
            yield from (
                Completion(
                    text=words[-1],
                    start_position=-len(words[-1]),
                    display_meta=META_DICT_CMD_TYPE.get(words[-1], ""),
                ),
                Completion(
                    text="",
                    display="✔",
                    display_meta=(
                        f"{_desc_list[0]}..."
                        if len(_desc_list := _cmd.value.description.split("\n")) > 1
                        else _desc_list[0]
                    ),
                ),
            )

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            # custom
            completer = FuzzyWordCompleter(
                tuple(self.options),
                meta_dict=META_DICT_CMD_TYPE,  # pyright: ignore[reportArgumentType]
                WORD=True,
            )
            yield from completer.get_completions(document, complete_event)


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
            if _preset_name is not None and _preset_name in PRESET_OPT_NAME:
                add_set: set[str] = {f"-{n}" for n in PRESET_OPT_NAME[_preset_name]}
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
            or (words[-1] in add_comp_words)
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
                    DeduplicateCompleter(
                        merge_completers(
                            (
                                _nested_dict_to_nc(new_nd),
                                FuzzyCompleter(_nested_dict_to_nc(new_nd), WORD=True),
                            )
                        )
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

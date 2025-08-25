from dataclasses import dataclass
from itertools import zip_longest
import os
from pathlib import Path
import re
from datetime import datetime
import enum
import shutil
from time import sleep
from threading import Thread
from typing import Iterable

from .. import easyrip_web
from ..easyrip_log import log
from ..easyrip_mlang import gettext, Global_lang_val
from . import media_info
from .utils import get_base62_time
from .font_subset import subset


FF_PROGRESS_LOG_FILE = Path("FFProgress.log")
FF_REPORT_LOG_FILE = Path("FFReport.log")


class Ripper:
    ripper_list: list["Ripper"] = []

    @staticmethod
    def add_ripper(
        input_path: Iterable[str | Path],
        output_prefix: Iterable[str | None],
        output_dir: str | None,
        option: "Option | PresetName",
        option_map: dict[str, str],
    ):
        try:
            Ripper.ripper_list.append(
                Ripper(input_path, output_prefix, output_dir, option, option_map)
            )
        except Exception as e:
            log.error("Failed to add ripper: {}", e, deep=True)

    class PresetName(enum.Enum):
        custom = "custom"

        copy = "copy"

        subset = "subset"

        flac = "flac"

        x264fast = "x264fast"
        x264slow = "x264slow"

        x265fast4 = "x265fast4"
        x265fast3 = "x265fast3"
        x265fast2 = "x265fast2"
        x265fast = "x265fast"
        x265slow = "x265slow"
        x265full = "x265full"

        h264_amf = "h264_amf"
        h264_nvenc = "h264_nvenc"
        h264_qsv = "h264_qsv"

        hevc_amf = "hevc_amf"
        hevc_nvenc = "hevc_nvenc"
        hevc_qsv = "hevc_qsv"

        av1_amf = "av1_amf"
        av1_nvenc = "av1_nvenc"
        av1_qsv = "av1_qsv"

        @classmethod
        def _missing_(cls, value: object):
            default = cls.custom
            log.error(
                "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                value,
                cls.__name__,
                default,
                list(cls.__members__.keys()),
            )
            return default

    class AudioCodec(enum.Enum):
        copy = "copy"
        libopus = "libopus"
        flac = "flac"

        @classmethod
        def _missing_(cls, value: object):
            default = cls.copy
            log.error(
                "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                value,
                cls.__name__,
                default,
                list(cls.__members__.keys()),
            )
            return default

    class Muxer(enum.Enum):
        mp4 = "mp4"
        mkv = "mkv"

        @classmethod
        def _missing_(cls, value: object):
            default = cls.mkv
            log.error(
                "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                value,
                cls.__name__,
                default,
                list(cls.__members__.keys()),
            )
            return default

    @dataclass
    class Option:
        preset_name: "Ripper.PresetName"
        encoder_format_str: str
        audio_encoder: "Ripper.AudioCodec | None"
        muxer: "Ripper.Muxer | None"
        muxer_format_str: str

        def __str__(self):
            return f"  preset_name = {self.preset_name}\n  option_format = {self.encoder_format_str}"

    input_path_list: list[Path]
    output_prefix_list: list[str]
    output_dir: str
    option: Option
    option_map: dict[str, str]

    preset_name: PresetName

    info: media_info.Media_info

    _progress: dict
    """
    .frame_count : int 总帧数
    .frame : int 已输出帧数
    .fps : float 当前输出帧率

    .duration : float 视频总时长 s
    .out_time_us : int 已输出时长 us

    .speed : float 当前输出速率 倍
    """

    def __init__(
        self,
        input_path: Iterable[str | Path],
        output_prefix: Iterable[str | None],
        output_dir: str | None,
        option: Option | PresetName,
        option_map: dict[str, str],
    ):
        self.input_path_list = [Path(path) for path in input_path]

        self.info = media_info.get_media_info(self.input_path_list[0])

        self.output_prefix_list = [
            path[0] or (path[1] or self.input_path_list[-1]).stem
            for path in zip_longest(output_prefix, self.input_path_list, fillvalue=None)
        ]

        self.output_dir = output_dir or os.path.realpath(os.getcwd())

        self.option_map = option_map.copy()

        # 内封字幕时强制修改 muxer
        if (
            self.option_map.get("soft-sub") or self.option_map.get("only-mux-sub-path")
        ) and self.option_map.get("muxer") != "mkv":
            self.option_map["muxer"] = "mkv"
            log.info(
                "The muxer must be 'mkv' when mux subtitle and font. Auto modified"
            )

        if isinstance(option, Ripper.PresetName):
            self.preset_name = option
            self.option = self.preset_name_to_option(option)
        else:
            self.preset_name = Ripper.PresetName.custom
            self.option = option

        self._progress = {}

    def __str__(self):
        return (
            f"-i {self.input_path_list[0]} -o {self.output_prefix_list[0]} -o:dir {self.output_dir} -preset {self.option.preset_name.value} {' '.join((f'-{key} {val}' for key, val in self.option_map.items()))}\n"
            "  option:  {\n"
            f"  {str(self.option).replace('\n', '\n  ')}\n"
            "  }\n"
            f"  option_map: {self.option_map}"
        )

    def preset_name_to_option(self, preset_name: PresetName) -> Option:
        if (
            force_fps := self.option_map.get("r") or self.option_map.get("fps")
        ) == "auto":
            try:
                force_fps = self.info.r_frame_rate[0] / self.info.r_frame_rate[1]
                if 23.975 < force_fps < 23.977:
                    force_fps = "24000/1001"
                elif 29.969 < force_fps < 29.971:
                    force_fps = "30000/1001"
                elif 47.951 < force_fps < 47.953:
                    force_fps = "48000/1001"
                elif 59.939 < force_fps < 59.941:
                    force_fps = "60000/1001"
            except Exception as e:
                log.error(f"{repr(e)} {e}", deep=True)

        # Path
        vpy_pathname = self.option_map.get("pipe")

        if vpy_pathname and not os.path.exists(vpy_pathname):
            log.error('The file "{}" does not exist', vpy_pathname)

        is_pipe_input = bool(self.input_path_list[0].suffix == ".vpy" or vpy_pathname)

        ff_input_option: list[str]
        if is_pipe_input:
            ff_input_option = ["-"]
        else:
            ff_input_option = ['"{input}"']
        ff_stream_option: list[str] = ["0:v"]
        ff_vf_option: list[str] = (
            s.split(",") if (s := self.option_map.get("vf")) else []
        )

        if sub_pathname := self.option_map.get("sub"):
            sub_pathname = f"'{sub_pathname.replace('\\', '/').replace(':', '\\:')}'"
            ff_vf_option.append(f"ass={sub_pathname}")

        # Audio
        if audio_encoder := self.option_map.get("c:a"):
            _audio_encoder_str = audio_encoder
            audio_encoder = Ripper.AudioCodec(audio_encoder)
            if is_pipe_input:
                ff_input_option.append('"{input}"')
                ff_stream_option.append("1:a")
            else:
                ff_stream_option.append("0:a")

            _encoder_str = (
                ""
                if audio_encoder == Ripper.AudioCodec.copy
                and self.preset_name == Ripper.PresetName.copy
                else "-an "
                if audio_encoder == Ripper.AudioCodec.flac
                else f"-c:a {_audio_encoder_str} "
            )
            _bitrate_str = (
                ""
                if audio_encoder == Ripper.AudioCodec.copy
                else f"-b:a {self.option_map.get('b:a') or '160k'}"
            )
            audio_option = f"{_encoder_str}{_bitrate_str} "

        else:
            audio_encoder = None
            audio_option = ""

        # Muxer
        if muxer := self.option_map.get("muxer"):
            muxer = Ripper.Muxer(muxer)

            match muxer:
                case Ripper.Muxer.mp4:
                    muxer_format_str = (
                        ' && mp4box -add "{output}" -new "{output}" '
                        + (
                            f"-chap {chapters} "
                            if (chapters := self.option_map.get("chapters"))
                            else ""
                        )
                        + (
                            ""
                            if self.preset_name == Ripper.PresetName.flac
                            else (
                                "&& mp4fpsmod "
                                + (f"-r 0:{force_fps}" if force_fps else "")
                                + ' -i "{output}"'
                            )
                        )
                    )

                case Ripper.Muxer.mkv:
                    if (
                        only_mux_sub_path := self.option_map.get("only-mux-sub-path")
                    ) is not None:
                        only_mux_sub_path = Path(only_mux_sub_path)
                        if not only_mux_sub_path.is_dir():
                            log.error("It is not a dir: {}", only_mux_sub_path)
                            only_mux_sub_path = None

                    muxer_format_str = (
                        ' && mkvpropedit "{output}" --add-track-statistics-tags && mkvmerge -o "{output}.temp.mkv" "{output}" && mkvmerge -o "{output}" '
                        + (
                            f"--default-duration 0:{force_fps}fps --fix-bitstream-timing-information 0:1 "
                            if force_fps and only_mux_sub_path is None
                            else ""
                        )
                        + (
                            f"--chapters {chapters} "
                            if (chapters := self.option_map.get("chapters"))
                            else ""
                        )
                        + (
                            " ".join(
                                (
                                    ""
                                    if len(
                                        affixes := _file.stem.rsplit(".", maxsplit=1)
                                    )
                                    == 1
                                    else "--attach-file "
                                    if _file.suffix in {".otf", ".ttf", ".ttc"}
                                    else f"--language 0:{affixes[1]} --track-name 0:{Global_lang_val.language_tag_to_local_str(affixes[1])} "
                                )
                                + f'"{_file.absolute()}"'
                                for _file in only_mux_sub_path.iterdir()
                                if _file.suffix
                                in {
                                    ".srt",
                                    ".ass",
                                    ".ssa",
                                    ".sup",
                                    ".idx",
                                    ".otf",
                                    ".ttf",
                                    ".ttc",
                                }
                            )
                            if only_mux_sub_path
                            else ""
                        )
                        + ' --no-global-tags --no-track-tags --default-track-flag 0 "{output}.temp.mkv" && del /Q "{output}.temp.mkv"'
                    )

        else:
            muxer = None
            muxer_format_str = ""

        vspipe_input: str = ""
        pipe_gvar_list = [
            s for s in self.option_map.get("pipe:gvar", "").split(":") if s
        ]
        pipe_gvar_dict = {
            s.split("=")[0]: s.split("=")[1] for s in pipe_gvar_list if "=" in s
        }
        if sub_pathname:
            pipe_gvar_dict["subtitle"] = sub_pathname

        if self.input_path_list[0].suffix == ".vpy":
            vspipe_input = f'vspipe -c y4m {" ".join(f'-a "{k}={v}"' for k, v in pipe_gvar_dict.items())} "{{input}}" - | '
        elif vpy_pathname:
            vspipe_input = f'vspipe -c y4m {" ".join(f'-a "{k}={v}"' for k, v in pipe_gvar_dict.items())} -a "input={{input}}" "{vpy_pathname}" - | '

        hwaccel = (
            f"-hwaccel {hwaccel}" if (hwaccel := self.option_map.get("hwaccel")) else ""
        )

        ffparams_ff = self.option_map.get("ff-params:ff") or self.option_map.get(
            "ff-params", ""
        )
        ffparams_in = self.option_map.get("ff-params:in", "")
        ffparams_out = self.option_map.get("ff-params:out", "")
        if _ss := self.option_map.get("ss"):
            ffparams_in += f" -ss {_ss}"
        if _t := self.option_map.get("t"):
            ffparams_out += f" -t {_t}"
        if _preset := self.option_map.get("v:preset"):
            ffparams_out += f" -preset {_preset}"

        FFMPEG_HEADER = f"ffmpeg {'-hide_banner ' if self.option_map.get('_sub_ripper_num') else ''}-progress {FF_PROGRESS_LOG_FILE} -report {ffparams_ff} {ffparams_in}"

        match preset_name:
            case Ripper.PresetName.custom:
                if not (
                    encoder_format_str := self.option_map.get(
                        "custom:format",
                        self.option_map.get(
                            "custom:template", self.option_map.get("custom")
                        ),
                    )
                ):
                    log.warning(
                        "The preset custom must have custom:format or custom:template"
                    )
                    encoder_format_str = ""

                else:
                    if encoder_format_str.startswith("''''"):
                        encoder_format_str = encoder_format_str[4:]
                    else:
                        encoder_format_str = encoder_format_str.replace("''", '"')
                    encoder_format_str = (
                        encoder_format_str.replace("\\34/", '"')
                        .replace("\\39/", "'")
                        .format_map(
                            self.option_map | {"input": "{input}", "output": "{output}"}
                        )
                    )

            case Ripper.PresetName.copy:
                hwaccel = (
                    f"-hwaccel {hwaccel}"
                    if (hwaccel := self.option_map.get("hwaccel"))
                    else ""
                )

                encoder_format_str = (
                    f"{FFMPEG_HEADER} {hwaccel} "
                    + '-i "{input}" -c copy '
                    + f"{' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + f"{audio_option} {ffparams_out} "
                    + '"{output}"'
                )

                match self.option_map.get("c:a"):
                    case None | "flac":
                        if muxer == Ripper.Muxer.mp4:
                            encoder_format_str = 'mp4box -add "{input}" -new "{output}"'
                            for _audio_info in self.info.audio_info:
                                encoder_format_str += f" -rem {_audio_info.index + 1}"
                        else:
                            encoder_format_str = (
                                'mkvmerge -o "{output}" --no-audio "{input}"'
                            )
                    case "copy":
                        encoder_format_str = (
                            'mp4box -add "{input}" -new "{output}"'
                            if muxer == Ripper.Muxer.mp4
                            else 'mkvmerge -o "{output}" "{input}"'
                        )

            case Ripper.PresetName.flac:
                _ff_encode_str: str = ""
                _flac_encode_str: str = ""
                _mux_flac_input_list = list[str]()
                # _mux_flac_map_str: str = ""
                _del_flac_str: str = ""

                for _audio_info in self.info.audio_info:
                    _encoder: str = (
                        "pcm_s24le"
                        if (
                            _audio_info.bits_per_raw_sample == 24
                            or _audio_info.bits_per_sample == 24
                        )
                        else {
                            "u8": "pcm_u8",
                            "s16": "pcm_s16le",
                            "s32": "pcm_s32le",
                            "flt": "pcm_s32le",
                            "dbl": "pcm_s32le",
                            "u8p": "pcm_u8",
                            "s16p": "pcm_s16le",
                            "s32p": "pcm_s32le",
                            "fltp": "pcm_s32le",
                            "dblp": "pcm_s32le",
                            "s64": "pcm_s32le",
                            "s64p": "pcm_s32le",
                        }.get(_audio_info.sample_fmt, "pcm_s32le")
                    )

                    _new_output_str: str = f"{{output}}.{_audio_info.index}.temp"

                    _ff_encode_str += (
                        f"-map 0:{_audio_info.index} -c:a {_encoder} {ffparams_out} "
                        f'"{_new_output_str}.wav" '
                    )
                    _flac_encode_str += (
                        f"&& flac -j 32 -8 -e -p -l {'19' if _audio_info.sample_rate > 48000 else '12'} "
                        f'-o "{_new_output_str}.flac" "{_new_output_str}.wav" && del /Q "{_new_output_str}.wav" '
                    )

                    _mux_flac_input_list.append(f'"{_new_output_str}.flac"')

                    _del_flac_str += f'&& del /Q "{_new_output_str}.flac" '

                match len(_mux_flac_input_list):
                    case 0:
                        raise Exception(f'No audio in "{self.input_path_list[0]}"')

                    case 1 if muxer is None:
                        encoder_format_str = (
                            FFMPEG_HEADER + ' -i "{input}" '
                            f"{_ff_encode_str} {_flac_encode_str} "
                            f"&& {'copy' if os.name == 'nt' else 'cp'} {_mux_flac_input_list[0]} "
                            + '"{output}" '
                            + _del_flac_str
                        )

                    case _:
                        _mux_str = (
                            f"mp4box -add {' -add '.join(_mux_flac_input_list)}"
                            + ' -new "{output}" '
                            if muxer == Ripper.Muxer.mp4
                            else 'mkvmerge -o "{output}" '
                            + " ".join(_mux_flac_input_list)
                        )
                        encoder_format_str = (
                            FFMPEG_HEADER + ' -i "{input}" '
                            f"{_ff_encode_str} {_flac_encode_str} "
                            f"&& {_mux_str} " + _del_flac_str
                        )

            case Ripper.PresetName.x264fast | Ripper.PresetName.x264slow:
                match preset_name:
                    case Ripper.PresetName.x264fast:
                        _option_map = {
                            "threads": self.option_map.get("threads", "auto"),
                            # Select
                            "crf": self.option_map.get("crf", "20"),
                            "psy-rd": self.option_map.get("psy-rd", "0.6,0.15"),
                            "qcomp": self.option_map.get("qcomp", "0.66"),
                            "keyint": self.option_map.get("keyint", "250"),
                            "deblock": self.option_map.get("deblock", "0,0"),
                            # Default
                            "qpmin": self.option_map.get("qpmin", "8"),
                            "qpmax": self.option_map.get("qpmax", "32"),
                            "bframes": self.option_map.get("bframes", "8"),
                            "ref": self.option_map.get("ref", "4"),
                            "subme": self.option_map.get("subme", "5"),
                            "me": self.option_map.get("me", "hex"),
                            "merange": self.option_map.get("merange", "16"),
                            "aq-mode": self.option_map.get("aq-mode", "1"),
                            "rc-lookahead": self.option_map.get("rc-lookahead", "60"),
                            "min-keyint": self.option_map.get("min-keyint", "2"),
                            "trellis": self.option_map.get("trellis", "1"),
                            "fast-pskip": self.option_map.get("fast-pskip", "1"),
                            # No change
                            "weightb": "1",
                            **{
                                k: v
                                for k, v in [
                                    s.split("=")
                                    for s in str(
                                        self.option_map.get("x264-params", "")
                                    ).split(":")
                                    if s != ""
                                ]
                            },
                        }
                    case Ripper.PresetName.x264slow:
                        _option_map = {
                            "threads": self.option_map.get("threads", "auto"),
                            # Select
                            "crf": self.option_map.get("crf", "21"),
                            "psy-rd": self.option_map.get("psy-rd", "0.6,0.15"),
                            "qcomp": self.option_map.get("qcomp", "0.66"),
                            "keyint": self.option_map.get("keyint", "250"),
                            "deblock": self.option_map.get("deblock", "-1,-1"),
                            # Default
                            "qpmin": self.option_map.get("qpmin", "8"),
                            "qpmax": self.option_map.get("qpmax", "32"),
                            "bframes": self.option_map.get("bframes", "16"),
                            "ref": self.option_map.get("ref", "8"),
                            "subme": self.option_map.get("subme", "7"),
                            "me": self.option_map.get("me", "umh"),
                            "merange": self.option_map.get("merange", "24"),
                            "aq-mode": self.option_map.get("aq-mode", "3"),
                            "rc-lookahead": self.option_map.get("rc-lookahead", "120"),
                            "min-keyint": self.option_map.get("min-keyint", "2"),
                            "trellis": self.option_map.get("trellis", "2"),
                            "fast-pskip": self.option_map.get("fast-pskip", "0"),
                            # No change
                            "weightb": "1",
                            **{
                                k: v
                                for k, v in [
                                    s.split("=")
                                    for s in str(
                                        self.option_map.get("x264-params", "")
                                    ).split(":")
                                    if s != ""
                                ]
                            },
                        }

                _param = ":".join((f"{key}={val}" for key, val in _option_map.items()))

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + f"{audio_option} -c:v libx264 {'' if is_pipe_input else '-pix_fmt yuv420p'} -x264-params "
                    + f'"{_param}" {ffparams_out} '
                    + (f' -vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case (
                Ripper.PresetName.x265fast4
                | Ripper.PresetName.x265fast3
                | Ripper.PresetName.x265fast2
                | Ripper.PresetName.x265fast
                | Ripper.PresetName.x265slow
                | Ripper.PresetName.x265full
            ):
                _default_option_map = {
                    "crf": "20",
                    "qpmin": "6",
                    "qpmax": "32",
                    "rd": "3",
                    "psy-rd": "2",
                    "rdoq-level": "0",
                    "psy-rdoq": "0",
                    "qcomp": "0.68",
                    "keyint": "250",
                    "min-keyint": "2",
                    "deblock": "0,0",
                    "me": "umh",
                    "merange": "57",
                    "hme": "1",
                    "hme-search": "hex,hex,hex",
                    "hme-range": "16,57,92",
                    "aq-mode": "2",
                    "aq-strength": "1",
                    "tu-intra-depth": "1",
                    "tu-inter-depth": "1",
                    "limit-tu": "0",
                    "bframes": "16",
                    "ref": "8",
                    "subme": "2",
                    "open-gop": "1",
                    "gop-lookahead": "0",
                    "rc-lookahead": "20",
                    "rect": "0",
                    "amp": "0",
                    "cbqpoffs": "0",
                    "crqpoffs": "0",
                    "ipratio": "1.4",
                    "pbratio": "1.3",
                    "early-skip": "1",
                    "ctu": "64",
                    "min-cu-size": "8",
                    "max-tu-size": "32",
                    "level-idc": "0",
                    "sao": "0",
                    "weightb": "1",
                    "info": "1",
                }
                _custom_option_map = {
                    "crf": self.option_map.get("crf"),
                    "qpmin": self.option_map.get("qpmin"),
                    "qpmax": self.option_map.get("qpmax"),
                    "psy-rd": self.option_map.get("psy-rd"),
                    "rd": self.option_map.get("rd"),
                    "rdoq-level": self.option_map.get("rdoq-level"),
                    "psy-rdoq": self.option_map.get("psy-rdoq"),
                    "qcomp": self.option_map.get("qcomp"),
                    "keyint": self.option_map.get("keyint"),
                    "min-keyint": self.option_map.get("min-keyint"),
                    "deblock": self.option_map.get("deblock"),
                    "me": self.option_map.get("me"),
                    "merange": self.option_map.get("merange"),
                    "hme": self.option_map.get("hme"),
                    "hme-search": self.option_map.get("hme-search"),
                    "hme-range": self.option_map.get("hme-range"),
                    "aq-mode": self.option_map.get("aq-mode"),
                    "aq-strength": self.option_map.get("aq-strength"),
                    "tu-intra-depth": self.option_map.get("tu-intra-depth"),
                    "tu-inter-depth": self.option_map.get("tu-inter-depth"),
                    "limit-tu": self.option_map.get("limit-tu"),
                    "bframes": self.option_map.get("bframes"),
                    "ref": self.option_map.get("ref"),
                    "subme": self.option_map.get("subme"),
                    "open-gop": self.option_map.get("open-gop"),
                    "gop-lookahead": self.option_map.get("gop-lookahead"),
                    "rc-lookahead": self.option_map.get("rc-lookahead"),
                    "rect": self.option_map.get("rect"),
                    "amp": self.option_map.get("amp"),
                    "cbqpoffs": self.option_map.get("cbqpoffs"),
                    "crqpoffs": self.option_map.get("crqpoffs"),
                    "ipratio": self.option_map.get("ipratio"),
                    "pbratio": self.option_map.get("pbratio"),
                    "early-skip": self.option_map.get("early-skip"),
                    "ctu": self.option_map.get("ctu"),
                    "min-cu-size": self.option_map.get("min-cu-size"),
                    "max-tu-size": self.option_map.get("max-tu-size"),
                    "level-idc": self.option_map.get("level-idc"),
                    "sao": self.option_map.get("sao"),
                    **{
                        k: v
                        for k, v in [
                            s.split("=")
                            for s in str(self.option_map.get("x265-params", "")).split(
                                ":"
                            )
                            if s != ""
                        ]
                    },
                }
                _custom_option_map = {
                    k: v for k, v in _custom_option_map.items() if v is not None
                }

                match preset_name:
                    case Ripper.PresetName.x265fast4:
                        _option_map = {
                            "crf": "18",
                            "qpmin": "12",
                            "qpmax": "28",
                            "rd": "2",
                            "rdoq-level": "1",
                            "me": "hex",
                            "merange": "57",
                            "hme-search": "hex,hex,hex",
                            "hme-range": "16,32,48",
                            "aq-mode": "1",
                            "tu-intra-depth": "1",
                            "tu-inter-depth": "1",
                            "limit-tu": "4",
                            "bframes": "8",
                            "ref": "6",
                            "subme": "3",
                            "open-gop": "0",
                            "gop-lookahead": "0",
                            "rc-lookahead": "48",
                            "cbqpoffs": "-1",
                            "crqpoffs": "-1",
                            "pbratio": "1.28",
                        }
                    case Ripper.PresetName.x265fast3:
                        _option_map = {
                            "crf": "18",
                            "qpmin": "12",
                            "qpmax": "28",
                            "rdoq-level": "1",
                            "deblock": "-0.5,-0.5",
                            "me": "hex",
                            "merange": "57",
                            "hme-search": "hex,hex,hex",
                            "hme-range": "16,32,57",
                            "aq-mode": "3",
                            "tu-intra-depth": "2",
                            "tu-inter-depth": "2",
                            "limit-tu": "4",
                            "bframes": "12",
                            "ref": "6",
                            "subme": "3",
                            "open-gop": "0",
                            "gop-lookahead": "0",
                            "rc-lookahead": "120",
                            "cbqpoffs": "-1",
                            "crqpoffs": "-1",
                            "pbratio": "1.27",
                        }
                    case Ripper.PresetName.x265fast2:
                        _option_map = {
                            "crf": "18",
                            "qpmin": "12",
                            "qpmax": "28",
                            "rdoq-level": "2",
                            "deblock": "-1,-1",
                            "me": "hex",
                            "merange": "57",
                            "hme-search": "hex,hex,hex",
                            "hme-range": "16,57,92",
                            "aq-mode": "3",
                            "tu-intra-depth": "3",
                            "tu-inter-depth": "2",
                            "limit-tu": "4",
                            "ref": "6",
                            "subme": "4",
                            "open-gop": "0",
                            "gop-lookahead": "0",
                            "rc-lookahead": "192",
                            "cbqpoffs": "-1",
                            "crqpoffs": "-1",
                            "pbratio": "1.25",
                        }
                    case Ripper.PresetName.x265fast:
                        _option_map = {
                            "crf": "18",
                            "qpmin": "12",
                            "qpmax": "28",
                            "psy-rd": "1.8",
                            "rdoq-level": "2",
                            "psy-rdoq": "0.4",
                            "keyint": "312",
                            "deblock": "-1,-1",
                            "me": "umh",
                            "merange": "57",
                            "hme-search": "umh,hex,hex",
                            "hme-range": "16,57,92",
                            "aq-mode": "4",
                            "tu-intra-depth": "4",
                            "tu-inter-depth": "3",
                            "limit-tu": "4",
                            "subme": "5",
                            "gop-lookahead": "8",
                            "rc-lookahead": "216",
                            "cbqpoffs": "-2",
                            "crqpoffs": "-2",
                            "pbratio": "1.2",
                        }
                    case Ripper.PresetName.x265slow:
                        _option_map = {
                            "crf": "17.5",
                            "qpmin": "12",
                            "qpmax": "28",
                            "rd": "5",
                            "psy-rd": "1.8",
                            "rdoq-level": "2",
                            "psy-rdoq": "0.4",
                            "qcomp": "0.7",
                            "keyint": "312",
                            "deblock": "-1,-1",
                            "me": "umh",
                            "merange": "57",
                            "hme-search": "umh,hex,hex",
                            "hme-range": "16,57,184",
                            "aq-mode": "4",
                            "aq-strength": "1",
                            "tu-intra-depth": "4",
                            "tu-inter-depth": "3",
                            "limit-tu": "2",
                            "subme": "6",
                            "gop-lookahead": "14",
                            "rc-lookahead": "250",
                            "rect": "1",
                            "min-keyint": "2",
                            "cbqpoffs": "-2",
                            "crqpoffs": "-2",
                            "pbratio": "1.2",
                            "early-skip": "0",
                        }
                    case Ripper.PresetName.x265full:
                        _option_map = {
                            "crf": "17",
                            "qpmin": "3",
                            "qpmax": "20",
                            "psy-rd": "2.2",
                            "rd": "5",
                            "rdoq-level": "2",
                            "psy-rdoq": "1.6",
                            "qcomp": "0.72",
                            "keyint": "266",
                            "min-keyint": "2",
                            "deblock": "-1,-1",
                            "me": "umh",
                            "merange": "160",
                            "hme-search": "full,umh,hex",
                            "hme-range": "16,92,320",
                            "aq-mode": "4",
                            "aq-strength": "1.2",
                            "tu-intra-depth": "4",
                            "tu-inter-depth": "4",
                            "limit-tu": "2",
                            "subme": "7",
                            "open-gop": "1",
                            "gop-lookahead": "14",
                            "rc-lookahead": "250",
                            "rect": "1",
                            "amp": "1",
                            "cbqpoffs": "-3",
                            "crqpoffs": "-3",
                            "ipratio": "1.43",
                            "pbratio": "1.2",
                            "early-skip": "0",
                        }

                _option_map = _default_option_map | _option_map | _custom_option_map

                if _option_map.get("hme", "0") == "0":
                    _option_map.pop("hme-search")
                    _option_map.pop("hme-range")

                _param = ":".join(f"{key}={val}" for key, val in _option_map.items())

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f" -c:v libx265 {'' if is_pipe_input else '-pix_fmt yuv420p10le'} -x265-params "
                    + f' "{_param}" {ffparams_out} '
                    + (f' -vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case (
                Ripper.PresetName.h264_amf
                | Ripper.PresetName.h264_nvenc
                | Ripper.PresetName.h264_qsv
                | Ripper.PresetName.hevc_amf
                | Ripper.PresetName.hevc_nvenc
                | Ripper.PresetName.hevc_qsv
                | Ripper.PresetName.av1_amf
                | Ripper.PresetName.av1_nvenc
                | Ripper.PresetName.av1_qsv
            ):
                _option_map = {
                    "q:v": self.option_map.get("q:v"),
                    "pix_fmt": self.option_map.get("pix_fmt"),
                    "preset:v": self.option_map.get("preset:v"),
                }

                _param = " ".join(
                    (f"-{key} {val}" for key, val in _option_map.items() if val)
                )

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f" -c:v {preset_name.value} "
                    + f" {_param} {ffparams_out} "
                    + (f' -vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case Ripper.PresetName.subset:
                encoder_format_str = ""

        return Ripper.Option(
            preset_name, encoder_format_str, audio_encoder, muxer, muxer_format_str
        )

    def _flush_progress(self, sleep_sec: float) -> None:
        while True:
            sleep(sleep_sec)

            if easyrip_web.http_server.Event.is_run_command[-1] is False:
                break

            try:
                with FF_PROGRESS_LOG_FILE.open("rt", encoding="utf-8") as file:
                    file.seek(0, 2)  # 将文件指针移动到文件末尾
                    total_size = file.tell()  # 获取文件的总大小
                    buffer = []
                    while len(buffer) < 12:
                        # 每次向前移动400字节
                        step = min(400, total_size)
                        total_size -= step
                        file.seek(total_size)
                        # 读取当前块的内容
                        lines = file.readlines()
                        # 将读取到的行添加到缓冲区
                        buffer = lines + buffer
                        # 如果已经到达文件开头，退出循环
                        if total_size == 0:
                            break
            except FileNotFoundError:
                continue
            except Exception as e:
                log.error(e)
                continue

            res = {
                line[0]: line[1]
                for line in (line.strip().split("=") for line in buffer[-12:])
            }

            if p := res.get("progress"):
                out_time_us = res.get("out_time_us", "")
                speed = res.get("speed", "").rstrip("x")

                self._progress["frame"] = int(res.get("frame", ""))
                self._progress["fps"] = float(res.get("fps", ""))
                self._progress["out_time_us"] = (
                    int(out_time_us) if out_time_us != "N/A" else 0
                )
                self._progress["speed"] = float(speed) if speed != "N/A" else 0

                easyrip_web.http_server.Event.progress.append(self._progress)
                easyrip_web.http_server.Event.progress.popleft()

                if p != "continue":
                    break

            else:
                continue

        easyrip_web.http_server.Event.progress.append({})
        easyrip_web.http_server.Event.progress.popleft()

    def run(self, prep_func=lambda _: None) -> bool:
        if not self.input_path_list[0].exists():
            log.error('The file "{}" does not exist', self.input_path_list[0])
            return False

        prep_func(self)

        # 生成临时名
        basename = self.output_prefix_list[0]
        temp_name = f"{basename}-{datetime.now().strftime('%Y-%m-%d_%H：%M：%S')}"
        suffix: str

        # 根据格式判断
        match self.option.preset_name:
            case Ripper.PresetName.custom:
                suffix = (
                    f".{_suffix}"
                    if (_suffix := self.option_map.get("custom:suffix"))
                    else ""
                )
                temp_name = temp_name + suffix
                cmd = self.option.encoder_format_str.format_map(
                    {
                        "input": str(self.input_path_list[0]),
                        "output": os.path.join(self.output_dir, temp_name),
                    }
                )

            case Ripper.PresetName.flac:
                if self.option.muxer is not None or len(self.info.audio_info) > 1:
                    suffix = f".flac.{'mp4' if self.option.muxer == Ripper.Muxer.mp4 else 'mkv'}"
                    temp_name = temp_name + suffix
                    cmd = " ".join(
                        (
                            self.option.encoder_format_str,
                            self.option.muxer_format_str,
                        )
                    ).format_map(
                        {
                            "input": str(self.input_path_list[0]),
                            "output": os.path.join(self.output_dir, temp_name),
                        }
                    )
                else:
                    suffix = ".flac"
                    temp_name = temp_name + suffix
                    cmd = self.option.encoder_format_str.format_map(
                        {
                            "input": str(self.input_path_list[0]),
                            "output": os.path.join(self.output_dir, temp_name),
                        }
                    )

            case Ripper.PresetName.subset:
                _output_dir = Path(self.output_dir) / basename
                _output_dir.mkdir(parents=True, exist_ok=True)

                _ass_list = list[Path]()
                _other_sub_list = list[Path]()

                for path in self.input_path_list:
                    if path.suffix == ".ass":
                        _ass_list.append(path)
                    else:
                        _other_sub_list.append(path)

                if _ass_list:
                    _font_path_list = self.option_map.get("subset-font-dir")
                    if _font_path_list is None:
                        _font_path_list = [
                            "",
                            *(
                                d.name
                                for d in Path.cwd().iterdir()
                                if d.is_dir() and "font" in d.name.lower()
                            ),
                        ]
                    else:
                        _font_path_list = _font_path_list.split("?")

                    _font_in_sub = self.option_map.get("subset-font-in-sub", "0") == "1"
                    _use_win_font = (
                        self.option_map.get("subset-use-win-font", "0") == "1"
                    )
                    _use_libass_spec = (
                        self.option_map.get("subset-use-libass-spec", "0") == "1"
                    )
                    _drop_non_render = (
                        self.option_map.get("subset-drop-non-render", "1") == "1"
                    )
                    _drop_unkow_data = (
                        self.option_map.get("subset-drop-unkow-data", "1") == "1"
                    )
                    _strict = self.option_map.get("subset-strict", "0") == "1"

                    subset_res = subset(
                        _ass_list,
                        _font_path_list,
                        _output_dir,
                        # *
                        font_in_sub=_font_in_sub,
                        use_win_font=_use_win_font,
                        use_libass_spec=_use_libass_spec,
                        drop_non_render=_drop_non_render,
                        drop_unkow_data=_drop_unkow_data,
                        strict=_strict,
                    )
                else:
                    subset_res = True

                for path in _other_sub_list:
                    shutil.copy2(path, _output_dir / path.name)

                if subset_res is False:
                    log.error("Run {} failed", "subset")
                return subset_res

            case _:
                match self.option.muxer:
                    case Ripper.Muxer.mp4:
                        if self.option_map.get("auto-infix", "1") == "0":
                            suffix = ".mp4"
                        else:
                            suffix = (
                                ".va.mp4" if self.option.audio_encoder else ".v.mp4"
                            )
                        temp_name = temp_name + suffix
                        cmd = " ".join(
                            (
                                self.option.encoder_format_str,
                                self.option.muxer_format_str,
                            )
                        ).format_map(
                            {
                                "input": str(self.input_path_list[0]),
                                "output": os.path.join(self.output_dir, temp_name),
                            }
                        )

                    case Ripper.Muxer.mkv:
                        if self.option_map.get("auto-infix", "1") == "0":
                            suffix = ".mkv"
                        else:
                            suffix = (
                                ".va.mkv" if self.option.audio_encoder else ".v.mkv"
                            )
                        temp_name = temp_name + suffix
                        cmd = " ".join(
                            (
                                self.option.encoder_format_str,
                                self.option.muxer_format_str,
                            )
                        ).format_map(
                            {
                                "input": str(self.input_path_list[0]),
                                "output": os.path.join(self.output_dir, temp_name),
                            }
                        )

                    case _:
                        if self.option_map.get("auto-infix", "1") == "0":
                            suffix = ".mkv"
                        else:
                            suffix = (
                                ".va.mkv" if self.option.audio_encoder else ".v.mkv"
                            )
                        temp_name = temp_name + suffix
                        cmd = self.option.encoder_format_str.format_map(
                            {
                                "input": str(self.input_path_list[0]),
                                "output": os.path.join(
                                    self.output_dir,
                                    os.path.join(self.output_dir, temp_name),
                                ),
                            }
                        )

        # 执行
        output_filename = basename + suffix
        run_start_time = datetime.now()
        run_sign = (
            f" Sub Ripper {sub_ripper_num}"
            if (sub_ripper_num := self.option_map.get("_sub_ripper_num"))
            else " Ripper"
        ) + (
            f": {sub_ripper_title}"
            if (sub_ripper_title := self.option_map.get("_sub_ripper_title"))
            else ""
        )
        log.write_html_log(
            '<hr style="color:aqua;margin:4px 0 0;">'
            '<div style="background-color:#b4b4b4;padding:0 1rem;">'
            f'<span style="color:green;">{run_start_time.strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]}</span> <span style="color:aqua;">{gettext("Start")}{run_sign}</span><br>'
            f'{gettext("Input file pathname")}: <span style="color:darkcyan;">"{self.input_path_list[0]}"</span><br>'
            f'{gettext("Output directory")}: <span style="color:darkcyan;">"{self.output_dir}"</span><br>'
            f'{gettext("Temporary file name")}: <span style="color:darkcyan;">"{temp_name}"</span><br>'
            f'{gettext("Output file name")}: <span style="color:darkcyan;">"{output_filename}"</span><br>'
            "Ripper:<br>"
            f'<span style="white-space:pre-wrap;color:darkcyan;">{self}</span>'
            # "</div>"
        )

        # 先删除，防止直接读到结束标志
        FF_PROGRESS_LOG_FILE.unlink(missing_ok=True)

        self._progress["frame_count"] = 0
        self._progress["duration"] = 0
        if not self.input_path_list[0].suffix == ".vpy":
            self._progress["frame_count"] = self.info.nb_frames
            self._progress["duration"] = self.info.duration

        Thread(target=self._flush_progress, args=(1,), daemon=True).start()

        if self.preset_name is not Ripper.PresetName.custom:
            os.environ["FFREPORT"] = f"file={FF_REPORT_LOG_FILE}:level=31"

        log.info(cmd)
        is_cmd_run_failed = os.system(cmd)

        # 读取编码速度
        speed: str = "N/A"
        if FF_PROGRESS_LOG_FILE.is_file():
            with FF_PROGRESS_LOG_FILE.open("rt", encoding="utf-8") as file:
                for line in file.readlines()[::-1]:
                    if res := re.search(r"speed=(.*)", line):
                        speed = res.group(1)
                        break

        log.write_html_log(
            f'{gettext("Encoding speed")}: <span style="color:darkcyan;">{speed}</span><br>'
        )

        if is_cmd_run_failed:
            log.error("There have error in running")
        else:  # 多文件合成
            # flac 音频轨合成
            if (
                self.preset_name != Ripper.PresetName.flac
                and self.option.audio_encoder == Ripper.AudioCodec.flac
            ):
                _flac_basename = f"flac_temp_{get_base62_time()}"
                _flac_fullname = _flac_basename + ".flac.mkv"
                _flac_ripper = Ripper(
                    [self.input_path_list[0]],
                    [_flac_basename],
                    self.output_dir,
                    Ripper.PresetName.flac,
                    (
                        self.option_map
                        | {
                            "_sub_ripper_num": str(
                                int(self.option_map.get("_sub_ripper_num", 0)) + 1
                            ),
                            "_sub_ripper_title": "FLAC Enc",
                            "muxer": "mkv",
                        }
                    ),
                )
                _flac_ripper.run()

                _mux_temp_name: str
                _mux_cmd: str
                _mux_muxer: str = (
                    "mp4" if self.option.muxer == Ripper.Muxer.mp4 else "mkv"
                )
                _mux_temp_name = f"{temp_name}_{get_base62_time()}.{_mux_muxer}"

                _mux_cmd = f'mkvmerge -o "{_mux_temp_name}" --no-audio "{temp_name}" --no-video "{_flac_fullname}"'

                log.info(_mux_cmd)
                if os.system(_mux_cmd):
                    log.error("There have error in running")
                else:
                    os.remove(temp_name)
                    mux_ripper = Ripper(
                        (_mux_temp_name,),
                        (Path(temp_name).stem,),
                        self.output_dir,
                        Ripper.PresetName.copy,
                        {
                            k: v
                            for k, v in {
                                "_sub_ripper_num": str(
                                    int(self.option_map.get("_sub_ripper_num", 0)) + 1
                                ),
                                "_sub_ripper_title": "FLAC Mux",
                                "auto-infix": "0",
                                "c:a": "copy",
                                "muxer": _mux_muxer,
                                "r": self.option_map.get("r"),
                                "fps": self.option_map.get("fps"),
                            }.items()
                            if v
                        },
                    )
                    mux_ripper.run()
                os.remove(_mux_temp_name)

                if os.path.exists(_flac_fullname):
                    os.remove(_flac_fullname)

            # 内封字幕合成
            if soft_sub := self.option_map.get("soft-sub"):
                # 处理 soft-sub
                soft_sub_list: list[str]
                soft_sub_map_list: list[str] = soft_sub.split(":")
                if soft_sub_map_list[0] == "auto":
                    soft_sub_list = []

                    _input_basename = os.path.splitext(
                        os.path.basename(self.input_path_list[0])
                    )
                    while _input_basename[1] != "":
                        _input_basename = os.path.splitext(_input_basename[0])
                    _input_prefix: str = _input_basename[0]

                    for _file_basename in os.listdir(self.output_dir):
                        _file_basename_list = os.path.splitext(_file_basename)
                        if (
                            _file_basename_list[1]
                            in {
                                ".srt",
                                ".ass",
                                ".ssa",
                                ".sup",
                                ".idx",
                            }
                            and _file_basename_list[0].startswith(_input_prefix)
                            and (
                                len(soft_sub_map_list) == 1
                                or os.path.splitext(_file_basename_list[0])[1].lstrip(
                                    "."
                                )
                                in soft_sub_map_list[1:]
                            )
                        ):
                            soft_sub_list.append(
                                os.path.join(self.output_dir, _file_basename)
                            )
                else:
                    soft_sub_list = soft_sub.split("?")

                # 子集化
                subset_folder = Path(self.output_dir) / f"subset_temp_{temp_name}"
                log.info("-soft-sub list = {}", soft_sub_list)
                if Ripper(
                    soft_sub_list,
                    (subset_folder.name,),
                    self.output_dir,
                    Ripper.PresetName.subset,
                    self.option_map,
                ).run():
                    # 合成 MKV
                    org_full_name: str = os.path.join(self.output_dir, temp_name)
                    new_full_name: str = os.path.join(
                        self.output_dir, f"wait_subset_{temp_name}"
                    )
                    os.rename(org_full_name, new_full_name)

                    if Ripper(
                        [new_full_name],
                        [os.path.splitext(org_full_name)[0]],
                        self.output_dir,
                        Ripper.PresetName.copy,
                        {
                            k: v
                            for k, v in {
                                "only-mux-sub-path": str(subset_folder),
                                "_sub_ripper_num": str(
                                    int(self.option_map.get("_sub_ripper_num", 0)) + 1
                                ),
                                "_sub_ripper_title": "Soft Sub Mux",
                                "auto-infix": "0",
                                "c:a": self.option_map.get("c:a") and "copy",
                                "muxer": "mkv",
                                "r": self.option_map.get("r"),
                                "fps": self.option_map.get("fps"),
                            }.items()
                            if v
                        },
                    ).run():
                        if os.path.exists(new_full_name):
                            os.remove(new_full_name)
                else:
                    log.error("Subset faild, cancel mux")

                shutil.rmtree(subset_folder)

        # 获取 ffmpeg report 中的报错
        if FF_REPORT_LOG_FILE.is_file():
            with FF_REPORT_LOG_FILE.open("rt", encoding="utf-8") as file:
                for line in file.readlines()[2:]:
                    log.warning("FFmpeg report: {}", line)

        # 获取体积
        temp_name_full = os.path.join(self.output_dir, temp_name)
        file_size = round(os.path.getsize(temp_name_full) / (1024 * 1024), 2)  # MiB .2f

        # 将临时名重命名
        try:
            os.rename(temp_name_full, os.path.join(self.output_dir, output_filename))
        except FileExistsError as e:
            log.error(e)
        except Exception as e:
            log.error(e)

        # 写入日志
        run_end_time = datetime.now()
        log.write_html_log(
            f'{gettext("File size")}: <span style="color:darkcyan;">{file_size} MiB</span><br>'
            f'{gettext("Time consuming")}: <span style="color:darkcyan;">{str(run_end_time - run_start_time)[:-4]}</span><br>'
            f'<span style="color:green;">{run_end_time.strftime("%Y.%m.%d %H:%M:%S.%f")[:-4]}</span> <span style="color:brown;">{gettext("End")}{run_sign}</span><br>'
            "</div>"
            '<hr style="color:brown;margin:0 0 6px;">'
        )

        # 删除临时文件
        FF_PROGRESS_LOG_FILE.unlink(missing_ok=True)
        FF_REPORT_LOG_FILE.unlink(missing_ok=True)

        # 删除临时环境变量
        os.environ.pop("FFREPORT", None)

        return True

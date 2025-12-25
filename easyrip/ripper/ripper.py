import os
import re
import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Final, Self, final

from .. import easyrip_web
from ..easyrip_log import log
from ..easyrip_mlang import Global_lang_val, gettext, translate_subtitles
from ..utils import get_base62_time
from .media_info import Media_info, Stream_error
from .param import (
    DEFAULT_PRESET_PARAMS,
    FONT_SUFFIX_SET,
    SUBTITLE_SUFFIX_SET,
    X264_PARAMS_NAME,
    X265_PARAMS_NAME,
)
from .sub_and_font import subset

FF_PROGRESS_LOG_FILE = Path("FFProgress.log")
FF_REPORT_LOG_FILE = Path("FFReport.log")


@final
class Ripper:
    ripper_list: Final[list["Ripper"]] = []

    @classmethod
    def add_ripper(
        cls: type["Ripper"],
        input_path: Iterable[str | Path],
        output_prefix: Iterable[str | None],
        output_dir: str | None,
        option: "Option | Preset_name",
        option_map: dict[str, str],
    ):
        try:
            cls.ripper_list.append(
                cls(input_path, output_prefix, output_dir, option, option_map)
            )
        except Exception as e:
            log.error("Failed to add Ripper: {}", e, deep=True)

    from .param import Audio_codec, Muxer, Preset_name

    @dataclass(slots=True)
    class Option:
        preset_name: "Ripper.Preset_name"
        encoder_format_str: str
        audio_encoder: "Ripper.Audio_codec | None"
        muxer: "Ripper.Muxer | None"
        muxer_format_str: str

        def __str__(self) -> str:
            return f"  preset_name = {self.preset_name}\n  option_format = {self.encoder_format_str}"

    input_path_list: list[Path]
    output_prefix_list: list[str]
    output_dir: str
    option: Option
    option_map: dict[str, str]

    preset_name: Preset_name

    media_info: Media_info

    _progress: dict[str, int | float]
    """
    server 模式的进度条数据

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
        option: Option | Preset_name,
        option_map: dict[str, str],
    ) -> None:
        self.input_path_list = [Path(path) for path in input_path]

        self.media_info = Media_info.from_path(self.input_path_list[0])

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

        if isinstance(option, Ripper.Preset_name):
            self.preset_name = option
            self.option = self.preset_name_to_option(option)
        else:
            self.preset_name = Ripper.Preset_name.custom
            self.option = option

        self._progress: dict[str, int | float] = {}

    def __str__(self) -> str:
        return (
            f"-i {self.input_path_list[0]} -o {self.output_prefix_list[0]} -o:dir {self.output_dir} -preset {self.option.preset_name.value} {' '.join((f'-{key} {val}' for key, val in self.option_map.items()))}\n"
            "  option:  {\n"
            f"  {str(self.option).replace('\n', '\n  ')}\n"
            "  }\n"
            f"  option_map: {self.option_map}"
        )

    def preset_name_to_option(self, preset_name: Preset_name) -> Option:
        if (
            force_fps := self.option_map.get("r") or self.option_map.get("fps")
        ) == "auto":
            try:
                force_fps = (
                    self.media_info.r_frame_rate[0] / self.media_info.r_frame_rate[1]
                )
                if 23.975 < force_fps < 23.977:
                    force_fps = "24000/1001"
                elif 29.969 < force_fps < 29.971:
                    force_fps = "30000/1001"
                elif 47.951 < force_fps < 47.953:
                    force_fps = "48000/1001"
                elif 59.939 < force_fps < 59.941:
                    force_fps = "60000/1001"
            except Exception as e:
                log.error(f"{e!r} {e}", deep=True)

        # Path
        vpy_pathname = self.option_map.get("pipe")

        if vpy_pathname and not os.path.exists(vpy_pathname):
            log.error('The file "{}" does not exist', vpy_pathname)

        is_pipe_input = bool(self.input_path_list[0].suffix == ".vpy" or vpy_pathname)

        ff_input_option: list[str]
        ff_input_option = ["-"] if is_pipe_input else ['"{input}"']
        ff_stream_option: list[str] = ["0:v"]
        ff_vf_option: list[str] = (
            s.split(",") if (s := self.option_map.get("vf")) else []
        )

        if sub_pathname := self.option_map.get("sub"):
            sub_pathname = f"'{sub_pathname.replace('\\', '/').replace(':', '\\:')}'"
            ff_vf_option.append(f"ass={sub_pathname}")

        # Audio
        if audio_encoder_str := self.option_map.get("c:a"):
            if (
                not self.media_info.audio_info
                and self.preset_name != Ripper.Preset_name.subset
            ):
                raise Stream_error(
                    "There is no audio stream in the video, so '-c:a' cannot be used"
                )

            if audio_encoder_str not in Ripper.Audio_codec._member_map_:
                raise ValueError(
                    gettext("Unsupported '{}' param: {}", "-c:a", audio_encoder_str)
                )

            audio_encoder = Ripper.Audio_codec[audio_encoder_str]

            # 通知别名映射
            if audio_encoder_str not in Ripper.Audio_codec._member_names_:
                log.info(
                    "Auto mapping encoder name: {} -> {}",
                    audio_encoder_str,
                    audio_encoder.name,
                )

            if is_pipe_input:
                ff_input_option.append('"{input}"')
                ff_stream_option.append("1:a")
            else:
                ff_stream_option.append("0:a")

            match audio_encoder:
                case Ripper.Audio_codec.copy:
                    _encoder_str = (
                        ""
                        if self.preset_name == Ripper.Preset_name.copy
                        else "-c:a copy "
                    )
                case Ripper.Audio_codec.flac:
                    _encoder_str = "-an "
                case Ripper.Audio_codec.libopus:
                    _encoder_str = "-c:a libopus "
                    for opt in (
                        "application",
                        "frame_duration",
                        "packet_loss",
                        "fec",
                        "vbr",
                        "mapping_family",
                        "apply_phase_inv",
                    ):
                        if (val := self.option_map.get(opt)) is not None:
                            _encoder_str += f"-{opt} {val} "

            _bitrate_str = (
                ""
                if audio_encoder in {Ripper.Audio_codec.copy, Ripper.Audio_codec.flac}
                else f"-b:a {self.option_map.get('b:a') or '160k'} "
            )

            audio_option = _encoder_str + _bitrate_str

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
                            if self.preset_name == Ripper.Preset_name.flac
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
                                    if _file.suffix in FONT_SUFFIX_SET
                                    else f"--language 0:{affixes[1]} --track-name 0:{Global_lang_val.language_tag_to_local_str(affixes[1])} "
                                )
                                + f'"{_file.absolute()}"'
                                for _file in only_mux_sub_path.iterdir()
                                if _file.suffix
                                in (SUBTITLE_SUFFIX_SET | FONT_SUFFIX_SET)
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
        pipe_gvar_dict = dict(
            s.split("=", maxsplit=1) for s in pipe_gvar_list if "=" in s
        )
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
        ffparams_in = self.option_map.get("ff-params:in", "") + " "
        ffparams_out = self.option_map.get("ff-params:out", "") + " "
        if _ss := self.option_map.get("ss"):
            ffparams_in += f"-ss {_ss} "
        if _t := self.option_map.get("t"):
            ffparams_out += f"-t {_t} "
        if _preset := self.option_map.get("v:preset"):
            ffparams_out += f"-preset {_preset} "

        FFMPEG_HEADER = f"ffmpeg {'-hide_banner ' if self.option_map.get('_sub_ripper_num') else ''}-progress {FF_PROGRESS_LOG_FILE} -report {ffparams_ff} {ffparams_in}"

        match preset_name:
            case Ripper.Preset_name.custom:
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

            case Ripper.Preset_name.copy:
                hwaccel = (
                    f"-hwaccel {hwaccel}"
                    if (hwaccel := self.option_map.get("hwaccel"))
                    else ""
                )

                encoder_format_str = (
                    f"{FFMPEG_HEADER} {hwaccel} "
                    '-i "{input}" -c copy '
                    f"{' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + ffparams_out
                    + '"{output}"'
                )

                match self.option_map.get("c:a"):
                    case None | "flac":
                        if muxer == Ripper.Muxer.mp4:
                            encoder_format_str = 'mp4box -add "{input}" -new "{output}"'
                            for _audio_info in self.media_info.audio_info:
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

            case Ripper.Preset_name.flac:
                _ff_encode_str: str = ""
                _flac_encode_str: str = ""
                _mux_flac_input_list: list[str] = []
                # _mux_flac_map_str: str = ""
                _del_flac_str: str = ""

                for _audio_info in self.media_info.audio_info:
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
                        raise RuntimeError(f'No audio in "{self.input_path_list[0]}"')

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
                            ' -new "{output}" '
                            if muxer == Ripper.Muxer.mp4
                            else 'mkvmerge -o "{output}" '
                            + " ".join(_mux_flac_input_list)
                        )
                        encoder_format_str = (
                            FFMPEG_HEADER + ' -i "{input}" '
                            f"{_ff_encode_str} {_flac_encode_str} "
                            f"&& {_mux_str} " + _del_flac_str
                        )

            case (
                Ripper.Preset_name.x264
                | Ripper.Preset_name.x264fast
                | Ripper.Preset_name.x264slow
            ):
                _custom_option_map: dict[str, str] = {
                    k: v
                    for k, v in {
                        **{
                            _param_name: self.option_map.get(_param_name)
                            for _param_name in X264_PARAMS_NAME
                        },
                        **dict(
                            s.split("=", maxsplit=1)
                            for s in str(self.option_map.get("x264-params", "")).split(
                                ":"
                            )
                            if s
                        ),
                    }.items()
                    if v is not None
                }

                _option_map = (
                    DEFAULT_PRESET_PARAMS.get(preset_name, {}) | _custom_option_map
                )

                if (
                    (_crf := _option_map.get("crf"))
                    and (_qpmin := _option_map.get("qpmin"))
                    and (_qpmax := _option_map.get("qpmax"))
                    and not (float(_qpmin) <= float(_crf) <= float(_qpmax))
                ):
                    log.warning("The CRF is not between QPmin and QPmax")

                _param = ":".join(f"{key}={val}" for key, val in _option_map.items())

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f"-c:v libx264 {'' if is_pipe_input else '-pix_fmt yuv420p'} -x264-params "
                    + f'"{_param}" {ffparams_out} '
                    + (f'-vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + '"{output}"'
                )

            case (
                Ripper.Preset_name.x265
                | Ripper.Preset_name.x265fast4
                | Ripper.Preset_name.x265fast3
                | Ripper.Preset_name.x265fast2
                | Ripper.Preset_name.x265fast
                | Ripper.Preset_name.x265slow
                | Ripper.Preset_name.x265full
            ):
                _custom_option_map: dict[str, str] = {
                    k: v
                    for k, v in {
                        **{
                            _param_name: self.option_map.get(_param_name)
                            for _param_name in X265_PARAMS_NAME
                        },
                        **dict(
                            s.split("=", maxsplit=1)
                            for s in str(self.option_map.get("x265-params", "")).split(
                                ":"
                            )
                            if s
                        ),
                    }.items()
                    if v is not None
                }

                _option_map = (
                    DEFAULT_PRESET_PARAMS.get(preset_name, {}) | _custom_option_map
                )

                # HEVC 规范
                if self.option_map.get(
                    "hevc-strict", "1"
                ) != "0" and self.media_info.width * self.media_info.height >= (
                    _RESOLUTION := 1920 * 1080 * 4
                ):
                    if _option_map.get("hme", "0") == "1":
                        _option_map["hme"] = "0"
                        log.warning(
                            "The resolution {} * {} >= {}, auto close HME",
                            self.media_info.width,
                            self.media_info.height,
                            _RESOLUTION,
                        )

                    if int(_option_map.get("ref") or "3") > (_NEW_REF := 6):
                        _option_map["ref"] = str(_NEW_REF)
                        log.warning(
                            "The resolution {} * {} >= {}, auto reduce {} to {}",
                            self.media_info.width,
                            self.media_info.height,
                            _RESOLUTION,
                            _option_map.get("ref"),
                            _NEW_REF,
                        )

                # 低版本 x265 不支持 -hme 0 主动关闭 HME
                if _option_map.get("hme", "0") == "0":
                    _option_map.pop("hme-search")
                    _option_map.pop("hme-range")

                if (
                    (_crf := _option_map.get("crf"))
                    and (_qpmin := _option_map.get("qpmin"))
                    and (_qpmax := _option_map.get("qpmax"))
                    and not (float(_qpmin) <= float(_crf) <= float(_qpmax))
                ):
                    log.warning("The CRF is not between QPmin and QPmax")

                _param = ":".join(f"{key}={val}" for key, val in _option_map.items())

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f"-c:v libx265 {'' if is_pipe_input else '-pix_fmt yuv420p10le'} -x265-params "
                    + f'"{_param}" {ffparams_out} '
                    + (f'-vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + '"{output}"'
                )

            case (
                Ripper.Preset_name.h264_amf
                | Ripper.Preset_name.h264_nvenc
                | Ripper.Preset_name.h264_qsv
                | Ripper.Preset_name.hevc_amf
                | Ripper.Preset_name.hevc_nvenc
                | Ripper.Preset_name.hevc_qsv
                | Ripper.Preset_name.av1_amf
                | Ripper.Preset_name.av1_nvenc
                | Ripper.Preset_name.av1_qsv
            ):
                _option_map = {
                    "q:v": self.option_map.get("q:v"),
                    "pix_fmt": self.option_map.get("pix_fmt"),
                    "preset:v": self.option_map.get("preset:v"),
                }
                match preset_name:
                    case (
                        Ripper.Preset_name.h264_qsv
                        | Ripper.Preset_name.hevc_qsv
                        | Ripper.Preset_name.av1_qsv
                    ):
                        _option_map["qsv_params"] = self.option_map.get("qsv_params")

                _param = " ".join(
                    (f"-{key} {val}" for key, val in _option_map.items() if val)
                )

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f"-c:v {preset_name.value} "
                    + f"{_param} {ffparams_out} "
                    + (f' -vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case Ripper.Preset_name.svtav1:
                _option_map = {
                    "crf": self.option_map.get("crf"),
                    "qp": self.option_map.get("qp"),
                    "pix_fmt": self.option_map.get(
                        "pix_fmt", None if is_pipe_input else "yuv420p10le"
                    ),
                    "preset:v": self.option_map.get("preset:v"),
                    "svtav1-params": self.option_map.get("svtav1-params"),
                }

                _param = " ".join(
                    (f"-{key} {val}" for key, val in _option_map.items() if val)
                )

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + "-c:v libsvtav1 "
                    + f"{_param} {ffparams_out} "
                    + (f'-vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case Ripper.Preset_name.vvenc:
                _option_map = {
                    "qp": self.option_map.get("qp"),
                    "pix_fmt": self.option_map.get(
                        "pix_fmt", None if is_pipe_input else "yuv420p10le"
                    ),
                    "preset:v": self.option_map.get("preset:v"),
                    "vvenc-params": self.option_map.get("vvenc-params"),
                }

                _param = " ".join(
                    (f"-{key} {val}" for key, val in _option_map.items() if val)
                )

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + "-c:v libvvenc "
                    + f"{_param} {ffparams_out} "
                    + (f'-vf "{",".join(ff_vf_option)}" ' if len(ff_vf_option) else "")
                    + ' "{output}"'
                )

            case Ripper.Preset_name.subset:
                encoder_format_str = ""

        return Ripper.Option(
            preset_name, encoder_format_str, audio_encoder, muxer, muxer_format_str
        )

    def _flush_progress(self, sleep_sec: float) -> None:
        while True:
            sleep(sleep_sec)

            if easyrip_web.http_server.Event.is_run_command is False:
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

            res = dict(line.strip().split("=", maxsplit=1) for line in buffer[-12:])

            if p := res.get("progress"):
                out_time_us = res.get("out_time_us", -1)
                speed = res.get("speed", "-1").rstrip("x")

                self._progress["frame"] = int(res.get("frame", -1))
                self._progress["fps"] = float(res.get("fps", -1))
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

    def run(
        self,
        prep_func: Callable[[Self], None] = lambda _: None,
    ) -> bool:
        if not self.input_path_list[0].exists():
            log.error('The file "{}" does not exist', self.input_path_list[0])
            return False

        prep_func(self)

        # 生成临时名
        basename = self.output_prefix_list[0]
        temp_name = (
            f"{basename}-{datetime.now().strftime('%Y-%m-%d_%H：%M：%S.%f')[:-4]}"
        )
        suffix: str

        # 根据格式判断
        match self.option.preset_name:
            case Ripper.Preset_name.custom:
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

            case Ripper.Preset_name.flac:
                if self.option.muxer is not None or len(self.media_info.audio_info) > 1:
                    suffix = f".flac.{'mp4' if self.option.muxer == Ripper.Muxer.mp4 else 'mkv'}"
                    temp_name = temp_name + suffix
                    cmd = f"{self.option.encoder_format_str} {self.option.muxer_format_str}".format_map(
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

            case Ripper.Preset_name.subset:
                _output_dir = Path(self.output_dir) / basename
                _output_dir.mkdir(parents=True, exist_ok=True)

                _ass_list: list[Path] = []
                _other_sub_list: list[Path] = []

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
                        cmd = f"{self.option.encoder_format_str} {self.option.muxer_format_str}".format_map(
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
                        cmd = f"{self.option.encoder_format_str} {self.option.muxer_format_str}".format_map(
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
        if self.input_path_list[0].suffix != ".vpy":
            self._progress["frame_count"] = self.media_info.nb_frames
            self._progress["duration"] = self.media_info.duration

        Thread(target=self._flush_progress, args=(1,), daemon=True).start()

        if self.preset_name is not Ripper.Preset_name.custom:
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
                self.preset_name != Ripper.Preset_name.flac
                and self.option.audio_encoder == Ripper.Audio_codec.flac
            ):
                _flac_basename = f"flac_temp_{get_base62_time()}"
                _flac_fullname = _flac_basename + ".flac.mkv"
                _flac_ripper = Ripper(
                    [self.input_path_list[0]],
                    [_flac_basename],
                    self.output_dir,
                    Ripper.Preset_name.flac,
                    {
                        k: v
                        for k, v in (
                            self.option_map
                            | {
                                "_sub_ripper_num": str(
                                    int(self.option_map.get("_sub_ripper_num", 0)) + 1
                                ),
                                "_sub_ripper_title": "FLAC Enc",
                                "muxer": "mkv",
                            }
                        ).items()
                        if k not in {"soft-sub", "sub", "translate-sub"}
                    },
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
                        Ripper.Preset_name.copy,
                        {
                            k: v
                            for k, v in dict[str, str | None](
                                {
                                    "_sub_ripper_num": str(
                                        int(self.option_map.get("_sub_ripper_num", 0))
                                        + 1
                                    ),
                                    "_sub_ripper_title": "FLAC Mux",
                                    "auto-infix": "0",
                                    "c:a": "copy",
                                    "muxer": _mux_muxer,
                                    "r": self.option_map.get("r"),
                                    "fps": self.option_map.get("fps"),
                                }
                            ).items()
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
                soft_sub_list: list[Path]
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
                            _file_basename_list[1] in SUBTITLE_SUFFIX_SET
                            and _file_basename_list[0].startswith(_input_prefix)
                            and (
                                len(soft_sub_map_list) == 1
                                or os.path.splitext(_file_basename_list[0])[1].lstrip(
                                    "."
                                )
                                in soft_sub_map_list[1:]
                            )
                        ):
                            soft_sub_list.append(Path(self.output_dir) / _file_basename)

                else:
                    soft_sub_list = [Path(s) for s in soft_sub.split("?")]

                subset_folder = Path(self.output_dir) / f"subset_temp_{temp_name}"
                if not soft_sub_list:
                    log.warning("-soft-sub is empty")
                log.info("-soft-sub list = {}", soft_sub_list)

                # 临时翻译
                add_tr_files: Final[list[Path]] = []
                if translate_sub := self.option_map.get("translate-sub"):
                    _tr = translate_sub.split(":")
                    if len(_tr) != 2:
                        log.error("{} param illegal", "-translate-sub")
                    else:
                        try:
                            _file_list = translate_subtitles(
                                Path(self.output_dir),
                                _tr[0],
                                _tr[1],
                                file_intersection_selector=soft_sub_list,
                            )
                        except Exception as e:
                            log.error(e, is_format=False)
                        else:
                            for f_and_s in _file_list:
                                if f_and_s[0].is_file():
                                    log.warning(
                                        'The file "{}" already exists, skip translating it',
                                        f_and_s[0],
                                    )
                                    continue
                                with f_and_s[0].open(
                                    "wt", encoding="utf-8-sig", newline="\n"
                                ) as f:
                                    f.write(f_and_s[1])
                                    add_tr_files.append(f_and_s[0])

                # 子集化
                if Ripper(
                    soft_sub_list + add_tr_files,
                    (subset_folder.name,),
                    self.output_dir,
                    Ripper.Preset_name.subset,
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
                        Ripper.Preset_name.copy,
                        {
                            k: v
                            for k, v in dict[str, str | None](
                                {
                                    "only-mux-sub-path": str(subset_folder),
                                    "_sub_ripper_num": str(
                                        int(self.option_map.get("_sub_ripper_num", 0))
                                        + 1
                                    ),
                                    "_sub_ripper_title": "Soft Sub Mux",
                                    "auto-infix": "0",
                                    "c:a": self.option_map.get("c:a") and "copy",
                                    "muxer": "mkv",
                                    "r": self.option_map.get("r"),
                                    "fps": self.option_map.get("fps"),
                                }
                            ).items()
                            if v
                        },
                    ).run() and os.path.exists(new_full_name):
                        os.remove(new_full_name)
                else:
                    log.error("Subset faild, cancel mux")

                # 清理临时文件
                shutil.rmtree(subset_folder)
                for f in add_tr_files:
                    try:
                        f.unlink()
                    except Exception as e:
                        log.error(f"{e!r} {e}", deep=True, is_format=False)

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

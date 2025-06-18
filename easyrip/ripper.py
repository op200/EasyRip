import os
import subprocess
import re
from datetime import datetime
import enum
from time import sleep
import json
from threading import Thread

from . import easyrip_web
from .easyrip_log import log
from .easyrip_mlang import gettext

__all__ = ['Ripper']


FF_PROGRESS_LOG_FILE = "FFProgress.log"
FF_REPORT_LOG_FILE = "FFReport.log"


class Ripper:

    ripper_list: list['Ripper'] = []

    class PresetName(enum.Enum):
        custom = 'custom'
        copy = 'copy'
        flac = 'flac'

        x264fast = 'x264fast'
        x264slow = 'x264slow'

        x265fast4 = 'x265fast4'
        x265fast3 = 'x265fast3'
        x265fast2 = 'x265fast2'
        x265fast = 'x265fast'
        x265slow = 'x265slow'
        x265full = 'x265full'

        h264_amf = 'h264_amf'
        h264_nvenc = 'h264_nvenc'
        h264_qsv = 'h264_qsv'

        hevc_amf = 'hevc_amf'
        hevc_nvenc = 'hevc_nvenc'
        hevc_qsv = 'hevc_qsv'

        @classmethod
        def _missing_(cls, value: object):
            default = cls.custom
            log.error("'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                      value, cls.__name__, default, list(cls.__members__.keys()))
            return default

    class AudioCodec(enum.Enum):
        copy = 'copy'
        libopus = 'libopus'

        @classmethod
        def _missing_(cls, value: object):
            default = cls.copy
            log.error("'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                      value, cls.__name__, default, list(cls.__members__.keys()))
            return default

    class Muxer(enum.Enum):
        mp4 = 'mp4'
        mkv = 'mkv'

        @classmethod
        def _missing_(cls, value: object):
            default = cls.mkv
            log.error("'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
                      value, cls.__name__, default, list(cls.__members__.keys()))
            return default

    class Option:

        preset_name: 'Ripper.PresetName'
        encoder_format_str: str
        audio_encoder: 'Ripper.AudioCodec | None'
        muxer: 'Ripper.Muxer | None'
        muxer_format_str: str

        def __init__(
            self,
            preset_name: "Ripper.PresetName",
            format_str: str,
            audio_encoder: "Ripper.AudioCodec | None",
            muxer: "Ripper.Muxer | None",
            muxer_format_str: str,
        ):
            self.preset_name = preset_name
            self.encoder_format_str = format_str
            self.audio_encoder = audio_encoder
            self.muxer = muxer
            self.muxer_format_str = muxer_format_str

        def __str__(self):
            return f'  preset_name = {self.preset_name}\n  option_format = {self.encoder_format_str}'


    class Info:
        '''
        nb_frames 封装帧数(f)

        r_frame_rate 基本帧率(fps分数)

        duration 时长(s)

        sample_fmt
        '''
        nb_frames: int
        r_frame_rate: tuple[int, int]
        duration: float
        sample_fmt: str
        sample_rate: int
        bits_per_sample: int
        bits_per_raw_sample: int

        def __init__(self):
            self.nb_frames = 0
            self.r_frame_rate = (0,1)
            self.duration = 0
            self.sample_fmt = ""
            self.sample_rate = 0
            self.bits_per_sample = 0
            self.bits_per_raw_sample = 0


    input_pathname: str
    output_prefix: str
    output_dir: str
    option: Option
    option_map: dict[str, str]

    preset_name: PresetName

    info: Info

    _progress: dict
    '''
    .frame_count : int 总帧数
    .frame : int 已输出帧数
    .fps : float 当前输出帧率

    .duration : float 视频总时长 s
    .out_time_us : int 已输出时长 us

    .speed : float 当前输出速率 倍
    '''


    def preset_name_to_option(self, preset_name: PresetName) -> Option:

        if (force_fps := self.option_map.get('r') or self.option_map.get('fps')) == "auto":
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
        input_suffix = os.path.splitext(self.input_pathname)[1]
        vpy_pathname = self.option_map.get('pipe')

        if vpy_pathname and not os.path.exists(vpy_pathname):
            log.error('The file "{}" does not exist', vpy_pathname)

        is_pipe_input = bool(input_suffix == ".vpy" or vpy_pathname)

        ff_input_option: list[str]
        if is_pipe_input:
            ff_input_option = ["-"]
        else:
            ff_input_option = ['"{input}"']
        ff_stream_option: list[str] = ["0:v"]
        ff_vf_option: list[str] = s.split(',') if (s := self.option_map.get('vf')) else []

        if sub_pathname := self.option_map.get('sub'):
            sub_pathname = f"'{sub_pathname.replace('\\', '/').replace(':', '\\:')}'"
            ff_vf_option.append(f"ass={sub_pathname}")


        # Audio
        if audio_encoder := self.option_map.get('c:a'):
            _audio_encoder_str = audio_encoder
            audio_encoder = Ripper.AudioCodec(audio_encoder)
            if is_pipe_input:
                ff_input_option.append('"{input}"')
                ff_stream_option.append("1:a")
                audio_option = f'-c:a {_audio_encoder_str} -b:a {self.option_map.get('b:a') or '160k'} '
            else:
                ff_stream_option.append("0:a")
                audio_option = f'-c:a {_audio_encoder_str} -b:a {self.option_map.get('b:a') or '160k'} '
        else:
            audio_encoder = None
            audio_option = ''

        # Muxer
        if muxer := self.option_map.get('muxer'):
            muxer = Ripper.Muxer(muxer)

            match muxer:
                case Ripper.Muxer.mp4:
                    muxer_format_str = r' && mp4box -add "{output}" -new "{output}" && mp4fpsmod ' + (f'-r 0:{force_fps}' if force_fps else '') + r' -i "{output}"'

                case Ripper.Muxer.mkv:
                    muxer_format_str = r' && mkvpropedit "{output}" --add-track-statistics-tags && mkvmerge -o "{output}.temp.mkv" "{output}" && mkvmerge -o "{output}" ' + (f'--default-duration 0:{force_fps}fps --fix-bitstream-timing-information 0:1' if force_fps else '') + r' --default-track-flag 0 "{output}.temp.mkv" && del /Q "{output}.temp.mkv"'

        else:
            muxer = None
            muxer_format_str = ''



        vspipe_input: str = ""
        pipe_gvar_list = [s for s in self.option_map.get('pipe:gvar', "").split(':') if s]
        pipe_gvar_dict = {s.split('=')[0]: s.split('=')[1] for s in pipe_gvar_list if '=' in s}
        if sub_pathname:
            pipe_gvar_dict['subtitle'] = sub_pathname

        if input_suffix == ".vpy":
            vspipe_input = f'vspipe -c y4m {" ".join(f'-a "{k}={v}"' for k,v in pipe_gvar_dict.items())} "{{input}}" - | '
        elif vpy_pathname:
            vspipe_input = f'vspipe -c y4m {" ".join(f'-a "{k}={v}"' for k,v in pipe_gvar_dict.items())} -a "input={{input}}" "{vpy_pathname}" - | '

        hwaccel = f"-hwaccel {hwaccel}" if (hwaccel := self.option_map.get("hwaccel")) else ""

        ffparams_ff = self.option_map.get('ff-params:ff') or self.option_map.get('ff-params', '')
        ffparams_in = self.option_map.get('ff-params:in', '')
        ffparams_out = self.option_map.get('ff-params:out', '')
        if _ss := self.option_map.get('ss'):
            ffparams_in += f' -ss {_ss}'
        if _t := self.option_map.get('t'):
            ffparams_out += f' -t {_t}'
        if _preset := self.option_map.get('v:preset'):
            ffparams_out += f' -preset {_preset}'

        FFMPEG_HEADER = f'ffmpeg -progress {FF_PROGRESS_LOG_FILE} -report {ffparams_ff} {ffparams_in}'


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
                    log.warning("The preset custom must have custom:format or custom:template")
                    encoder_format_str = ''

                else:
                    if encoder_format_str.startswith("''''"):
                        encoder_format_str = encoder_format_str[4:]
                    else:
                        encoder_format_str = encoder_format_str.replace("''", '"')
                    encoder_format_str = encoder_format_str.replace('\\34/', '"').replace('\\39/', "'").format_map(self.option_map | {'input': r'{input}', 'output': r'{output}'})


            case Ripper.PresetName.copy:

                hwaccel = f"-hwaccel {hwaccel}" if (hwaccel := self.option_map.get("hwaccel")) else ""

                encoder_format_str = (
                    f"{FFMPEG_HEADER} {hwaccel} "
                    + '-i "{input}" -c copy '
                    + f"{' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + f"{audio_option} {ffparams_out} "
                    + '"{output}"'
                )


            case Ripper.PresetName.flac:
                _encoder = {
                    "u8" : "pcm_u8",
                    "s16" : "pcm_s16le",
                    "s32" : "pcm_s32le",
                    "flt" : "pcm_s32le",
                    "dbl" : "pcm_s32le",

                    "u8p" : "pcm_u8",
                    "s16p" : "pcm_s16le",
                    "s32p" : "pcm_s32le",
                    "fltp" : "pcm_s32le",
                    "dblp" : "pcm_s32le",

                    "s64" : "pcm_s32le",
                    "s64p" : "pcm_s32le",
                }.get(self.info.sample_fmt, "pcm_s32le")
                if self.info.bits_per_raw_sample == 24 or self.info.bits_per_sample == 24:
                    _encoder = "pcm_s24le"

                encoder_format_str = (
                    FFMPEG_HEADER + ' -i "{input}" -map 0:a:0 -c:a '
                    f"{_encoder} {ffparams_out} "
                    '"{output}.temp.wav" && '
                    f" flac -j 32 -8 -e -p -l {'19' if self.info.sample_rate > 48000 else '12'} "
                    '-o "{output}" "{output}.temp.wav" && del /Q "{output}.temp.wav"'
                )


            case Ripper.PresetName.x264fast | Ripper.PresetName.x264slow:
                match preset_name:
                    case Ripper.PresetName.x264fast:
                        _option_map = {
                            'threads': self.option_map.get('threads', 'auto'),
                            # Select
                            'crf': self.option_map.get('crf', '20'),
                            'psy-rd': self.option_map.get('psy-rd', '0.6,0.15'),
                            'qcomp': self.option_map.get('qcomp', '0.66'),
                            'keyint': self.option_map.get('keyint', '250'),
                            'deblock': self.option_map.get('deblock', '0,0'),

                            # Default
                            'qpmin': self.option_map.get('qpmin', '8'),
                            'qpmax': self.option_map.get('qpmax', '32'),
                            'bframes': self.option_map.get('bframes', '8'),
                            'ref': self.option_map.get('ref', '4'),
                            'subme': self.option_map.get('subme', '5'),
                            'me': self.option_map.get('me', 'hex'),
                            'merange': self.option_map.get('merange', '16'),
                            'aq-mode': self.option_map.get('aq-mode', '1'),
                            'rc-lookahead': self.option_map.get('rc-lookahead', '60'),
                            'min-keyint': self.option_map.get('min-keyint', '2'),
                            'trellis': self.option_map.get('trellis', '1'),
                            'fast-pskip': self.option_map.get('fast-pskip', '1'),

                            # No change
                            'weightb' : '1',

                            **{
                                k: v
                                for k, v in [
                                    s.split('=')
                                    for s in str(self.option_map.get('x264-params', '')).split(':')
                                    if s != ""
                                ]
                            }
                        }
                    case Ripper.PresetName.x264slow:
                        _option_map = {
                            'threads': self.option_map.get('threads', 'auto'),
                            # Select
                            'crf': self.option_map.get('crf', '21'),
                            'psy-rd': self.option_map.get('psy-rd', '0.6,0.15'),
                            'qcomp': self.option_map.get('qcomp', '0.66'),
                            'keyint': self.option_map.get('keyint', '250'),
                            'deblock': self.option_map.get('deblock', '-1,-1'),

                            # Default
                            'qpmin': self.option_map.get('qpmin', '8'),
                            'qpmax': self.option_map.get('qpmax', '32'),
                            'bframes': self.option_map.get('bframes', '16'),
                            'ref': self.option_map.get('ref', '8'),
                            'subme': self.option_map.get('subme', '7'),
                            'me': self.option_map.get('me', 'umh'),
                            'merange': self.option_map.get('merange', '24'),
                            'aq-mode': self.option_map.get('aq-mode', '3'),
                            'rc-lookahead': self.option_map.get('rc-lookahead', '120'),
                            'min-keyint': self.option_map.get('min-keyint', '2'),
                            'trellis': self.option_map.get('trellis', '2'),
                            'fast-pskip': self.option_map.get('fast-pskip', '0'),

                            # No change
                            'weightb' : '1',

                            **{
                                k: v
                                for k, v in [
                                    s.split('=')
                                    for s in str(self.option_map.get('x264-params', '')).split(':')
                                    if s != ""
                                ]
                            }
                        }

                _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + f"{audio_option} -c:v libx264 {'' if is_pipe_input else '-pix_fmt yuv420p'} -x264-params "
                    + f'"{_param}" {ffparams_out} '
                    + (
                        f' -vf "{','.join(ff_vf_option)}" '
                        if len(ff_vf_option)
                        else ""
                    )
                    + ' "{output}"'
                )


            case Ripper.PresetName.x265fast4 | Ripper.PresetName.x265fast3 | Ripper.PresetName.x265fast2 | Ripper.PresetName.x265fast | Ripper.PresetName.x265slow | Ripper.PresetName.x265full:
                _default_option_map = {
                    'crf' : '20',
                    'qpmin' : '6',
                    'qpmax' : '32',

                    'rd' : '3',
                    'psy-rd' : '2',
                    'rdoq-level' : '0',
                    'psy-rdoq' : '0',

                    'qcomp' : '0.68',

                    'keyint' : '250',
                    'min-keyint' : '2',

                    'deblock' : '0,0',
                    
                    'me' : 'umh',
                    'merange' : '57',
                    'hme' : '1',
                    'hme-search' : 'hex,hex,hex',
                    'hme-range' : '16,57,92',

                    'aq-mode' : '2',
                    'aq-strength' : '1',

                    'tu-intra-depth' : '1',
                    'tu-inter-depth' : '1',
                    'limit-tu' : '0',

                    'bframes' : '16',
                    'ref' : '8',

                    'subme' : '2',

                    'open-gop' : '1',
                    'gop-lookahead' : '0',
                    'rc-lookahead' : '20',

                    'rect' : '0',
                    'amp' : '0',

                    'cbqpoffs' : '0',
                    'crqpoffs' : '0',
                    'ipratio' : '1.4',
                    'pbratio' : '1.3',

                    'early-skip' : '1',

                    'ctu' : '64',
                    'min-cu-size' : '8',
                    'max-tu-size' : '32',

                    'level-idc' : '0',

                    'sao' : '0',
                    'weightb' : '1',
                    'info' : '1',
                }
                _custom_option_map = {
                    'crf' : self.option_map.get('crf'),
                    'qpmin' : self.option_map.get('qpmin'),
                    'qpmax' : self.option_map.get('qpmax'),

                    'psy-rd' : self.option_map.get('psy-rd'),

                    'rd' : self.option_map.get('rd'),
                    'rdoq-level' : self.option_map.get('rdoq-level'),
                    'psy-rdoq' : self.option_map.get('psy-rdoq'),

                    'qcomp' : self.option_map.get('qcomp'),

                    'keyint' : self.option_map.get('keyint'),
                    'min-keyint' : self.option_map.get('min-keyint'),

                    'deblock' : self.option_map.get('deblock'),
                    
                    'me' : self.option_map.get('me'),
                    'merange' : self.option_map.get('merange'),
                    'hme' : self.option_map.get('hme'),
                    'hme-search' : self.option_map.get('hme-search'),
                    'hme-range' : self.option_map.get('hme-range'),

                    'aq-mode' : self.option_map.get('aq-mode'),
                    'aq-strength' : self.option_map.get('aq-strength'),

                    'tu-intra-depth' : self.option_map.get('tu-intra-depth'),
                    'tu-inter-depth' : self.option_map.get('tu-inter-depth'),
                    'limit-tu' : self.option_map.get('limit-tu'),

                    'bframes' : self.option_map.get('bframes'),
                    'ref' : self.option_map.get('ref'),

                    'subme' : self.option_map.get('subme'),

                    'open-gop' : self.option_map.get('open-gop'),
                    'gop-lookahead' : self.option_map.get('gop-lookahead'),
                    'rc-lookahead' : self.option_map.get('rc-lookahead'),

                    'rect' : self.option_map.get('rect'),
                    'amp' : self.option_map.get('amp'),

                    'cbqpoffs' : self.option_map.get('cbqpoffs'),
                    'crqpoffs' : self.option_map.get('crqpoffs'),
                    'ipratio' : self.option_map.get('ipratio'),
                    'pbratio' : self.option_map.get('pbratio'),

                    'early-skip' : self.option_map.get('early-skip'),

                    'ctu' : self.option_map.get('ctu'),
                    'min-cu-size' : self.option_map.get('min-cu-size'),
                    'max-tu-size' : self.option_map.get('max-tu-size'),

                    'level-idc' : self.option_map.get('level-idc'),

                    'sao' : self.option_map.get('sao'),

                    **{
                        k: v
                        for k, v in [
                            s.split('=')
                            for s in str(self.option_map.get('x265-params', '')).split(':')
                            if s != ""
                        ]
                    }
                }
                _custom_option_map = {k: v for k, v in _custom_option_map.items() if v is not None}

                match preset_name:
                    case Ripper.PresetName.x265fast4:
                        _option_map = {
                            'crf' : '18',
                            'qpmin' : '12',
                            'qpmax' : '28',

                            'rd' : '2',
                            'rdoq-level' : '1',

                            'me' : 'hex',
                            'merange' : '57',
                            'hme-search' : 'hex,hex,hex',
                            'hme-range' : '16,32,48',

                            'aq-mode' : '1',

                            'tu-intra-depth' : '1',
                            'tu-inter-depth' : '1',
                            'limit-tu' : '4',

                            'bframes' : '8',
                            'ref' : '6',

                            'subme' : '3',
                            'open-gop' : '0',
                            'gop-lookahead' : '0',
                            'rc-lookahead' : '48',

                            'cbqpoffs' : '-1',
                            'crqpoffs' : '-1',
                            'pbratio' : '1.28',
                        }
                    case Ripper.PresetName.x265fast3:
                        _option_map = {
                            'crf' : '18',
                            'qpmin' : '12',
                            'qpmax' : '28',

                            'rdoq-level' : '1',
                            'deblock' : '-0.5,-0.5',

                            'me' : 'hex',
                            'merange' : '57',
                            'hme-search' : 'hex,hex,hex',
                            'hme-range' : '16,32,57',

                            'aq-mode' : '3',

                            'tu-intra-depth' : '2',
                            'tu-inter-depth' : '2',
                            'limit-tu' : '4',

                            'bframes' : '12',
                            'ref' : '6',

                            'subme' : '3',
                            'open-gop' : '0',
                            'gop-lookahead' : '0',
                            'rc-lookahead' : '120',

                            'cbqpoffs' : '-1',
                            'crqpoffs' : '-1',
                            'pbratio' : '1.27',
                        }
                    case Ripper.PresetName.x265fast2:
                        _option_map = {
                            'crf' : '18',
                            'qpmin' : '12',
                            'qpmax' : '28',

                            'rdoq-level' : '2',
                            'deblock' : '-1,-1',

                            'me' : 'hex',
                            'merange' : '57',
                            'hme-search' : 'hex,hex,hex',
                            'hme-range' : '16,57,92',

                            'aq-mode' : '3',

                            'tu-intra-depth' : '3',
                            'tu-inter-depth' : '2',
                            'limit-tu' : '4',

                            'ref' : '6',

                            'subme' : '4',
                            'open-gop' : '0',
                            'gop-lookahead' : '0',
                            'rc-lookahead' : '192',

                            'cbqpoffs' : '-1',
                            'crqpoffs' : '-1',
                            'pbratio' : '1.25',
                        }
                    case Ripper.PresetName.x265fast:
                        _option_map = {
                            'crf' : '19',
                            'qpmin' : '12',
                            'qpmax' : '28',

                            'psy-rd' : '1.8',
                            'rdoq-level' : '2',
                            'psy-rdoq' : '0.4',
                            'keyint' : '312',
                            'deblock' : '-1,-1',

                            'me' : 'umh',
                            'merange' : '57',
                            'hme-search' : 'umh,hex,hex',
                            'hme-range' : '16,57,92',

                            'aq-mode' : '4',

                            'tu-intra-depth' : '4',
                            'tu-inter-depth' : '3',
                            'limit-tu' : '4',

                            'subme' : '5',
                            'gop-lookahead' : '8',
                            'rc-lookahead' : '216',

                            'cbqpoffs' : '-2',
                            'crqpoffs' : '-2',
                            'pbratio' : '1.2',
                        }
                    case Ripper.PresetName.x265slow:
                        _option_map = {
                            'crf' : '19',
                            'qpmin' : '12',
                            'qpmax' : '28',

                            'rd' : '5',
                            'psy-rd' : '1.8',
                            'rdoq-level' : '2',
                            'psy-rdoq' : '0.4',

                            'qcomp' : '0.7',

                            'keyint' : '312',

                            'deblock' : '-1,-1',

                            'me' : 'umh',
                            'merange' : '57',
                            'hme-search' : 'umh,hex,hex',
                            'hme-range' : '16,57,184',    

                            'aq-mode' : '4',
                            'aq-strength' : '1',

                            'tu-intra-depth' : '4',
                            'tu-inter-depth' : '3',
                            'limit-tu' : '2',

                            'subme' : '6',

                            'gop-lookahead' : '14',
                            'rc-lookahead' : '250',

                            'rect' : '1',

                            'min-keyint' : '2',
                            'cbqpoffs' : '-2',
                            'crqpoffs' : '-2',
                            'pbratio' : '1.2',
                            'early-skip' : '0',
                        }
                    case Ripper.PresetName.x265full:
                        _option_map = {
                            'crf' : '17',

                            'qpmin' : '3',
                            'qpmax' : '20',

                            'psy-rd' : '2.2',

                            'rd' : '5',
                            'rdoq-level' : '2',
                            'psy-rdoq' : '1.6',

                            'qcomp' : '0.72',

                            'keyint' : '266',
                            'min-keyint' : '2',

                            'deblock' : '-1,-1',
                            
                            'me' : 'umh',
                            'merange' : '160',
                            'hme-search' : 'full,umh,hex',
                            'hme-range' : '16,92,320',

                            'aq-mode' : '4',
                            'aq-strength' : '1.2',

                            'tu-intra-depth' : '4',
                            'tu-inter-depth' : '4',
                            'limit-tu' : '2',

                            'bframes' : '16',
                            'ref' : '8',

                            'subme' : '7',

                            'open-gop' : '1',
                            'gop-lookahead' : '14',
                            'rc-lookahead' : '250',

                            'rect' : '1',
                            'amp' : '1',

                            'cbqpoffs' : '-3',
                            'crqpoffs' : '-3',
                            'ipratio' : '1.43',
                            'pbratio' : '1.2',

                            'early-skip' : '0',
                        }

                _option_map = _default_option_map | _option_map | _custom_option_map

                if _option_map.get('hme', '0') == '0':
                    _option_map.pop('hme-search')
                    _option_map.pop('hme-range')

                _param = ":".join(
                    f"{key}={val}"
                    for key, val in _option_map.items()
                )

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f" -c:v libx265 {'' if is_pipe_input else '-pix_fmt yuv420p10le'} -x265-params "
                    + f' "{_param}" {ffparams_out} '
                    + (
                        f' -vf "{','.join(ff_vf_option)}" '
                        if len(ff_vf_option)
                        else ""
                    )
                    + ' "{output}"'
                )


            case Ripper.PresetName.h264_amf | Ripper.PresetName.h264_nvenc | Ripper.PresetName.h264_qsv | Ripper.PresetName.hevc_amf | Ripper.PresetName.hevc_nvenc | Ripper.PresetName.hevc_qsv:

                _option_map = {
                    'q:v': self.option_map.get('q:v'),
                    'pix_fmt' : self.option_map.get('pix_fmt'),
                    'preset:v' : self.option_map.get('preset:v'),
                }

                _param = ' '.join((f"-{key} {val}" for key, val in _option_map.items() if val))

                encoder_format_str = (
                    f"{vspipe_input} {FFMPEG_HEADER} {hwaccel} {' '.join(f'-i {s}' for s in ff_input_option)} {' '.join(f'-map {s}' for s in ff_stream_option)} "
                    + audio_option
                    + f" -c:v {preset_name.value} "
                    + f" {_param} {ffparams_out} "
                    + (
                        f' -vf "{','.join(ff_vf_option)}" '
                        if len(ff_vf_option)
                        else ""
                    )
                    + ' "{output}"'
                )


        return Ripper.Option(preset_name, encoder_format_str, audio_encoder, muxer, muxer_format_str)



    def _flush_progress(self, sleep_sec: float) -> None:
        while True:
            sleep(sleep_sec)

            if easyrip_web.http_server.Event.is_run_command[-1] is False:
                break

            try:
                with open(FF_PROGRESS_LOG_FILE, "rt", encoding="utf-8") as file:
                    file.seek(0, 2) # 将文件指针移动到文件末尾
                    total_size = file.tell() # 获取文件的总大小
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

            res = {line[0]:line[1] for line in (line.strip().split('=') for line in buffer[-12:])}

            if p := res.get('progress'):
                out_time_us = res.get('out_time_us', '')
                speed = res.get('speed', '').rstrip('x')

                self._progress['frame'] = int(res.get('frame', ''))
                self._progress['fps'] = float(res.get('fps', ''))
                self._progress['out_time_us'] = int(out_time_us) if out_time_us != 'N/A' else 0
                self._progress['speed'] = float(speed) if speed != 'N/A' else 0

                easyrip_web.http_server.Event.progress.append(self._progress)
                easyrip_web.http_server.Event.progress.popleft()

                if p != 'continue':
                    break

            else:
                continue
                
        easyrip_web.http_server.Event.progress.append({})
        easyrip_web.http_server.Event.progress.popleft()


    def run(self, prep_func = lambda _: None):

        if not os.path.exists(self.input_pathname):
            log.error('The file "{}" does not exist', self.input_pathname)


        else:

            prep_func(self)

            # 生成临时名
            basename = self.output_prefix
            temp_name = f'{basename}-{datetime.now().strftime('%Y-%m-%d_%H：%M：%S')}'
            suffix: str


            # 根据格式判断
            if self.option.preset_name == Ripper.PresetName.custom:

                suffix = f".{_suffix}" if (_suffix := self.option_map.get('custom:suffix')) else ''
                temp_name = temp_name+suffix
                cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname,  'output': os.path.join(self.output_dir, temp_name)})


            elif self.option.preset_name == Ripper.PresetName.flac:

                suffix = '.flac'
                temp_name = temp_name+suffix
                cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname, 'output': os.path.join(self.output_dir, temp_name)})


            else:

                match self.option.muxer:
                    case Ripper.Muxer.mp4:
                        suffix = '.va.mp4' if self.option.audio_encoder else '.rip.mp4'
                        temp_name = temp_name+suffix
                        cmd = ' '.join((
                            self.option.encoder_format_str,
                            self.option.muxer_format_str
                            )).format_map({'input': self.input_pathname, 'output': temp_name})

                    case Ripper.Muxer.mkv:
                        suffix = '.va.mkv' if self.option.audio_encoder else '.rip.mkv'
                        temp_name = temp_name+suffix
                        cmd = ' '.join((
                            self.option.encoder_format_str,
                            self.option.muxer_format_str
                            )).format_map({'input': self.input_pathname, 'output': temp_name})

                    case _:
                        suffix = '.va.mkv' if self.option.audio_encoder else '.rip.mkv'
                        temp_name = temp_name+suffix
                        cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname, 'output': os.path.join(self.output_dir, temp_name)})


            # 执行
            output_filename = basename+suffix
            run_start_time = datetime.now()
            log.write_html_log(
                f'<hr style="color:aqua;margin:4px 0 0;"><div style="background-color:#b4b4b4;padding:0 1rem;">'
                f'<span style="color:green;">{run_start_time.strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}</span> <span style="color:aqua;">{gettext("Start")}</span><br>'
                f'{gettext("Input file pathname")}: <span style="color:darkcyan;">"{self.input_pathname}"</span><br>'
                f'{gettext("Output directory")}: <span style="color:darkcyan;">"{self.output_dir}"</span><br>'
                f'{gettext("Temporary file name")}: <span style="color:darkcyan;">"{temp_name}"</span><br>'
                f'{gettext("Output file name")}: <span style="color:darkcyan;">"{output_filename}"</span><br>'
                f'Ripper:<br>'
                f'<span style="white-space:pre-wrap;color:darkcyan;">{self}</span></div>')

            # 先删除，防止直接读到结束标志
            if os.path.exists(FF_PROGRESS_LOG_FILE):
                os.remove(FF_PROGRESS_LOG_FILE)

            self._progress['frame_count'] = 0
            self._progress['duration'] = 0
            if not self.input_pathname.endswith('.vpy'):
                self._progress['frame_count'] = self.info.nb_frames
                self._progress['duration'] = self.info.duration

            Thread(target=self._flush_progress, args=(1,), daemon=True).start()

            log.info(cmd)
            if self.preset_name is not Ripper.PresetName.custom:
                os.environ["FFREPORT"] = f"file={FF_REPORT_LOG_FILE}:level=31"
            if os.system(cmd):
                log.error('There have error in running')


            # 获取 ffmpeg report 中的报错
            if os.path.exists(FF_REPORT_LOG_FILE):
                with open(FF_REPORT_LOG_FILE, 'rt', encoding='utf-8') as file:
                    for line in file.readlines()[2:]:
                        log.error('FFmpeg report: {}', line)

            # 获取体积
            temp_name_full = os.path.join(self.output_dir, temp_name)
            file_size = round(os.path.getsize(temp_name_full) / (1024 * 1024), 2) # MiB .2f

            # 将临时名重命名
            try:
                os.rename(temp_name_full, os.path.join(self.output_dir, output_filename))
            except FileExistsError as e:
                log.error(e)
            except Exception as e:
                log.error(e)

            # 读取编码速度
            speed: str = 'N/A'
            if os.path.exists(FF_PROGRESS_LOG_FILE):
                with open(FF_PROGRESS_LOG_FILE, 'rt', encoding='utf-8') as file:
                    for line in file.readlines()[::-1]:
                        if res := re.search(r'speed=(.*)', line):
                            speed = res.group(1)
                            break

            # 写入日志
            run_end_time = datetime.now()
            log.write_html_log(
                f'<div style="background-color:#b4b4b4;padding:0 1rem;">{gettext("Encoding speed")}: <span style="color:darkcyan;">{speed}</span><br>'
                f'{gettext("File size")}: <span style="color:darkcyan;">{file_size} MiB</span><br>'
                f'{gettext("Time consuming")}: <span style="color:darkcyan;">{str(run_end_time - run_start_time)[:-4]}</span><br>'
                f'<span style="color:green;">{run_end_time.strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}</span> <span style="color:brown;">{gettext("End")}</span><br>'
                f'</div><hr style="color:brown;margin:0 0 6px;">')

            # 删除临时文件
            if os.path.exists(FF_PROGRESS_LOG_FILE):
                os.remove(FF_PROGRESS_LOG_FILE)
            if os.path.exists(FF_REPORT_LOG_FILE):
                os.remove(FF_REPORT_LOG_FILE)



    def __init__(self, input_pathname: str, output_prefix: str | None, output_dir: str | None, option: Option | str, option_map: dict):

        self.input_pathname = input_pathname

        self.info = Ripper.Info()
        try:
            _info: dict = json.loads(
                subprocess.Popen(
                    [
                        "ffprobe",
                        "-v", "0",
                        "-select_streams", "v:0",
                        "-show_streams",
                        "-print_format", "json",
                        self.input_pathname,
                    ],
                    stdout=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                ).communicate()[0]
            )
            _info_list: list = _info.get("streams", [])

            _video_info_dict: dict = _info_list[0] if _info_list else dict()

            _fps_str: str = _video_info_dict.get("r_frame_rate", "0") + "/1"
            _fps = [int(s) for s in _fps_str.split("/")]
            self.info.r_frame_rate = (_fps[0], _fps[1])

            self.info.nb_frames = int(_video_info_dict.get("nb_frames", 0))
            self.info.duration = float(_video_info_dict.get("duration", 0))

            _info: dict = json.loads(
                subprocess.Popen(
                    [
                        "ffprobe",
                        "-v", "0",
                        "-select_streams", "a:0",
                        "-show_streams",
                        "-print_format", "json",
                        self.input_pathname,
                    ],
                    stdout=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                ).communicate()[0]
            )
            _info_list: list = _info.get("streams", [])

            _audio_info_dict: dict = _info_list[0] if _info_list else dict()
    
            self.info.sample_fmt = str(_audio_info_dict.get("sample_fmt", ""))
            self.info.sample_rate = int(_audio_info_dict.get("sample_rate", 0))
            self.info.bits_per_sample = int(_audio_info_dict.get("bits_per_sample", 0))
            self.info.bits_per_raw_sample = int(_audio_info_dict.get("bits_per_raw_sample", 0))

        except Exception as e:
            log.error(f"{repr(e)} {e}", deep=True, is_format=False)

        self.output_prefix = output_prefix if output_prefix else os.path.splitext(os.path.basename(input_pathname))[0]
        self.output_dir = output_dir or os.path.realpath(os.getcwd())
        self.option_map = option_map.copy()

        if isinstance(option, str):
            self.preset_name = Ripper.PresetName(option)
            self.option = self.preset_name_to_option(self.preset_name)
        else:
            self.preset_name = Ripper.PresetName.custom
            self.option = option

        self._progress = {}


    def __str__(self):
        return (
            f"-i {self.input_pathname} -o {self.output_prefix} -o:dir {self.output_dir} -preset {self.option.preset_name.value} {' '.join((f'-{key} {val}' for key, val in self.option_map.items()))}\n"
            "  option:  {\n"
            f"  {str(self.option).replace('\n', '\n  ')}\n"
            "  }\n"
            f"  option_map: {self.option_map}"
        )

import os
import subprocess
import re
from datetime import datetime
import enum

from easyrip_log import log
print = None

__all__ = ['Ripper']


ENCODING_LOG_FILE = "编码日志.html"
FF_PROGRESS_LOG_FILE = "progress.log"
FF_REPORT_LOG_FILE = "report.log"


class Ripper:

    ripper_list: list['Ripper'] = []

    class PresetName(enum.Enum):
        custom = enum.auto()
        copy = enum.auto()
        flac = enum.auto()
        x264slow = enum.auto()
        x265fast2 = enum.auto()
        x265fast = enum.auto()
        x265slow = enum.auto()
        x265full = enum.auto()

        @staticmethod
        def str_to_enum(name: str):
            try:
                return {
                    'custom': Ripper.PresetName.custom,
                    'copy': Ripper.PresetName.copy,
                    'flac': Ripper.PresetName.flac,
                    'x264slow': Ripper.PresetName.x264slow,
                    'x265fast2': Ripper.PresetName.x265fast2,
                    'x265fast': Ripper.PresetName.x265fast,
                    'x265slow': Ripper.PresetName.x265slow,
                    'x265full': Ripper.PresetName.x265full}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.PresetName: str_to_enum: {e}")

        @staticmethod
        def enum_to_str(name: 'Ripper.PresetName'):
            try:
                return {
                    Ripper.PresetName.custom: 'custom',
                    Ripper.PresetName.copy: 'copy',
                    Ripper.PresetName.flac: 'flac',
                    Ripper.PresetName.x264slow: 'x264slow',
                    Ripper.PresetName.x265fast2: 'x265fast2',
                    Ripper.PresetName.x265fast: 'x265fast',
                    Ripper.PresetName.x265slow: 'x265slow',
                    Ripper.PresetName.x265full: 'x265full'}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.PresetName: enum_to_str: {e}")

    class AudioCodec(enum.Enum):
        copy = enum.auto()
        libopus = enum.auto()

        @staticmethod
        def str_to_enum(name: str):
            try:
                return {
                    'libopus': Ripper.AudioCodec.libopus,
                    'copy': Ripper.AudioCodec.copy}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.AudioCodec: str_to_enum: {e}")

        @staticmethod
        def enum_to_str(name: 'Ripper.AudioCodec'):
            try:
                return {
                    Ripper.AudioCodec.libopus: 'libopus',
                    Ripper.AudioCodec.copy: 'copy'}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.AudioCodec: enum_to_str: {e}")

    class Muxer(enum.Enum):
        mp4 = enum.auto()
        mkv = enum.auto()

        @staticmethod
        def str_to_enum(name: str):
            try:
                return {
                    'mp4': Ripper.Muxer.mp4,
                    'mkv': Ripper.Muxer.mkv}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.Muxer: str_to_enum: {e}")

        @staticmethod
        def enum_to_str(name: 'Ripper.Muxer'):
            try:
                return {
                    Ripper.Muxer.mp4: 'mp4',
                    Ripper.Muxer.mkv: 'mkv'}[name]
            except KeyError as e:
                raise KeyError(f"Ripper.Muxer: enum_to_str: {e}")


    class Option:

        preset_name: 'Ripper.PresetName'
        encoder_format_str: str
        audio_encoder: 'Ripper.AudioCodec | None'
        muxer: 'Ripper.Muxer | None'
        muxer_format_str: str

        def __init__(self,
                     preset_name: 'Ripper.PresetName', format_str: str,
                     audio_encoder: 'Ripper.AudioCodec | None',
                     muxer: 'Ripper.Muxer | None', muxer_format_str: str):
            self.preset_name = preset_name
            self.encoder_format_str = format_str
            self.audio_encoder = audio_encoder
            self.muxer = muxer
            self.muxer_format_str = muxer_format_str

        def __str__(self):
            return f'  preset_name = {self.preset_name}\n  option_format = {self.encoder_format_str}'


    input_pathname: str
    output_prefix: str
    output_dir: str
    option: Option
    option_map: dict

    preset_name: PresetName


    def preset_name_to_option(self, preset_name: PresetName) -> Option:

        # Path
        input_suffix = os.path.splitext(self.input_pathname)[1]
        vpy_pathname = self.option_map.get('pipe')
        if sub_pathname := self.option_map.get('sub'):
            sub_pathname: str = f"'{sub_pathname.replace('\\', '/').replace(':', '\\:')}'"

        # Audio
        if audio_encoder := self.option_map.get('c:a'):
            _audio_encoder_str = audio_encoder
            audio_encoder = Ripper.AudioCodec.str_to_enum(audio_encoder)
            if input_suffix == '.vpy' or vpy_pathname:
                audio_option = r' -i "{input}" ' + f'-map 1:a -c:a {_audio_encoder_str} -b:a {self.option_map.get('b:a') or '160k'} '
            else:
                audio_option = f' -map 0:a -c:a {_audio_encoder_str} -b:a {self.option_map.get('b:a') or '160k'} '
        else:
            audio_option = ''

        # Muxer
        if muxer := self.option_map.get('muxer'):
            muxer = Ripper.Muxer.str_to_enum(muxer)
            force_fps = self.option_map.get('r') or self.option_map.get('fps')

            if muxer == Ripper.Muxer.mp4:
                muxer_format_str = r' && mp4box -add "{output}" -new "{output}" && mp4fpsmod ' + (f'-r 0:{force_fps}' if force_fps else '') + r' -i "{output}"'

            elif muxer == Ripper.Muxer.mkv:
                muxer_format_str = r' && mkvpropedit "{output}" --add-track-statistics-tags && mkvmerge -o "{output}.temp.mkv" "{output}" && mkvmerge -o "{output}" ' + (f'--default-duration 0:{force_fps}fps --fix-bitstream-timing-information 0:1' if force_fps else '') + r' --default-track-flag 0 "{output}.temp.mkv" && del /Q "{output}.temp.mkv"'

        else:
            muxer_format_str = ''




        FFMPEG_HEADER = f'ffmpeg -progress {FF_PROGRESS_LOG_FILE} -report'


        if preset_name == Ripper.PresetName.custom:
            if not (encoder_format_str := self.option_map.get('custom:format') or self.option_map.get('custom:template')):
                log.warning("The preset custom must have custom:format or custom:template")
                encoder_format_str = ''

            else:
                encoder_format_str: str = encoder_format_str.replace('\\34/', '"').replace('\\39/', "'").format_map(self.option_map | {'input': r'{input}', 'output': r'{output}'})


        elif preset_name == Ripper.PresetName.copy:
            encoder_format_str = FFMPEG_HEADER + r' -i "{input}" ' + audio_option + r' -map 0:v -c:v copy "{output}"'


        elif preset_name == Ripper.PresetName.flac:
            encoder_format_str = FFMPEG_HEADER + r' -i "{input}" -map 0:a:0 -f wav - | flac -j 32 -8 -e -p -l {maxlpc} -o "{output}" -'


        elif preset_name == Ripper.PresetName.x264slow:

            _option_map = {
                # Select
                'crf': self.option_map.get('crf') or '21',
                'psy-rd': self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '0.6,0.15',
                'qcomp': self.option_map.get('qcomp') or '0.66',
                'keyint': self.option_map.get('keyint') or '250',
                'deblock': self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin': self.option_map.get('qpmin') or '8',
                'qpmax': self.option_map.get('qpmax') or '32',
                'bframes': self.option_map.get('bframes') or '16',
                'ref': self.option_map.get('ref') or '8',
                'subme': self.option_map.get('subme') or '7',
                'me': self.option_map.get('me') or 'umh',
                'merange': self.option_map.get('merange') or '24',
                'aq-mode': self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '3',
                'rc-lookahead': self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '120',
                'min-keyint': self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'trellis': self.option_map.get('trellis') or '2',
                'fast-pskip': self.option_map.get('fast-pskip') or self.option_map.get('fastpskip') or '0',

                # No change
                'weightb' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            _threads = self.option_map.get('threads') or '16',
            if _threads != '16':
                _param += f':threads={_threads}'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if input_suffix == '.vpy':
                encoder_format_str = r'vspipe -c y4m "{input}" - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx264 -x264-params ' + f'"{_param}"' + r' "{output}"'

            elif vpy_pathname:
                encoder_format_str = r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx264 -x264-params ' + f'"{_param}"' + r' "{output}"'

            elif sub_pathname:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx264 -pix_fmt yuv420p -x264-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"'

            else:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx264 -pix_fmt yuv420p -x264-params ' + f'"{_param}" {custom_vf} ' + r' "{output}"'


        elif preset_name == Ripper.PresetName.x265fast2:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '18',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '2',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0',
                'qcomp' : self.option_map.get('qcomp') or '0.68',
                'keyint' : self.option_map.get('keyint') or '250',
                'deblock' : self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '12',
                'qpmax' : self.option_map.get('qpmax') or '28',

                'me' : self.option_map.get('me') or 'hex',
                'merange' : self.option_map.get('merange') or '57',
                'hme' : self.option_map.get('hme') or '1',
                'hme-search' : self.option_map.get('hme-search') or self.option_map.get('hmesearch') or 'hex,hex,hex',
                'hme-range' : self.option_map.get('hme-range') or self.option_map.get('hmerange') or '16,57,92',

                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '3',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1',

                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '3',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '2',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '4',

                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '6',

                'rd' : self.option_map.get('rd') or '3',
                'subme' : self.option_map.get('subme') or '5',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '0',
                'gop-lookahead' : self.option_map.get('gop-lookahead') or self.option_map.get('goplookahead') or '0',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '192',

                'rect' : self.option_map.get('rect') or '0',
                'amp' : self.option_map.get('amp') or '0',

                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-1',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-1',
                'ipratio' : self.option_map.get('ipratio') or '1.4',
                'pbratio' : self.option_map.get('pbratio') or '1.25',
                'early-skip' : self.option_map.get('early-skip') or self.option_map.get('earlyskip') or '1',

                'ctu' : self.option_map.get('ctu') or '64',
                'min-cu-size' : self.option_map.get('min-cu-size') or self.option_map.get('mincusize') or '8',
                'max-tu-size' : self.option_map.get('max-tu-size') or self.option_map.get('maxtusize') or '32',

                # No change
                'sao' : self.option_map.get('sao') or '0',
                'weightb' : '1',
                'info' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if input_suffix == '.vpy':
                encoder_format_str = r'vspipe -c y4m "{input}" - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif vpy_pathname:
                encoder_format_str = r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif sub_pathname:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"'

            else:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"'


        elif preset_name == Ripper.PresetName.x265fast:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '19',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4',
                'qcomp' : self.option_map.get('qcomp') or '0.66',
                'keyint' : self.option_map.get('keyint') or '312',
                'deblock' : self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '12',
                'qpmax' : self.option_map.get('qpmax') or '28',

                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '57',
                'hme' : self.option_map.get('hme') or '1',
                'hme-search' : self.option_map.get('hme-search') or self.option_map.get('hmesearch') or 'umh,hex,hex',
                'hme-range' : self.option_map.get('hme-range') or self.option_map.get('hmerange') or '16,57,92',

                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1',

                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '3',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '4',

                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',

                'rd' : self.option_map.get('rd') or '3',
                'subme' : self.option_map.get('subme') or '5',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '1',
                'gop-lookahead' : self.option_map.get('gop-lookahead') or self.option_map.get('goplookahead') or '8',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '216',

                'rect' : self.option_map.get('rect') or '0',
                'amp' : self.option_map.get('amp') or '0',

                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-2',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-2',
                'ipratio' : self.option_map.get('ipratio') or '1.4',
                'pbratio' : self.option_map.get('pbratio') or '1.2',
                'early-skip' : self.option_map.get('early-skip') or self.option_map.get('earlyskip') or '1',

                'ctu' : self.option_map.get('ctu') or '64',
                'min-cu-size' : self.option_map.get('min-cu-size') or self.option_map.get('mincusize') or '8',
                'max-tu-size' : self.option_map.get('max-tu-size') or self.option_map.get('maxtusize') or '32',

                # No change
                'sao' : self.option_map.get('sao') or '0',
                'weightb' : '1',
                'info' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if input_suffix == '.vpy':
                encoder_format_str = r'vspipe -c y4m "{input}" - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif vpy_pathname:
                encoder_format_str = r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif sub_pathname:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"'

            else:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"'


        elif preset_name == Ripper.PresetName.x265slow:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '19',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4',
                'qcomp' : self.option_map.get('qcomp') or '0.66',
                'keyint' : self.option_map.get('keyint') or '312',
                'deblock' : self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '12',
                'qpmax' : self.option_map.get('qpmax') or '28',

                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '57',
                'hme' : self.option_map.get('hme') or '1',
                'hme-search' : self.option_map.get('hme-search') or self.option_map.get('hmesearch') or 'umh,hex,hex',
                'hme-range' : self.option_map.get('hme-range') or self.option_map.get('hmerange') or '16,57,184',

                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1',

                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '3',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '2',

                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',

                'rd' : self.option_map.get('rd') or '5',
                'subme' : self.option_map.get('subme') or '7',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '1',
                'gop-lookahead' : self.option_map.get('gop-lookahead') or self.option_map.get('goplookahead') or '14',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '250',

                'rect' : self.option_map.get('rect') or '0',
                'amp' : self.option_map.get('amp') or '0',

                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-2',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-2',
                'ipratio' : self.option_map.get('ipratio') or '1.4',
                'pbratio' : self.option_map.get('pbratio') or '1.2',
                'early-skip' : self.option_map.get('early-skip') or self.option_map.get('earlyskip') or '0',

                'ctu' : self.option_map.get('ctu') or '64',
                'min-cu-size' : self.option_map.get('min-cu-size') or self.option_map.get('mincusize') or '8',
                'max-tu-size' : self.option_map.get('max-tu-size') or self.option_map.get('maxtusize') or '32',

                # No change
                'sao' : self.option_map.get('sao') or '0',
                'weightb' : '1',
                'info' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if input_suffix == '.vpy':
                encoder_format_str = r'vspipe -c y4m "{input}" - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif vpy_pathname:
                encoder_format_str = r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif sub_pathname:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"'
            else:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"'


        elif preset_name == Ripper.PresetName.x265full:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '17',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '3',
                'qpmax' : self.option_map.get('qpmax') or '20',

                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '2.2',

                'rd' : self.option_map.get('rd') or '5',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '1.6',

                'qcomp' : self.option_map.get('qcomp') or '0.72',

                'keyint' : self.option_map.get('keyint') or '266',
                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',

                'deblock' : self.option_map.get('deblock') or '-1,-1',
                
                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '160',
                'hme' : self.option_map.get('hme') or '1',
                'hme-search' : self.option_map.get('hme-search') or self.option_map.get('hmesearch') or 'full,umh,hex',
                'hme-range' : self.option_map.get('hme-range') or self.option_map.get('hmerange') or '16,92,320',

                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1.2',

                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '4',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '0',

                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',

                'subme' : self.option_map.get('subme') or '7',

                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '1',
                'gop-lookahead' : self.option_map.get('gop-lookahead') or self.option_map.get('goplookahead') or '14',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '250',

                'rect' : self.option_map.get('rect') or '1',
                'amp' : self.option_map.get('amp') or '1',

                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-3',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-3',
                'ipratio' : self.option_map.get('ipratio') or '1.43',
                'pbratio' : self.option_map.get('pbratio') or '1.2',

                'early-skip' : self.option_map.get('early-skip') or self.option_map.get('earlyskip') or '0',

                'ctu' : self.option_map.get('ctu') or '64',
                'min-cu-size' : self.option_map.get('min-cu-size') or self.option_map.get('mincusize') or '8',
                'max-tu-size' : self.option_map.get('max-tu-size') or self.option_map.get('maxtusize') or '32',

                # No change
                'sao' : self.option_map.get('sao') or '0',
                'weightb' : '1',
                'info' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if input_suffix == '.vpy':
                encoder_format_str = r'vspipe -c y4m "{input}" - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            elif vpy_pathname:
                encoder_format_str = r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ' + f'{FFMPEG_HEADER} -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"'

            else:
                encoder_format_str = f'{FFMPEG_HEADER} {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"'


        return Ripper.Option(preset_name, encoder_format_str, audio_encoder, muxer, muxer_format_str)



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

                suffix = f".{self.option_map.get('custom:suffix') or 'mkv'}"
                temp_name = temp_name+suffix
                cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname,  'output': os.path.join(self.output_dir, temp_name)})


            elif self.option.preset_name == Ripper.PresetName.flac:

                # 获取 maxlpc
                process_get_maxlpc = subprocess.Popen([
                    'ffmpeg',
                    '-i', self.input_pathname
                ],stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

                maxlpc: str
                for line in process_get_maxlpc.communicate()[0].splitlines():
                    if match := re.search(r'Stream ?#0:.*Audio:.*, *(\d+) *Hz', line):
                        if int(match.group(1)) > 48000:
                            maxlpc = '19'
                        else:
                            maxlpc = '12'
                        break

                suffix = '.flac'
                temp_name = temp_name+suffix
                cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname, 'maxlpc': maxlpc, 'output': os.path.join(self.output_dir, temp_name)})


            else:

                # 判断 muxer
                if self.option.muxer == Ripper.Muxer.mp4:
                    suffix = '.va.mp4' if self.option.audio_encoder else '.rip.mp4'
                    temp_name = temp_name+suffix
                    cmd = ' '.join((
                        self.option.encoder_format_str,
                        self.option.muxer_format_str
                        )).format_map({'input': self.input_pathname, 'output': temp_name})

                elif self.option.muxer == Ripper.Muxer.mkv:
                    suffix = '.va.mkv' if self.option.audio_encoder else '.rip.mkv'
                    temp_name = temp_name+suffix
                    cmd = ' '.join((
                        self.option.encoder_format_str,
                        self.option.muxer_format_str
                        )).format_map({'input': self.input_pathname, 'output': temp_name})

                else:
                    suffix = '.va.mkv' if self.option.audio_encoder else '.rip.mkv'
                    temp_name = temp_name+suffix
                    cmd = self.option.encoder_format_str.format_map({'input': self.input_pathname, 'output': os.path.join(self.output_dir, temp_name)})


            # 执行
            output_filename = basename+suffix
            run_start_time = datetime.now()
            with open(ENCODING_LOG_FILE, 'at', encoding='utf-8') as file:
                file.write(f'<hr style="color:aqua;margin:4px 0 0;"><div style="background-color:#b4b4b4;padding:0 4px;">'
                           f'<span style="color:green;">{run_start_time.strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}</span> <span style="color:aqua;">Start</span><br>'
                           f'原文件路径名：<span style="color:darkcyan;">"{self.input_pathname}"</span><br>'
                           f'输出目录：<span style="color:darkcyan;">"{self.output_dir}"</span><br>'
                           f'临时文件名：<span style="color:darkcyan;">"{temp_name}"</span><br>'
                           f'输出文件名：<span style="color:darkcyan;">"{output_filename}"</span><br>'
                           f'Option:<br>'
                           f'<span style="white-space:pre-wrap;color:darkcyan;">{self.option}</span></div>')

            log.info(cmd)
            os.environ["FFREPORT"] = f"file={FF_REPORT_LOG_FILE}:level=31"
            if os.system(cmd):
                log.error('There have error in running')


            # 获取 ffmpeg report 中的报错
            with open(FF_REPORT_LOG_FILE, 'rt') as f:
                for line in f.readlines()[2:]:
                    log.error('FFmpeg report: {}', line)

            # 获取体积
            temp_name_full = os.path.join(self.output_dir, temp_name)
            file_size = round(os.path.getsize(temp_name_full) / (1024 * 1024), 2) # MB .2f

            # 将临时名重命名
            try:
                os.rename(temp_name_full, os.path.join(self.output_dir, output_filename))
            except FileExistsError as e:
                log.error(e)
            except Exception as e:
                log.error(e)

            # 读取编码速度
            try:
                with open(FF_PROGRESS_LOG_FILE, 'rt', encoding='utf-8') as file:
                    progress = file.readlines()
                speed: str = 'N/A'
                for line in progress[::-1]:
                    if res := re.search(r'speed=(.*)', line):
                        speed = res.group(1)
                        break
            except Exception as e:
                log.error(e)

            # 写入日志
            run_end_time = datetime.now()
            with open(ENCODING_LOG_FILE, 'at', encoding='utf-8') as file:
                file.write(f'<div style="background-color:#b4b4b4;padding:0 4px;">Encoding speed=<span style="color:darkcyan;">{speed}</span><br>'
                           f'File size=<span style="color:darkcyan;">{file_size}</span><br>'
                           f'Time consuming=<span style="color:darkcyan;">{str(run_end_time - run_start_time)[:-4]}</span><br>'
                           f'<span style="color:green;">{run_end_time.strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}</span> <span style="color:brown;">End</span><br>'
                           f'</div><hr style="color:brown;margin:0 0 6px;">')

            # 删除临时文件
            if os.path.exists(FF_PROGRESS_LOG_FILE):
                os.remove(FF_PROGRESS_LOG_FILE)
            if os.path.exists(FF_REPORT_LOG_FILE):
                os.remove(FF_REPORT_LOG_FILE)



    def __init__(self, input_pathname: str, output_prefix: str | None, output_dir: str | None, option: Option | str, option_map: dict):

        self.input_pathname = input_pathname
        self.output_prefix = output_prefix if output_prefix else os.path.splitext(os.path.basename(input_pathname))[0]
        self.output_dir = output_dir or os.getcwd()
        self.option_map = option_map.copy()

        if type(option) is str:
            self.preset_name = Ripper.PresetName.str_to_enum(option)
            self.option = self.preset_name_to_option(self.preset_name)
        else:
            self.preset_name = Ripper.PresetName.custom
            self.option = option


    def __str__(self):
        return f'-i {self.input_pathname} -o {self.output_prefix} -o:dir {self.output_dir} {" ".join((f"-{key} {val}" for key, val in self.option_map.items()))}\n  option: ' + '{' + f'\n  {str(self.option).replace('\n', '\n  ')}' + '\n  }' + f'\n  option_map: {self.option_map}'



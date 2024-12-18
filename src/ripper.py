import os
import subprocess
import re
from datetime import datetime
import enum


from easyrip_log import log


class Ripper:

    ripper_list: list['Ripper'] = []

    class PresetName(enum.Enum):
        custom = enum.auto()
        flac = enum.auto()
        x264sub = enum.auto()
        x265veryfastsub = enum.auto()
        x265fast = enum.auto()
        x265slow = enum.auto()
        x265full = enum.auto()

        @staticmethod
        def str_to_enum(name: str):
            return {
                'custom': Ripper.PresetName.custom,
                'flac': Ripper.PresetName.flac,
                'x264sub': Ripper.PresetName.x264sub,
                'x265veryfastsub': Ripper.PresetName.x265veryfastsub,
                'x265fast': Ripper.PresetName.x265fast,
                'x265slow': Ripper.PresetName.x265slow,
                'x265full': Ripper.PresetName.x265full}[name]

        @staticmethod
        def enum_to_str(name: 'Ripper.PresetName'):
            return {
                Ripper.PresetName.custom: 'custom',
                Ripper.PresetName.flac: 'flac',
                Ripper.PresetName.x264sub: 'x264sub',
                Ripper.PresetName.x265veryfastsub: 'x265veryfastsub',
                Ripper.PresetName.x265fast: 'x265fast',
                Ripper.PresetName.x265slow: 'x265slow',
                Ripper.PresetName.x265full: 'x265full'}[name]

    class AudioCodec(enum.Enum):
        copy = enum.auto()
        libopus = enum.auto()

        @staticmethod
        def str_to_enum(name: str):
            return {
                'libopus': Ripper.AudioCodec.libopus,
                'copy': Ripper.AudioCodec.copy}[name]

        @staticmethod
        def enum_to_str(name: 'Ripper.AudioCodec'):
            return {
                Ripper.AudioCodec.libopus: 'libopus',
                Ripper.AudioCodec.copy: 'copy'}[name]


    class Option:

        def __init__(self, name: 'Ripper.PresetName', format: str):
            self.name = name
            self.format = format

        def __str__(self):
            return f'  option_name = {self.name}\n  option_format = {self.format}'


    input_pathname: str
    output_basename: str
    option: Option
    option_map: map

    preset_name: PresetName


    def preset_name_to_option(self, preset_name: PresetName) -> Option:

        input_suffix = os.path.splitext(self.input_pathname)[1]
        vpy_pathname = self.option_map.get('pipe')
        if sub_pathname := self.option_map.get('sub'):
            sub_pathname: str = f"'{sub_pathname.replace('\\', '/').replace(':', '\\:')}'"

        if audio_encoder := self.option_map.get('c:a'):
            if input_suffix == '.vpy' or vpy_pathname:
                audio_option = r' -i "{input}" ' + f'-map 1:a -c:a {audio_encoder} -b:a {self.option_map.get('b:a') or '160k'} '
            else:
                audio_option = f' -map 0:a -c:a {audio_encoder} -b:a {self.option_map.get('b:a') or '160k'} '
        else:
            audio_option = ''

        if preset_name == Ripper.PresetName.flac:
            return Ripper.Option(preset_name, r'ffmpeg -progress progress.log -i "{input}" -map 0:a:0 -f wav - | flac -8 -e -p -l {maxlpc} -o "{output}" -')


        elif preset_name == Ripper.PresetName.x264sub:

            _option_map = {
                # Select
                'crf': self.option_map.get('crf') or '24',
                'psy-rd': self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '0.6,0.15',
                'qcomp': self.option_map.get('qcomp') or '0.65',
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


            if input_suffix == '.vpy':
                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx264 -x264-params ' + f'"{_param}"' + r' "{output}"')

            elif vpy_pathname:
                return Ripper.Option('vs264', r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx264 -x264-params ' + f'"{_param}"' + r' "{output}"')

            elif sub_pathname:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx264 -pix_fmt yuv420p -x264-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')

            else:
                log.error("Missing subtitle pathname")
                raise Exception("Missing subtitle pathname")


        elif preset_name == Ripper.PresetName.x265veryfastsub:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '19.5',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '0',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4',
                'qcomp' : self.option_map.get('qcomp') or '0.66',
                'keyint' : self.option_map.get('keyint') or '250',
                'deblock' : self.option_map.get('deblock') or '0,0',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '14',
                'qpmax' : self.option_map.get('qpmax') or '30',
                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '57',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '0.8',
                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '3',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '2',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '4',
                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',
                'rd' : self.option_map.get('rd') or '3',
                'subme' : self.option_map.get('subme') or '5',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '0',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '192',
                'rect' : self.option_map.get('rect') or '0',
                'amp' : self.option_map.get('amp') or '0',
                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-1',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-1',
                'ipratio' : self.option_map.get('ipratio') or '1.4',
                'pbratio' : self.option_map.get('pbratio') or '1.25',

                # No change
                'sao' : '0',
                'weightb' : '1',
                'info' : '1'
            }

            _param = ':'.join((f"{key}={val}" for key, val in _option_map.items()))

            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif sub_pathname:
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')

            else:
                log.error("Missing subtitle pathname")
                raise Exception("Missing subtitle pathname")


        elif preset_name == Ripper.PresetName.x265fast:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '19.5',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4',
                'qcomp' : self.option_map.get('qcomp') or '0.66',
                'keyint' : self.option_map.get('keyint') or '312',
                'deblock' : self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '12',
                'qpmax' : self.option_map.get('qpmax') or '30',
                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '57',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1',
                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '3',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '4',
                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',
                'rd' : self.option_map.get('rd') or '3',
                'subme' : self.option_map.get('subme') or '5',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '0',
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

                # No change
                'sao' : '0',
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
                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif vpy_pathname:
                return Ripper.Option('vs264', r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif sub_pathname:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')

            else:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"')


        elif preset_name == Ripper.PresetName.x265slow:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '19.5',
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4',
                'qcomp' : self.option_map.get('qcomp') or '0.66',
                'keyint' : self.option_map.get('keyint') or '312',
                'deblock' : self.option_map.get('deblock') or '-1,-1',

                # Default
                'qpmin' : self.option_map.get('qpmin') or '12',
                'qpmax' : self.option_map.get('qpmax') or '30',
                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '57',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1',
                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '3',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '2',
                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',
                'rd' : self.option_map.get('rd') or '5',
                'subme' : self.option_map.get('subme') or '7',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '0',
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

                # No change
                'sao' : '0',
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

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif vpy_pathname:

                return Ripper.Option('vs264', r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif sub_pathname:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')
            else:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"')


        elif preset_name == Ripper.PresetName.x265full:

            _option_map = {
                # Select
                'crf' : self.option_map.get('crf') or '17.5',

                # Default
                'psy-rd' : self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '2.2',
                'rdoq-level' : self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2',
                'psy-rdoq' : self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '1.6',
                'qcomp' : self.option_map.get('qcomp') or '0.7',
                'keyint' : self.option_map.get('keyint') or '266',
                'deblock' : self.option_map.get('deblock') or '-1,-1',
                'qpmin' : self.option_map.get('qpmin') or '3',
                'qpmax' : self.option_map.get('qpmax') or '25',
                'me' : self.option_map.get('me') or 'umh',
                'merange' : self.option_map.get('merange') or '160',
                'aq-strength' : self.option_map.get('aq-strength') or self.option_map.get('aqstrength') or '1.2',
                'tu-intra-depth' : self.option_map.get('tu-intra-depth') or self.option_map.get('tuintradepth') or '4',
                'tu-inter-depth' : self.option_map.get('tu-inter-depth') or self.option_map.get('tuinterdepth') or '4',
                'limit-tu' : self.option_map.get('limit-tu') or self.option_map.get('limittu') or '0',
                'aq-mode' : self.option_map.get('aq-mode') or self.option_map.get('aqmode') or '4',
                'bframes' : self.option_map.get('bframes') or '16',
                'ref' : self.option_map.get('ref') or '8',
                'rd' : self.option_map.get('rd') or '5',
                'subme' : self.option_map.get('subme') or '7',
                'open-gop' : self.option_map.get('open-gop') or self.option_map.get('opengop') or '0',
                'gop-lookahead' : self.option_map.get('gop-lookahead') or self.option_map.get('goplookahead') or '14',
                'rc-lookahead' : self.option_map.get('rc-lookahead') or self.option_map.get('rclookahead') or '250',
                'rect' : self.option_map.get('rect') or '1',
                'amp' : self.option_map.get('amp') or '1',
                'min-keyint' : self.option_map.get('min-keyint') or self.option_map.get('minkeyint') or '2',
                'cbqpoffs' : self.option_map.get('cbqpoffs') or '-3',
                'crqpoffs' : self.option_map.get('crqpoffs') or '-3',
                'ipratio' : self.option_map.get('ipratio') or '1.43',
                'pbratio' : self.option_map.get('pbratio') or '1.2',
                'early-skip' : self.option_map.get('early-skip') or self.option_map.get('earlyskip') or '0',

                # No change
                'sao' : '0',
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
                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            elif vpy_pathname:
                return Ripper.Option('vs264', r'vspipe -c y4m -a "input={input}" ' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - ' + audio_option + r' -map 0:v -c:v libx265 -x265-params ' + f'"{_param}"' + r' "{output}"')

            else:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" ' + audio_option + r' -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{_param}" {custom_vf} ' + r'"{output}"')


    def run(self, format_map: map = {}):

        if not os.path.exists(self.input_pathname):
            log.error(f'The file {self.input_pathname} does not exist')



        if self.option.name == Ripper.PresetName.custom:
            os.system(self.option.format.format_map(format_map))


        else:

            # 生成临时名
            basename = self.output_basename
            temp_name = f'{basename}-{datetime.now().strftime('%Y-%m-%d_%H：%M：%S')}'
            suffix: str



            # 根据格式判断
            if self.option.name == Ripper.PresetName.flac:

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
                cmd = self.option.format.format_map({'input': self.input_pathname, 'maxlpc': maxlpc, 'output': temp_name})


            else:

                suffix = '.va.mkv' if self.option_map.get('c:a') else '.rip.mkv'
                temp_name = temp_name+suffix
                cmd = self.option.format.format_map({'input': self.input_pathname, 'output': temp_name})


            # 执行
            output_filename = basename+suffix
            with open('编码日志.log', 'at', encoding='utf-8') as file:
                file.write(f'{log.hr}\n{datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]} Start\n原文件路径名："{self.input_pathname}"\n临时文件名："{temp_name}"\n输出文件名："{output_filename}"\nOption:\n{self.option}\n')

            log.info(cmd)
            os.system(cmd)



            # 将临时名重命名
            try:
                os.rename(temp_name, output_filename)
            except FileExistsError as e:
                log.error(e)
            except Exception as e:
                log.error(e)


            # 写入日志
            try:
                with open('progress.log', 'rt', encoding='utf-8') as file:
                    progress = file.readlines()
                speed: str = 'N/A'
                for line in progress[::-1]:
                    if res := re.search(r'speed=(.*)', line):
                        speed = res.group(1)
                        break
            except Exception as e:
                log.error(e)

            with open('编码日志.log', 'at', encoding='utf-8') as file:
                file.write(f'Encoding speed={speed}\n{datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]} End\n{log.hr}\n')


    def __init__(self, input_pathname: str, output_basename: str | None, option: Option | str, option_map: map):

        self.input_pathname = input_pathname
        self.output_basename = output_basename if output_basename else os.path.splitext(os.path.basename(input_pathname))[0]
        self.option_map = option_map

        if type(option) == str:
            self.preset_name = Ripper.PresetName.str_to_enum(option)
            self.option = self.preset_name_to_option(self.preset_name)
        else:
            self.preset_name = Ripper.PresetName.custom
            self.option = option


    def __str__(self):
        return f'-i "{self.input_pathname}" -o "{self.output_basename}" -preset {Ripper.PresetName.enum_to_str(self.preset_name)}\n  option: ' + '{' + f'\n  {str(self.option).replace('\n', '\n  ')}' + '\n  }' + f'\n  option_map: {self.option_map}'



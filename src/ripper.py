import os
import subprocess
import re
from datetime import datetime
import enum


from easy_rip_log import log


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


    class Option:
        def __init__(self, name: 'Ripper.PresetName', format: str):
            self.name = name
            self.format = format


    input_pathname: str
    output_basename: str
    option: Option
    option_map: map
    
            
    def preset_name_to_option(self, preset_name: PresetName) -> Option:
        
        if preset_name == Ripper.PresetName.flac:
            return Ripper.Option(preset_name, r'ffmpeg -progress progress.log -i "{input}" -map 0:a:0 -c copy -f wav - | flac -8 -e -p -l {maxlpc} -o "{output}" -')


        elif preset_name == Ripper.PresetName.x264sub:

            threads = self.option_map.get('threads') or '16'
            crf = self.option_map.get('crf') or '24'
            psyrd = self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '0.6,0.15'
            qcomp = self.option_map.get('qcomp') or '0.65'
            keyint = self.option_map.get('keyint') or '250'
            deblock = self.option_map.get('deblock') or '-1,-1'

            param = f'crf={crf}:qpmin=8:qpmax=32:bframes=16:ref=8:subme=7:me=umh:merange=24:aq-mode=3:weightb=1:deblock={deblock}:rc-lookahead=120:keyint={keyint}:min-keyint=2:psy-rd={psyrd}:qcomp={qcomp}:trellis=2:fast-pskip=0'
            if threads != '16':
                param += f':threads={threads}'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx264 -x264-params ' + f'"{param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a ""' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx264 -x264-params ' + f'"{param}"' + r' "{output}"')

            else:

                if sub_pathname := self.option_map.get('sub'):
                    sub_pathname: str = "'" +sub_pathname.replace('\\', '/').replace(':', '\\:') + "'"
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx264 -pix_fmt yuv420p -x264-params ' + f'"{param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')
                else:
                    log.error("Missing subtitle pathname")
                    raise Exception("Missing subtitle pathname")


        elif preset_name == Ripper.PresetName.x265veryfastsub:

            crf = self.option_map.get('crf') or '19.5'
            psyrd = self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8'
            rdoqlevel = self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '0'
            psyrdoq = self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4'
            qcomp = self.option_map.get('qcomp') or '0.66'
            keyint = self.option_map.get('keyint') or '250'
            deblock = self.option_map.get('deblock') or '0,0'

            param = f'crf={crf}:qpmin=14:qpmax=30:me=umh:merange=57:aq-strength=0.8:tu-intra-depth=3:tu-inter-depth=2:limit-tu=4:aq-mode=4:bframes=16:ref=8:rd=3:subme=5:open-gop=0:rc-lookahead=192:sao=0:rect=0:amp=0:rdoq-level={rdoqlevel}:psy-rdoq={psyrdoq}:psy-rd={psyrd}:qcomp={qcomp}:weightb=1:deblock={deblock}:min-keyint=2:cbqpoffs=-1:crqpoffs=-1:keyint={keyint}:ipratio=1.4:pbratio=1.25:info=1'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a ""' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            else:

                if sub_pathname := self.option_map.get('sub'):
                    sub_pathname: str = "'" +sub_pathname.replace('\\', '/').replace(':', '\\:') + "'"
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')
                else:
                    log.error("Missing subtitle pathname")
                    raise Exception("Missing subtitle pathname")


        elif preset_name == Ripper.PresetName.x265fast:

            crf = self.option_map.get('crf') or '19.5'
            psyrd = self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8'
            rdoqlevel = self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2'
            psyrdoq = self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4'
            qcomp = self.option_map.get('qcomp') or '0.66'
            keyint = self.option_map.get('keyint') or '312'
            deblock = self.option_map.get('deblock') or '-1,-1'

            param = f'crf={crf}:qpmin=12:qpmax=30:me=umh:merange=57:aq-strength=1:tu-intra-depth=4:tu-inter-depth=3:limit-tu=4:aq-mode=4:bframes=16:ref=8:rd=3:subme=5:gop-lookahead=8:rc-lookahead=216:sao=0:rect=0:amp=0:rdoq-level={rdoqlevel}:psy-rdoq={psyrdoq}:psy-rd={psyrd}:qcomp={qcomp}:weightb=1:deblock={deblock}:min-keyint=2:cbqpoffs=-2:crqpoffs=-2:keyint={keyint}:ipratio=1.4:pbratio=1.2:info=1:early-skip=1'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a ""' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            else:

                if sub_pathname := self.option_map.get('sub'):
                    sub_pathname: str = "'" +sub_pathname.replace('\\', '/').replace(':', '\\:') + "'"
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')
                else:
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}" {custom_vf} ' + r'"{output}"')


        elif preset_name == Ripper.PresetName.x265slow:

            crf = self.option_map.get('crf') or '19.5'
            psyrd = self.option_map.get('psy-rd') or self.option_map.get('psyrd') or '1.8'
            rdoqlevel = self.option_map.get('rdoq-level') or self.option_map.get('rdoqlevel') or '2'
            psyrdoq = self.option_map.get('psy-rdoq') or self.option_map.get('psyrdoq') or '0.4'
            qcomp = self.option_map.get('qcomp') or '0.66'
            keyint = self.option_map.get('keyint') or '312'
            deblock = self.option_map.get('deblock') or '-1,-1'

            param = f'crf={crf}:qpmin=12:qpmax=30:me=umh:merange=57:aq-strength=1:tu-intra-depth=4:tu-inter-depth=3:limit-tu=2:aq-mode=4:bframes=16:ref=8:rd=5:subme=7:gop-lookahead=14:rc-lookahead=250:sao=0:rect=0:amp=0:rdoq-level={rdoqlevel}:psy-rdoq={psyrdoq}:psy-rd={psyrd}:qcomp={qcomp}:weightb=1:deblock={deblock}:min-keyint=2:cbqpoffs=-2:crqpoffs=-2:keyint={keyint}:ipratio=1.4:pbratio=1.2:info=1:early-skip=0'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a ""' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            else:

                if sub_pathname := self.option_map.get('sub'):
                    sub_pathname: str = "'" +sub_pathname.replace('\\', '/').replace(':', '\\:') + "'"
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}"' + f' -vf "ass={sub_pathname}"' + r' "{output}"')
                else:
                    return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}" {custom_vf} ' + r'"{output}"')


        elif preset_name == Ripper.PresetName.x265full:

            crf = self.option_map.get('crf') or '17.5'

            param = f'crf={crf}:qpmin=3:qpmax=25:me=umh:merange=160:aq-strength=1.2:tu-intra-depth=4:tu-inter-depth=4:limit-tu=0:aq-mode=4:bframes=16:ref=8:rd=5:subme=7:gop-lookahead=14:rc-lookahead=250:sao=0:rect=1:amp=1:rdoq-level=2:psy-rdoq=1.6:psy-rd=2.2:qcomp=0.7:weightb=1:deblock=-1,-1:min-keyint=2:info=1:cbqpoffs=-3:crqpoffs=-3:keyint=360:ipratio=1.43:pbratio=1.2:early-skip=0'


            if hwaccel := self.option_map.get('hwaccel'):
                hwaccel = f"-hwaccel {hwaccel}"
            else:
                hwaccel = ""


            if self.option_map.get('deinterlacing') not in ('0', None):
                custom_vf = "-vf yadif"
            else:
                custom_vf = ""


            if os.path.splitext(self.input_pathname)[1] == '.vpy':

                return Ripper.Option('vs264', r'vspipe -c y4m "{input}" - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            elif vpy_pathname := self.option_map.get('pipe'):

                return Ripper.Option('vs264', r'vspipe -c y4m -a ""' + f'"{vpy_pathname}"' + r' - | ffmpeg -progress progress.log -i - -map 0:v -c:v libx265 -x265-params ' + f'"{param}"' + r' "{output}"')

            else:
                return Ripper.Option(preset_name, f'ffmpeg -progress progress.log {hwaccel} ' + r'-i "{input}" -map 0:v -c:v libx265 -pix_fmt yuv420p10le -x265-params ' + f'"{param}" {custom_vf} ' + r'"{output}"')


    def run(self, format_map: map = {}):

        if self.option.name == Ripper.PresetName.custom:
            os.system(self.option.format.format_map(format_map))


        else:

            # 生成临时名
            basename = self.output_basename
            temp_name = f'{basename}-{datetime.now().strftime('%Y-%m-%d_%H：%M：%S')}'
            suffix: str

            # 执行
            if self.option.name == Ripper.PresetName.flac:

                # 获取 maxlpc
                process_get_maxlpc = subprocess.Popen([
                    'ffmpeg',
                    '-i', self.pathname
                ],stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

                maxlpc: str
                for line in process_get_maxlpc.communicate()[0].splitlines():
                    if match := re.search(r'Stream ?#0:.*Audio:.*, *(\d+) *Hz', line):
                        if int(match.group(1)) > 48000:
                            maxlpc = '19'
                        else:
                            maxlpc = '12'
                        break

                # 执行
                suffix = '.flac'
                os.system(self.option.format.format_map({'input': self.input_pathname, 'maxlpc': maxlpc, 'output': temp_name+suffix}))

            else:

                suffix = '.rip.mkv'
                os.system(self.option.format.format_map({'input': self.input_pathname, 'output': temp_name+suffix}))


            # 将临时名重命名
            os.rename(temp_name+suffix, basename+suffix)


    def __init__(self, input_pathname: str, output_basename: str | None, option: Option | str, option_map: map):

        self.input_pathname = input_pathname
        self.output_basename = output_basename if output_basename else os.path.splitext(os.path.basename(input_pathname))[0]
        self.option_map = option_map

        if type(option) == str:
            name = {
                'custom': Ripper.PresetName.custom,
                'flac': Ripper.PresetName.flac,
                'x264sub': Ripper.PresetName.x264sub,
                'x265veryfastsub': Ripper.PresetName.x265veryfastsub,
                'x265fast': Ripper.PresetName.x265fast,
                'x265slow': Ripper.PresetName.x265slow,
                'x265full': Ripper.PresetName.x265full}[option]
            self.option = self.preset_name_to_option(name)
            print('++++++', self.option)
        else:
            self.option = option


    def __str__(self):
        return f'-i {self.input_pathname} -o '



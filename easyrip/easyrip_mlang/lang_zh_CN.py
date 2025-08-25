from ..global_val import Global_val
from .global_lang_val import Global_lang_val

lang_map: dict[str | Global_lang_val.Extra_text_index, str] = {
    Global_lang_val.Extra_text_index.HELP_DOC: (
        f"{Global_val.PROJECT_NAME}\n版本: {Global_val.PROJECT_VERSION}\n{Global_val.PROJECT_URL}\n"
        "\n"
        "\n"
        "帮助:\n"
        "  输入命令或使用命令行传参以运行\n"
        "\n"
        "\n"
        "可用命令:\n"
        "\n"
        "  h / help\n"
        "    打印 help\n"
        "\n"
        "  v / ver / version\n"
        "    打印版本信息\n"
        "\n"
        "  log [<日志级别>] <message>\n"
        "    输出自定义日志\n"
        "    日志级别:\n"
        "      info, warning | warn, error | err, send, debug\n"
        "      默认: info\n"
        "\n"
        "  $ <code>\n"
        "    直接从内部环境运行代码\n"
        "    直接执行 $ 之后的代码\n"
        '    字符串"\\N"将变为实际的"\\n"\n'
        "\n"
        "  exit\n"
        "    退出程序\n"
        "\n"
        "  cd <string>\n"
        "    更改当前目录\n"
        "\n"
        "  dir\n"
        "    打印当前目录的所有文件和文件夹的名字\n"
        "\n"
        "  mkdir / makedir <string>\n"
        "    新建路径\n"
        "\n"
        "  cls / clear\n"
        "    清屏\n"
        "\n"
        "  list <list 选项>\n"
        "    操作 ripper list\n"
        "\n"
        "    默认:\n"
        "      打印 ripper list\n"
        "\n"
        "    clear / clean:\n"
        "      清空 ripper list\n"
        "\n"
        "    del / pop <index>:\n"
        "      删除 ripper list 中指定的一个 ripper\n"
        "\n"
        "    sort [n][r]:\n"
        "      排序 list\n"
        "      'n': 自然排序\n"
        "      'r': 倒序\n"
        "\n"
        "    <int> <int>:\n"
        "      交换指定索引\n"
        "\n"
        "  run [<run option>]\n"
        "    执行 ripper list 中的 ripper\n"
        "\n"
        "    默认:\n"
        "      仅执行\n"
        "\n"
        "    exit:\n"
        "      执行后退出程序\n"
        "\n"
        "    shutdown [<秒数>]:\n"
        "      执行后关机\n"
        "      默认: 60\n"
        "\n"
        "    server [<地址> [<端口> [<密码>]]]:\n"
        "      启动 web 服务\n"
        '      默认: server "" 0\n'
        "      客户端发送命令 'kill' 可以退出 ripper 的运行，注意，FFmpeg需要接受多次^C信号才能强制终止，单次^C会等待文件输出完才会终止\n"
        "\n"
        "    config <config 选项>:\n"
        "      regenerate | clear | clean | reset\n"
        "        重新生成 config 文件\n"
        "      open\n"
        "        打开 config 文件所在目录\n"
        "      list\n"
        "        展示所有 config 可调选项\n"
        "      set <key> <val>\n"
        "        设置 config，例如 config set language en\n"
        "\n"
        "  <Option>\n"
        "    -i <输入> -o <输出> [-o:dir <目录>] -preset <预设名> [-pipe <vpy 路径名> -crf <值> -psy-rd <值> ...] [-sub <字幕文件路径名>] [-c:a <音频编码器> -b:a <音频码率>] [-muxer <复用器> [-r <帧率>]] [-run [<run 选项>]]\n"
        "      往 ripper list 中添加一个 ripper，你可以单独设置预设中每个选项的值，使用 -run 执行 ripper\n"
        "\n"
        "\n"
        "Easy Rip options:\n"
        "\n"
        "  -i <string[::string[?string...]...] | 'fd'>\n"
        "    输入文件的路径名或输入'fd'以使用文件对话框\n"
        "    部分情况下允许使用 '?' 作为间隔符往一个 ripper 中输入多个，例如 '-preset subset' 允许输入多个 ASS\n"
        "\n"
        "  -o <string>\n"
        "    输出文件的文件名前缀\n"
        "    多个输入时允许有迭代器和时间格式化:\n"
        '      e.g. "name--?{start=6,padding=4,increment=2}--?{time:%Y.%m.%S}"\n'
        "\n"
        "  -auto-infix <0 | 1>\n"
        "    If enable, output file name will have auto infix:\n"
        "      no audio: '.v'\n"
        "      with audio: '.va'\n"
        "    Default: 1\n"
        "\n"
        "  -o:dir <string>\n"
        "    输出文件的目标目录\n"
        "\n"
        "  -preset <string>\n"
        "    设置预设\n"
        "    预设名:\n"
        "      custom\n"
        "      subset\n"
        "      copy\n"
        "      flac\n"
        "      x264fast x264slow\n"
        "      x265fast4 x265fast3 x265fast2 x265fast x265slow x265full\n"
        "      h264_amf h264_nvenc h264_qsv\n"
        "      hevc_amf hevc_nvenc hevc_qsv\n"
        "      av1_amf av1_nvenc av1_qsv\n"
        "\n"
        "  -pipe <string>\n"
        "    选择一个 vpy 文件作为管道的输入，这个 vpy 必须有 input 全局变量\n"
        "    演示如何 input: vspipe -a input=<input> filter.vpy\n"
        "\n"
        "  -pipe:gvar <key>=<val>[:...]\n"
        "    自定义传给 vspipe 的全局变量，多个则用':'间隔\n"
        '    例如: -pipe:gvar "a=1 2 3:b=abc" -> vspipe -a "a=1 2 3" -a "b=abc"\n'
        "\n"
        "  -vf <string>\n"
        "    自定义 FFmpeg 的 -vf\n"
        "    与 -sub 同时使用为未定义行为\n"
        "\n"
        "  -sub <string | 'auto' | 'auto:...'>\n"
        "    它使用 libass 制作硬字幕，需要硬字幕时请输入字幕路径名\n"
        '    使用 "::" 以输入多个字幕，例如: 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n'
        "    如果使用'auto'，相同前缀的字幕文件将作为输入\n"
        "    'auto:...'可以只选择指定中缀，例如'auto:zh-Hans:zh-Hant'\n"
        "\n"
        "  -only-mux-sub-path <string>\n"
        "    All subtitles and fonts in this path will be muxed\n"
        "\n"
        "  -soft-sub <string[?string...] | 'auto' | 'auto:...'>\n"
        "    往 MKV 中封装子集化字幕\n"
        "\n"
        "  -subset-font-dir <string[?string...]>\n"
        "    子集化时使用的字体的目录\n"
        '    默认: 优先当前目录，其次当前目录下含有 "font" 的文件夹 (不分大小写)\n'
        "\n"
        "  -subset-font-in-sub <0 | 1>\n"
        "    将字体编码到 ASS 文件中，而不是单独的字体文件\n"
        "    默认: 0\n"
        "\n"
        "  -subset-use-win-font <0 | 1>\n"
        "    无法从 subset-font-dir 找到字体时使用 Windows 字体\n"
        "    默认: 0\n"
        "\n"
        "  -subset-use-libass-spec <0 | 1>\n"
        "    子集化时使用 libass 规范\n"
        '    e.g. "11\\{22}33" ->\n'
        '      "11\\33"   (VSFilter)\n'
        '      "11{22}33" (libass)\n'
        "    默认: 0\n"
        "\n"
        "  -subset-drop-non-render <0 | 1>\n"
        "    丢弃 ASS 中的注释行、Name、Effect等非渲染内容\n"
        "    默认: 1\n"
        "\n"
        "  -subset-drop-unkow-data <0 | 1>\n"
        "    丢弃 ASS 中的非 {[Script Info], [V4+ Styles], [Events]} 行\n"
        "    默认: 1\n"
        "\n"
        "  -subset-strict <0 | 1>\n"
        "    子集化时报错则中断\n"
        "    默认: 0\n"
        "\n"
        "  -c:a <string>\n"
        "    设置音频编码器\n"
        "\n"
        "    音频编码器:\n"
        "      copy\n"
        "      libopus\n"
        "      flac\n"
        "\n"
        "  -b:a <string>\n"
        "    设置音频码率。默认值 '160k'\n"
        "\n"
        "  -muxer <string>\n"
        "    设置复用器\n"
        "\n"
        "    可用的复用器:\n"
        "      mp4\n"
        "      mkv\n"
        "\n"
        "  -r / -fps <string | 'auto'>\n"
        "    设置封装的帧率\n"
        "    使用 auto 时，自动从输入的视频获取帧率，并吸附到最近的预设点位\n"
        "\n"
        "  -chapters <string>\n"
        "    指定添加的章节文件\n"
        "    支持与 '-o' 相同的迭代语法\n"
        "\n"
        "  -custom / -custom:format / -custom:template <string>\n"
        "    当 -preset custom 时，将运行这个选项\n"
        "    字符串转义: \\34/ -> \", \\39/ -> ', '' -> \"\n"
        '    e.g. -custom:format \'-i "{input}" -map {testmap123} "{output}" \' -custom:suffix mp4 -testmap123 0:v:0\n'
        "\n"
        "  -custom:suffix <string>\n"
        "    当 -preset custom 时，这个选项将作为输出文件的后缀\n"
        "    默认: ''\n"
        "\n"
        "  -run [<string>]\n"
        "    执行 ripper list 中的 ripper\n"
        "\n"
        "    默认:\n"
        "      仅执行\n"
        "\n"
        "    exit:\n"
        "      执行后退出程序\n"
        "\n"
        "    shutdown [<秒数>]:\n"
        "      执行后关机\n"
        "      默认: 60\n"
        "\n"
        "\n"
        "Codec options:\n"
        "\n"
        "    -ff-params / -ff-params:ff <string>\n"
        "      设置 FFmpeg 的全局选项\n"
        "      等同于 ffmpeg <option> ... -i ...\n"
        "\n"
        "    -ff-params:in <string>\n"
        "      设置 FFmpeg 的输入选项\n"
        "      等同于 ffmpeg ... <option> -i ...\n"
        "\n"
        "    -ff-params:out <string>\n"
        "      设置 FFmpeg 的输出选项\n"
        "      等同于 ffmpeg -i ... <option> ...\n"
        "\n"
        "    -hwaccel <string>\n"
        "      使用 FFmpeg 的硬件加速 (详见 'ffmpeg -hwaccels')\n"
        "\n"
        "    -ss <time>\n"
        "      设置输入给 FFmpeg 的文件的开始时间\n"
        "      等同于 ffmpeg -ss <time> -i ...\n"
        "\n"
        "    -t <time>\n"
        "      设置 FFmpeg 输出的文件的持续时间\n"
        "      等同于 ffmpeg -i ... -t <time> ...\n"
    ),
    "Check env...": "检测环境中...",
    "{} not found, download it: {}": "没找到 {}，在此下载: {}",
    "flac ver ({}) must >= 1.5.0": "flac 版本 ({}) 必须 >= 1.5.0",
    # "The MediaInfo must be CLI ver": "MediaInfo 必须是 CLI 版本",
    Global_lang_val.Extra_text_index.NEW_VER_TIP: "检测到 {} 有新版本 {}。可在此下载: {}",
    "Easy Rip command": "Easy Rip 命令",
    "Stop run ripper": "ripper 执行终止",
    "There are {} {} during run": "执行期间有 {} 个 {}",
    "Execute shutdown in {}s": "{}s 后执行关机",
    "{} run completed, shutdown in {}s": "{} 执行完成，{}s 后关机",
    "Run completed": "执行完成",
    "Your input command has error:\n{}": "输入的命令报错:\n{}",
    "Delete the {}th ripper success": "成功删除第 {} 个 ripper",
    "Will shutdown in {}s after run finished": "将在执行结束后的{}秒后关机",
    "Can not start multiple services": "禁止重复启用服务",
    "Disable the use of 'fd' on the web": "禁止在 web 使用 'fd'",
    'Illegal char in -o "{}"': '-o "{}" 中有非法字符',
    'The directory "{}" did not exist and was created': '目录 "{}" 不存在，自动创建',
    "Missing '-preset' option, set to default value 'custom'": "缺少 '-preset' 选项，自动设为默认值 'custom'",
    "Input file number == 0": "输入的文件数量为 0",
    'The file "{}" does not exist': '文件 "{}" 不存在',
    "No subtitle file exist as -sub auto when -i {} -o:dir {}": "-sub auto 没有在 -i {} -o:dir {} 中找到对应字幕文件",
    "Unsupported option: {}": "不支持的选项: {}",
    "Manually force exit": "手动强制退出",
    "or run '{}' when you use pip": "或运行 '{}' 以使用 pip 更新",
    "Wrong sec in -shutdown, change to default 60s": "-shutdown 设定的秒数错误，改为默认值 60s",
    "Current work directory has an other Easy Rip is running: {}": "当前工作目录存在其他 Easy Rip 正在运行: {}",
    "Stop run command": "命令执行终止",
    # log
    "encoding_log.html": "编码日志.html",
    "Start": "开始",
    "Input file pathname": "输入文件路径名",
    "Output directory": "输出目录",
    "Temporary file name": "临时文件名",
    "Output file name": "输出文件名",
    "Encoding speed": "编码速率",
    "File size": "文件体积",
    "Time consuming": "耗时",
    "End": "结束",
    # ripper.py
    "Failed to add ripper: {}": "添加 ripper 失败: {}",
    "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}": "'{}' 不存在于 '{}'，已设为默认值 '{}'。有以下值可用: {}",
    "The preset custom must have custom:format or custom:template": "custom 预设必须要有 custom:format 或 custom:template",
    "There have error in running": "执行时出错",
    "FFmpeg report: {}": "FFmpeg 报告: {}",
    "{} not found. Skip it": "没找到 {}。默认跳过",
    'The font "{}" does not contain these characters: {}': '字体 "{}" 不包含字符: {}',
    # web
    "Starting HTTP service on port {}...": "在端口 {} 启动 HTTP 服务...",
    "HTTP service stopped by ^C": "HTTP 服务被 ^C 停止",
    "There is a running command, terminate this request": "存在正在运行的命令，终止此次请求",
    "Prohibited from use $ <code> in web service when no password": "禁止在未设定密码的 Web 服务中使用 $ <code>",
    # config
    "The config version is not match, use '{}' to regenerate config file": "配置文件版本不匹配，使用 '{}' 重新生成配置文件",
    "Regenerate config file": "重新生成 config 文件",
    "Config file is not found": "配置文件不存在",
    "Config data is not found": "配置文件数据不存在",
    "User profile is not found, regenerate config": "用户配置文件不存在，重新生成配置",
    "User profile is not a valid dictionary": "用户配置文件不是有效的字典",
    "User profile is not found": "用户配置文件不存在",
    "Key '{}' is not found in user profile": "用户配置文件中不存在 {}",
    # config about
    "Easy Rip's language, support: {}": "Easy Rip 的语言，支持: {}",
    "Auto check the update of Easy Rip": "自动检测 Easy Rip 更新",
    "Auto check the versions of all dependent programs": "自动检测所有依赖的程序的版本",
    "Program startup directory, when the value is empty, starts in the working directory": "程序启动目录，值为空时在工作目录启动",
    "Force change of log file path, when the value is empty, it is the working directory": "强制更改日志文件所在路径，值为空时为工作目录",
    "Do not write to log file": "不写入日志文件",
    "Logs this level and above will be printed, and if the value is 'none', they will not be printed, support: {}": "此等级及以上的日志会打印到控制台，若值为 'none' 则不打印，支持: {}",
    "Logs this level and above will be written, and if the value is 'none', they will not be written, support: {}": "此等级及以上的日志会写入日志文件，若值为 'none' 则不写入，支持: {}",
    # 通用
    "Run {} failed": "执行 {} 失败",
}

from global_val import GlobalVal
from . import global_lang_val

lang_map: dict[str | global_lang_val.GlobalLangVal.ExtraTextIndex, str] = {
    global_lang_val.GlobalLangVal.ExtraTextIndex.HELP_DOC: (
        f"{GlobalVal.PROJECT_NAME}\n版本: {GlobalVal.PROJECT_VERSION}\n{GlobalVal.PROJECT_URL}\n"
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
        "      info, warning | warn, error | err\n"
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
        "  <Option>\n"
        "    -i <输入> -o <输出> [-o:dir <目录>] -preset <预设名> [-pipe <vpy 路径名> -crf <值> -psy-rd <值> ...] [-sub <字幕文件路径名>] [-c:a <音频编码器> -b:a <音频码率>] [-muxer <复用器> [-r <帧率>]] [-run [<run 选项>]]\n"
        "      往 ripper list 中添加一个 ripper，你可以单独设置预设中每个选项的值，使用 -run 执行 ripper\n"
        "\n"
        "\n"
        "Easy Rip options:\n"
        "\n"
        "  -i <string[::string...] | 'fd'>\n"
        "    输入文件的路径名或输入'fd'以使用文件对话框\n"
        "\n"
        "  -o <string>\n"
        "    输出文件的文件名前缀\n"
        "    多个输入时允许有迭代器和时间格式化:\n"
        '      e.g. "name--?{start=6,padding=4,increment=2}--?{time:%Y.%m.%S}"\n'
        "\n"
        "  -o:dir <string>\n"
        "    输出文件的目标目录\n"
        "\n"
        "  -preset <string>\n"
        "    设置预设\n"
        "\n"
        "    预设名:\n"
        "      custom\n"
        "      flac\n"
        "      x264slow\n"
        "      x265fast2 x265fast x265slow x265full\n"
        "\n"
        "  -pipe <string>\n"
        "    选择一个 vpy 文件作为管道的输入，这个 vpy 必须有 input 全局变量\n"
        "    演示如何 input: vspipe -a input=<input> filter.vpy\n"
        "\n"
        "  -vf <string>\n"
        "    自定义 FFmpeg 的 -vf\n"
        "    与 -sub 同时使用为未定义行为\n"
        "\n"
        "  -sub <string | 'auto'>\n"
        "    它使用 libass 制作硬字幕，需要硬字幕时请输入字幕路径名\n"
        '    使用"::"以输入多个字幕，例如: 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n'
        "    如果使用'auto'，相同前缀的字幕文件将作为输入\n"
        "\n"
        "  -c:a <string>\n"
        "    设置音频编码器\n"
        "\n"
        "    音频编码器:\n"
        "      copy\n"
        "      libopus\n"
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
        "  -custom:format / -custom:template <string>\n"
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
    global_lang_val.GlobalLangVal.ExtraTextIndex.NEW_VER_TIP: "检测到 {} 有新版本 {}。可在此下载: {}",
    "Easy Rip command": "Easy Rip 命令",
    "Stop run ripper": "ripper 执行终止",
    "Execute shutdown in {}s": "{}s 后执行关机",
    "{} run completed, shutdown in {}s": "{} 执行完成，{}s 后关机",
    "Run completed": "执行完成",
    "Your input command has error:\n{}": "输入的命令报错:\n{}",
    "Delete the {}th ripper success": "成功删除第 {} 个 ripper",
    "Will shutdown in {}s after run finished": "将在执行结束后的{}秒后关机",
    "Can not start multiple services": "禁止重复启用服务",
    "Disable the use of 'fd' on the web": "禁止在 web 使用 'fd'",
    'Illegal char in -o "{}"': '-o "{}" 中有非法字符',
    'The directory "{}" does not exist': '目录 "{}" 不存在',
    "Missing '-preset' option, set to default value 'custom'": "缺少 '-preset' 选项，自动设为默认值 'custom'",
    "Input file number == 0": "输入的文件数量为 0",
    'The file "{}" does not exist': '文件 "{}" 不存在',
    "No subtitle file exist as -sub auto when -i {} -o:dir {}": "-sub auto 没有在 -i {} -o:dir {} 中找到对应字幕文件",
    "Unsupported option: {}": "不支持的选项: {}",
    "Manually force exit": "手动强制退出",
    "Wrong sec in -shutdown, change to default 60s": "-shutdown 设定的秒数错误，改为默认值 60s",
    "Stop run command": "命令执行终止",
    # log
    "encoding_log.html": "编码日志.html",
    # ripper.py
    "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}": "'{}' 不存在于 '{}'，已设为默认值 '{}'。有以下值可用: {}",
    "The preset custom must have custom:format or custom:template": "custom 预设必须要有 custom:format 或 custom:template",
    "There have error in running": "执行时出错",
    "FFmpeg report: {}": "FFmpeg report: {}",
    # web
    "Starting HTTP service on port {}...": "在端口 {} 启动 HTTP 服务...",
    "There is a running command, terminate this request": "存在正在运行的命令，终止此次请求",
    "Prohibited from use $ <code> in web service when no password": "禁止在未设定密码的 Web 服务中使用 $ <code>",
}

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
        "  h / help [exit]\n"
        "    打印 help\n"
        "\n"
        "  v / version [exit]\n"
        "    打印版本\n"
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
        "  cls / clear\n"
        "    清屏\n"
        "\n"
        "  list <list option>\n"
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
        "  run [<run option>]\n"
        "    执行 ripper list 中的 ripper\n"
        "\n"
        "    默认:\n"
        "      仅执行\n"
        "\n"
        "    exit:\n"
        "      执行后退出程序\n"
        "\n"
        "    server [<address> [<port> [<password>]]]:\n"
        "      启动 web 服务\n"
        '      默认: server "" 0\n'
        "\n"
        "  <Option>\n"
        "    -i <input> -o <output> -preset <preset name> [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-c:a <audio codec> -b:a <audio bitrate>] [-muxer <muxer> [-r <fps>]] [-run [<run option>]]\n"
        "      往 ripper list 中添加一个 ripper，你可以单独设置预设中每个选项的值，使用 -run 执行 ripper\n"
        "\n"
        "\n"
        "Easy Rip options:\n"
        "\n"
        "  -i <string | 'fd'>\n"
        "    输入文件的路径名或输入'fd'以使用文件对话框\n"
        "\n"
        "  -o <string>\n"
        "    输出文件的文件名前缀\n"
        "\n"
        "  -preset <string>\n"
        "    设置预设\n"
        "\n"
        "    Preset name:\n"
        "      custom\n"
        "      flac\n"
        "      x264slow\n"
        "      x265fast2 x265fast x265slow x265full\n"
        "\n"
        "  -pipe <string>\n"
        "    选择一个 vpy 文件作为管道的输入，这个 vpy 必须有 input\n"
        "    演示如何 input: vspipe -a input=<input> filter.vpy\n"
        "\n"
        "  -sub <string | 'auto'>\n"
        "    它使用 libass 制作硬字幕，需要硬字幕时请输入字幕路径名\n"
        '    使用"::"以输入多个字幕，例如: 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n'
        "    如果使用'auto'，相同前缀的字幕文件将作为输入\n"
        "\n"
        "  -c:a <string>\n"
        "    设置音频编码器\n"
        "\n"
        "    Audio encoder:\n"
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
        "  -r / -fps <string>\n"
        "    设置封装的帧率\n"
        "\n"
        "  -custom:format / -custom:template <string>\n"
        "    当 -preset custom 时，将运行这个选项\n"
        "    字符串转义: \\34/ -> \", \\39/ -> '\n"
        "\n"
        "  -custom:suffix <string>\n"
        "    当 -preset custom 时，这个选项将作为输出文件的后缀\n"
        "    默认: mkv\n"
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
        "\n"
        "Codec options:\n"
        "\n"
        "    -hwaccel <string>\n"
        "      使用 FFmpeg 的硬件加速 (详见 'ffmpeg -hwaccels')\n"
        "\n"
        "    -deinterlacing <bool 0..1>\n"
        "      使用 yadif 滤镜反交错\n"
    ),
    global_lang_val.GlobalLangVal.ExtraTextIndex.NEW_VER_TIP: "检测到新版本 {}。你可以进入此链接下载 https://github.com/op200/EasyRip/releases",
    "Easy Rip command": "Easy Rip 命令",
    "Stop run ripper": "ripper 执行终止",
    "Run completed": "执行完成",
    "Your input command has error:\n{}": "输入的命令报错:\n{}",
    "Delete the {}th ripper success": "成功删除第 {} 个 ripper",
    "Can not start multiple services": "禁止重复启用服务",
    'Illegal char in -o "{}"': '-o "{}" 中有非法字符',
    'The directory "{}" does not exist': '目录 "{}" 不存在',
    "Missing -preset": "缺少 -preset",
    "Input file number == 0": "输入的文件数量为 0",
    'The file "{}" does not exist': '文件 "{}" 不存在',
    "No subtitle file exist as -sub auto when -i {} -o:dir {}": "-sub auto 没有在 -i {} -o:dir {} 中找到对应字幕文件",
    "Unsupported option: {}": "不支持的选项: {}",
    "Manually force exit": "手动强制退出",
    "Stop run command": "命令执行终止",
    # log
    "encoding_log.html": "编码日志.html",
    # ripper.py
    "The preset custom must have custom:format or custom:template": "custom 预设必须要有 custom:format 或 custom:template",
    "There have error in running": "执行时出错",
    "FFmpeg report: {}": "FFmpeg report: {}",
    # web
    "Starting HTTP server on port {}...": "在端口 {} 启动 HTTP 服务器...",
}

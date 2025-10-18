from ..easyrip_command import Cmd_type, Opt_type
from .global_lang_val import (
    Lang_tag,
    Lang_tag_language,
    Lang_tag_region,
    Lang_tag_script,
)

LANG_TAG = Lang_tag(
    language=Lang_tag_language.zh,
    script=Lang_tag_script.Hans,
    region=Lang_tag_region.CN,
)

LANG_MAP: dict[str, str] = {
    # doc
    "Version": "版本",
    "Help": "帮助",
    "You can input command or use command-line arguments to run.": "输入命令或使用命令行传参以运行。",
    "Commands": "命令",
    "Ripper options": "Ripper 选项",
    Cmd_type.help.value.description: "展示全部帮助文档或展示 <cmd> 的帮助文档",
    Cmd_type.version.value.description: "展示版本信息",
    Cmd_type.init.value.description: (
        "执行初始化函数\n"  # .
        "例如你可以在修改动态翻译文件后执行它"
    ),
    Cmd_type.log.value.opt_str: "log [<日志级别>] <string>",
    Cmd_type.log.value.description: (
        "输出自定义日志\n"
        "日志级别:\n"
        "  info\n"
        "  warning | warn\n"
        "  error | err\n"
        "  send\n"
        "  debug\n"
        "  默认: info"
    ),
    Cmd_type._run_any.value.description: (
        "直接从内部环境运行代码\n"  # .
        "直接执行 $ 之后的代码\n"
        '字符串"\\N"将变为实际的"\\n"'
    ),
    Cmd_type.exit.value.description: "退出程序",
    Cmd_type.cd.value.description: "更改当前目录",
    Cmd_type.dir.value.description: "打印当前目录的所有文件和文件夹的名字",
    Cmd_type.mkdir.value.description: "新建文件目录",
    Cmd_type.cls.value.description: "清屏",
    Cmd_type.list.value.opt_str: "list <list 选项>",
    Cmd_type.list.value.description: (
        "操作 Ripper list\n"
        " \n"
        "默认:\n"
        "  打印 Ripper list\n"
        " \n"
        "clear / clean:\n"
        "  清空 Ripper list\n"
        " \n"
        "del / pop <index>:\n"
        "  删除 Ripper list 中指定的一个 Ripper\n"
        " \n"
        "sort [n][r]:\n"
        "  排序 list\n"
        "  'n': 自然排序\n"
        "  'r': 倒序\n"
        " \n"
        "<int> <int>:\n"
        "  交换指定索引"
    ),
    Cmd_type.run.value.opt_str: "run <run 选项>",
    Cmd_type.run.value.description: (
        "执行 Ripper list 中的 Ripper\n"
        " \n"
        "默认:\n"
        "  仅执行\n"
        " \n"
        "exit:\n"
        "  执行后退出程序\n"
        " \n"
        "shutdown [<秒数>]:\n"
        "  执行后关机\n"
        "  默认: 60"
    ),
    Cmd_type.server.value.opt_str: "server [[-a | -address] <地址>[:<端口>] [[-p | -password] <密码>]]",
    Cmd_type.server.value.description: (
        "启动 web 服务\n"
        "默认: server localhost:0\n"
        "客户端发送命令 'kill' 可以退出 Ripper 的运行，注意，FFmpeg需要接受多次^C信号才能强制终止，单次^C会等待文件输出完才会终止"
    ),
    Cmd_type.config.value.opt_str: "config <config 选项>",
    Cmd_type.config.value.description: (
        "regenerate | clear | clean | reset\n"
        "  重新生成 config 文件\n"
        "open\n"
        "  打开 config 文件所在目录\n"
        "list\n"
        "  展示所有 config 可调选项\n"
        "set <key> <val>\n"
        "  设置 config\n"
        "  例如 config set language en"
    ),
    Cmd_type.translate.value.opt_str: "translate <中缀> <目标语言标签> [-overwrite]",
    Cmd_type.translate.value.description: (
        "翻译字幕文件\n"
        "例如 'translate zh-Hans zh-Hant' 将翻译所有 '*.zh-Hans.ass' 文件为 zh-Hant"
    ),
    Cmd_type.Option.value.description: (
        "-i <输入> -p <预设名> [-o <输出>] [-o:dir <目录>] [-pipe <vpy 路径名> -crf <值> -psy-rd <值> ...] [-sub <字幕文件路径名>] [-c:a <音频编码器> -b:a <音频码率>] [-muxer <复用器> [-r <帧率>]] [-run [<run 选项>]] [...]\n"
        " \n"
        "往 Ripper list 中添加一个 Ripper，你可以单独设置预设中每个选项的值，使用 -run 执行 Ripper"
    ),
    Opt_type._i.value.description: (
        "输入文件的路径名或输入 'fd' 以使用文件对话框，'cfd' 从当前目录打开\n"
        "部分情况下允许使用 '?' 作为间隔符往一个 Ripper 中输入多个，例如 '-preset subset' 允许输入多个 ASS"
    ),
    Opt_type._o_dir.value.description: "输出文件的目标目录",
    Opt_type._o.value.description: (
        "输出文件的文件名前缀\n"
        "多个输入时允许有迭代器和时间格式化\n"
        '  e.g. "name--?{start=6,padding=4,increment=2}--?{time:%Y.%m.%S}"'
    ),
    Opt_type._auto_infix.value.description: (
        "如果启用，输出的文件将添加自动中缀:\n"  # .
        "  无音轨: '.v'\n"
        "  有音轨: '.va'\n"
        "默认: 1"
    ),
    Opt_type._preset.value.description: (
        "设置预设\n"
        "预设名:\n"
        "  custom\n"
        "  subset\n"
        "  copy\n"
        "  flac\n"
        "  x264fast x264slow\n"
        "  x265fast4 x265fast3 x265fast2 x265fast x265slow x265full\n"
        "  h264_amf h264_nvenc h264_qsv\n"
        "  hevc_amf hevc_nvenc hevc_qsv\n"
        "  av1_amf av1_nvenc av1_qsv"
    ),
    Opt_type._pipe.value.description: (
        "选择一个 vpy 文件作为管道的输入，这个 vpy 必须有 input 全局变量\n"
        "演示如何 input: vspipe -a input=<input> filter.vpy"
    ),
    Opt_type._pipe_gvar.value.description: (
        "自定义传给 vspipe 的全局变量，多个则用':'间隔\n"
        '例如: -pipe:gvar "a=1 2 3:b=abc" -> vspipe -a "a=1 2 3" -a "b=abc"'
    ),
    Opt_type._vf.value.description: (
        "自定义 FFmpeg 的 -vf\n"  # .
        "与 -sub 同时使用为未定义行为"
    ),
    Opt_type._sub.value.description: (
        "它使用 libass 制作硬字幕，需要硬字幕时请输入字幕路径名\n"
        '使用 "::" 以输入多个字幕，例如: 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n'
        "如果使用'auto'，相同前缀的字幕文件将作为输入\n"
        "'auto:...'可以只选择指定中缀，例如'auto:zh-Hans:zh-Hant'"
    ),
    Opt_type._only_mux_sub_path.value.description: "该目录下所有的字幕和字体文件将加入混流",
    Opt_type._soft_sub.value.description: "往 MKV 中封装子集化字幕",
    Opt_type._subset_font_dir.value.description: (
        "子集化时使用的字体的目录\n"
        '默认: 优先当前目录，其次当前目录下含有 "font" 的文件夹 (不分大小写)'
    ),
    Opt_type._subset_font_in_sub.value.description: (
        "将字体编码到 ASS 文件中，而不是单独的字体文件\n"  # .
        "默认: 0"
    ),
    Opt_type._subset_use_win_font.value.description: (
        "无法从 subset-font-dir 找到字体时使用 Windows 字体\n"  # .
        "默认: 0"
    ),
    Opt_type._subset_use_libass_spec.value.description: (
        "子集化时使用 libass 规范\n"
        'e.g. "11\\{22}33" ->\n'
        '  "11\\33"   (VSFilter)\n'
        '  "11{22}33" (libass)\n'
        "默认: 0"
    ),
    Opt_type._subset_drop_non_render.value.description: (
        "丢弃 ASS 中的注释行、Name、Effect等非渲染内容\n"  # .
        "默认: 1"
    ),
    Opt_type._subset_drop_unkow_data.value.description: (
        "丢弃 ASS 中的非 {[Script Info], [V4+ Styles], [Events]} 行\n"  # .
        "默认: 1"
    ),
    Opt_type._subset_strict.value.description: (
        "子集化时报错则中断\n"  # .
        "默认: 0"
    ),
    Opt_type._translate_sub.value.opt_str: "-translate-sub <中缀>:<语言标签>",
    Opt_type._translate_sub.value.description: (
        "临时生成字幕的翻译文件\n"  # .
        "例如 'zh-Hans:zh-Hant' 将临时生成繁体字幕"
    ),
    Opt_type._c_a.value.description: (
        "设置音频编码器\n"
        " \n"  # .
        "音频编码器:\n"
        "  copy\n"
        "  libopus\n"
        "  flac"
    ),
    Opt_type._b_a.value.description: "设置音频码率。默认值 '160k'",
    Opt_type._muxer.value.description: (
        "设置复用器\n"
        " \n"  # .
        "可用的复用器:\n"
        "  mp4\n"
        "  mkv"
    ),
    Opt_type._r.value.description: (
        "设置封装的帧率\n"  # .
        "使用 auto 时，自动从输入的视频获取帧率，并吸附到最近的预设点位"
    ),
    Opt_type._r.value.description: (
        "指定添加的章节文件\n"  # .
        "支持与 '-o' 相同的迭代语法"
    ),
    Opt_type._custom_template.value.description: (
        "当 -preset custom 时，将运行这个选项\n"
        "字符串转义: \\34/ -> \", \\39/ -> ', '' -> \"\n"
        '例如 -custom:format \'-i "{input}" -map {testmap123} "{output}" \' -custom:suffix mp4 -testmap123 0:v:0'
    ),
    Opt_type._custom_suffix.value.description: (
        "当 -preset custom 时，这个选项将作为输出文件的后缀\n"  # .
        '默认: ""'
    ),
    Opt_type._run.value.description: (
        "执行 Ripper list 中的 Ripper\n"
        " \n"
        "默认:\n"
        "  仅执行\n"
        " \n"
        "exit:\n"
        "  执行后退出程序\n"
        " \n"
        "shutdown [<秒数>]:\n"
        "  执行后关机\n"
        "  默认: 60"
    ),
    Opt_type._ff_params_ff.value.description: (
        "设置 FFmpeg 的全局选项\n"  # .
        "等同于 ffmpeg <option> ... -i ..."
    ),
    Opt_type._ff_params_in.value.description: (
        "设置 FFmpeg 的输入选项\n"  # .
        "等同于 ffmpeg ... <option> -i ..."
    ),
    Opt_type._ff_params_out.value.description: (
        "设置 FFmpeg 的输出选项\n"  # .
        "等同于 ffmpeg -i ... <option> ..."
    ),
    Opt_type._hwaccel.value.description: "使用 FFmpeg 的硬件加速 (详见 'ffmpeg -hwaccels')",
    Opt_type._ss.value.description: (
        "设置输入给 FFmpeg 的文件的开始时间\n"  # .
        "等同于 ffmpeg -ss <time> -i ..."
    ),
    Opt_type._t.value.description: (
        "设置 FFmpeg 输出的文件的持续时间\n"  # .
        "等同于 ffmpeg -i ... -t <time> ..."
    ),
    # utils
    "{} has new version {}. You can download it: {}": "检测到 {} 有新版本 {}。可在此下载: {}",
    "{} not found, download it: {}": "没找到 {}，在此下载: {}",
    "flac ver ({}) must >= 1.5.0": "flac 版本 ({}) 必须 >= 1.5.0",
    # main
    "Check env...": "检测环境中...",
    # "The MediaInfo must be CLI ver": "MediaInfo 必须是 CLI 版本",
    "Easy Rip command": "Easy Rip 命令",
    "Stop run Ripper": "Ripper 执行终止",
    "There are {} {} during run": "执行期间有 {} 个 {}",
    "Execute shutdown in {}s": "{}s 后执行关机",
    "{} run completed, shutdown in {}s": "{} 执行完成，{}s 后关机",
    "Run completed": "执行完成",
    "Your input command has error:\n{}": "输入的命令报错:\n{}",
    "Delete the {}th Ripper success": "成功删除第 {} 个 Ripper",
    "Will shutdown in {}s after run finished": "将在执行结束后的{}秒后关机",
    "Can not start multiple services": "禁止重复启用服务",
    "Disable the use of '{}' on the web": "禁止在 web 使用 '{}'",
    'Illegal char in -o "{}"': '-o "{}" 中有非法字符',
    'The directory "{}" did not exist and was created': '目录 "{}" 不存在，自动创建',
    "Missing '-preset' option, set to default value 'custom'": "缺少 '-preset' 选项，自动设为默认值 'custom'",
    "Input file number == 0": "输入的文件数量为 0",
    'The file "{}" does not exist': '文件 "{}" 不存在',
    "No subtitle file exist as -sub auto when -i {} -o:dir {}": "-sub auto 没有在 -i {} -o:dir {} 中找到对应字幕文件",
    "Unsupported option: {}": "不支持的选项: {}",
    "Unsupported param: {}": "不支持的参数: {}",
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
    "Failed to add Ripper: {}": "添加 Ripper 失败: {}",
    "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}": "'{}' 不存在于 '{}'，已设为默认值 '{}'。有以下值可用: {}",
    "The preset custom must have custom:format or custom:template": "custom 预设必须要有 custom:format 或 custom:template",
    "There have error in running": "执行时出错",
    "{} param illegal": "{} 参数非法",
    'The file "{}" already exists, skip translating it': '文件 "{}" 已存在，跳过翻译',
    "Subset faild, cancel mux": "子集化失败，取消混流",
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
    "Easy Rip's language, support incomplete matching. Support: {}": "Easy Rip 的语言，支持不完整匹配。支持: {}",
    "Auto check the update of Easy Rip": "自动检测 Easy Rip 更新",
    "Auto check the versions of all dependent programs": "自动检测所有依赖的程序的版本",
    "Program startup directory, when the value is empty, starts in the working directory": "程序启动目录，值为空时在工作目录启动",
    "Force change of log file path, when the value is empty, it is the working directory": "强制更改日志文件所在路径，值为空时为工作目录",
    "Do not write to log file": "不写入日志文件",
    "Logs this level and above will be printed, and if the value is '{}', they will not be printed. Support: {}": "此等级及以上的日志会打印到控制台，若值为 '{}' 则不打印。支持: {}",
    "Logs this level and above will be written, and if the value is '{}', the '{}' only be written when 'server', they will not be written. Support: {}": "此等级及以上的日志会写入日志文件，若值为 '{}' 则不写入，'{}' 仅在 'server' 时写入。支持: {}",
    # 第三方 API
    "Translating into '{target_lang}' using '{api_name}'": "正在使用 '{api_name}' 翻译为 '{target_lang}'",
    # mlang
    "Unsupported language tag: {}": "不支持的语言标签: {}",
    'Start translating file "{}"': '开始翻译文件 "{}"',
    "Successfully translated: {}": "翻译完成: {}",
    "{num} file{s} in total": "总共 {num} 个文件",
    # 通用
    "Run {} failed": "执行 {} 失败",
    "Unknown error": "未知错误",
}

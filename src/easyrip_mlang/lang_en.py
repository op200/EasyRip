from global_val import GlobalVal
from . import global_lang_val

lang_map: dict[str | global_lang_val.GlobalLangVal.ExtraTextIndex, str] = {
    global_lang_val.GlobalLangVal.ExtraTextIndex.HELP_DOC: (
        f"{GlobalVal.PROJECT_NAME}\nVersion: {GlobalVal.PROJECT_VERSION}\n{GlobalVal.PROJECT_URL}\n"
        "\n"
        "\n"
        "Help:\n"
        "  You can input command or use command-line arguments to run.\n"
        "\n"
        "\n"
        "Commands:\n"
        "\n"
        "  h / help [exit]\n"
        "    Show help\n"
        "\n"
        "  v / ver / version [exit]\n"
        "    Show version info\n"
        "\n"
        "  log [<log level>] <message>\n"
        "    Output custom log\n"
        "    log level:\n"
        "      info, warning | warn, error | err\n"
        "      Default: info\n"
        "\n"
        "  $ <code>\n"
        "    Run code directly from the internal environment\n"
        "    Execute the code string directly after the $\n"
        '    The string "\\N" will be changed to real "\\n"\n'
        "\n"
        "  exit\n"
        "    Exit this program\n"
        "\n"
        "  cd <string>\n"
        "    Change current working directory\n"
        "\n"
        "  dir\n"
        "    Print files and folders' name in the current working directory\n"
        "\n"
        "  mkdir / makedir <string>\n"
        "    Create a new path\n"
        "\n"
        "  cls / clear\n"
        "    Clear screen\n"
        "\n"
        "  list <list option>\n"
        "    Operate ripper list\n"
        "\n"
        "    Default:\n"
        "      Show ripper list\n"
        "\n"
        "    clear / clean:\n"
        "      Clear ripper list\n"
        "\n"
        "    del / pop <index>:\n"
        "      Delete a ripper from ripper list\n"
        "\n"
        "  run [<run option>]\n"
        "    Run the ripper in the ripper list\n"
        "\n"
        "    Default:\n"
        "      Only run\n"
        "\n"
        "    exit:\n"
        "      Close program when runned\n"
        "\n"
        "    shutdown [<sec>]:\n"
        "      Shutdown when runned\n"
        "      Default: 60\n"
        "\n"
        "    server [<address> [<port> [<password>]]]:\n"
        "      Boot web service\n"
        '      Default: server "" 0\n'
        "      Client send command 'kill' can exit ripper's run, note that FFmpeg needs to accept multiple ^C signals to forcibly terminate, and a single ^C signal will wait for the file output to be complete before terminating\n"
        "\n"
        "  <Option>\n"
        "    -i <input> -o <output> [-o:dir <dir>] -preset <preset name> [-pipe <vpy pathname> -crf <val> -psy-rd <val> ...] [-sub <subtitle pathname>] [-c:a <audio encoder> -b:a <audio bitrate>] [-muxer <muxer> [-r <fps>]] [-run [<run option>]]\n"
        "      Add a new ripper to the ripper list, you can set the values of the options in preset individually, you can run ripper list when use -run\n"
        "\n"
        "\n"
        "Easy Rip options:\n"
        "\n"
        "  -i <string | 'fd'>\n"
        "    Input file's pathname or use file dialog\n"
        "\n"
        "  -o <string>\n"
        "    Output file basename's prefix\n"
        "\n"
        "  -o:dir <string>\n"
        "    Destination directory of the output file\n"
        "\n"
        "  -preset <string>\n"
        "    Setting preset\n"
        "\n"
        "    Preset name:\n"
        "      custom\n"
        "      flac\n"
        "      x264slow\n"
        "      x265fast2 x265fast x265slow x265full\n"
        "\n"
        "  -pipe <string>\n"
        "    Select a vpy file as pipe to input, this vpy must have input global val\n"
        "    The input in vspipe: vspipe -a input=<input> filter.vpy\n"
        "\n"
        "  -sub <string | 'auto'>\n"
        "    It use libass to make hard subtitle, input a subtitle pathname when you need hard subtitle\n"
        '    It can add multiple subtitles by "::", e.g. 01.zh-Hans.ass::01.zh-Hant.ass::01.en.ass\n'
        "    If use 'auto', the subtitle files with the same prefix will be used\n"
        "\n"
        "  -c:a <string>\n"
        "    Setting audio encoder\n"
        "\n"
        "    Audio encoder:\n"
        "      copy\n"
        "      libopus\n"
        "\n"
        "  -b:a <string>\n"
        "    Setting audio bitrate. Default '160k'\n"
        "\n"
        "  -muxer <string>\n"
        "    Setting muxer\n"
        "\n"
        "    Muxer:\n"
        "      mp4\n"
        "      mkv\n"
        "\n"
        "  -r / -fps <string>\n"
        "    Setting FPS when muxing\n"
        "\n"
        "  -custom:format / -custom:template <string>\n"
        "    When -preset custom, this option will run\n"
        "    String escape: \\34/ -> \", \\39/ -> '\n"
        "\n"
        "  -custom:suffix <string>\n"
        "    When -preset custom, this option will be used as a suffix for the output file\n"
        "    Default: mkv\n"
        "\n"
        "  -run [<string>]\n"
        "    Run the ripper in the ripper list\n"
        "\n"
        "    Default:\n"
        "      Only run\n"
        "\n"
        "    exit:\n"
        "      Close program when runned\n"
        "\n"
        "    shutdown [<sec>]:\n"
        "      Shutdown when runned\n"
        "      Default: 60\n"
        "\n"
        "\n"
        "Codec options:\n"
        "\n"
        "    -hwaccel <string>\n"
        "      Use FFmpeg hwaccel (See 'ffmpeg -hwaccels' for details)\n"
        "\n"
        "    -deinterlacing <bool 0..1>\n"
        "      Use the filter yadif to deinterlacing\n"
    ),
    global_lang_val.GlobalLangVal.ExtraTextIndex.NEW_VER_TIP: f"New version {{}} detected. You can download it in {GlobalVal.PROJECT_RELEASE_URL}",
}

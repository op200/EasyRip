# Easy Rip

Self-use tools  
自用压制工具

### Get file

Download exe in [Actions](https://github.com/op200/EasyRip/actions)  
在 [Actions](https://github.com/op200/EasyRip/actions) 中下载最新的 exe

Or download exe or bat script collection in [Releases](https://github.com/op200/EasyRip/releases)  
或者在 [Releases](https://github.com/op200/EasyRip/releases) 中下载 exe 或 bat脚本包

### Use

运行 `easyrip`，键入 `help` 获取帮助文档  
Run `easyrip`, input `help` to get help doc

[Wiki](https://github.com/op200/EasyRip/wiki)

### Dependency

Python
```
pip install -U loguru
```

CLI
```
ffmpeg.exe
flac.exe
mp4box.exe
mp4fpsmod.exe
mkvpropedit.exe
mkvmerge.exe
```

### TODO

预计后续可能加入的功能

* Web 端控制面板
* 弃用 loguru 库
* 自动捕获 ffmpeg 解码器输出的异常
* 更好用的 CLI 语法（重写命令拼接部分）
* 多语言

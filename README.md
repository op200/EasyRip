# Easy Rip

Self-use codec tool  
自用压制工具

**[Easy Rip Web Panel  
Easy Rip 网页版控制台](https://op200.github.io/EasyRip-WebPanel/)**

### Get file

* If you have Python environment
  如果你有 Python 环境

  *
  1. You can `pip install -U https://github.com/op200/EasyRip.git` to pull the version from the repositoryand, or `pip install -U easyrip` to obtain the stable version.
  2. After installation, run `easyrip` on command.

  *
  1. 你可以 `pip install -U https://github.com/op200/EasyRip.git` 获取仓库中的版本，或者 `pip install -U easyrip` 获取稳定版。
  2. 安装后直接在命令行运行 `easyrip`。


* If you want to download a standalone exe file
  如果你想下载一个独立的可执行文件

  *
    Download exe in [Actions](https://github.com/op200/EasyRip/actions).
    Or download exe or bat script collection in [Releases](https://github.com/op200/EasyRip/releases).

    在 [Actions](https://github.com/op200/EasyRip/actions) 中下载最新的 exe。
    或者在 [Releases](https://github.com/op200/EasyRip/releases) 中下载 exe 或 bat 脚本包。

  * 
    The file `BatchScriptPackage` in [Releases](https://github.com/op200/EasyRip/releases) is a bat script collection. 
    It is used to facilitate ordinary users, it only has Chinese.

    [Releases](https://github.com/op200/EasyRip/releases) 中每隔一段时间发布一次名为 BatchScriptPackage 的 bat 脚本包  
    用于方便一般用户，其内只有中文



### Use


Run `easyrip`, input `help` to get help doc
运行 `easyrip`，键入 `help` 获取帮助文档

[View usage in wiki  
在 Wiki 中查看用法](https://github.com/op200/EasyRip/wiki)

### Dependency

* Python 3.13 (must >=3.11)
  ```pwsh
  pip install -U pycryptodome
  ```

* CLI
  * [ffmpeg & ffprobe](https://ffmpeg.org/)
  * [flac](https://xiph.org/flac/)
  * [mp4box](https://gpac.io/)
  * [mp4fpsmod](https://github.com/nu774/mp4fpsmod)
  * [mkvpropedit & mkvmerge](https://mkvtoolnix.download/)
  <!-- * [MediaInfo](https://mediaarea.net/en/MediaInfo) -->

### Supported languages
* en
* zh-Hans-CN

If you want to add or modify translation, edit the `easyrip/easyrip_mlang`
# Easy Rip

Self-use codec tool  
自用压制工具

**[Easy Rip Web Panel  
Easy Rip 网页版控制台](https://op200.github.io/EasyRip-WebPanel/)**

## Start

1. Install [Python](https://www.python.org/)  
  安装 [Python](https://www.python.org/)
2. Install Easy Rip using pip: `pip install -U easyrip`  
  使用 pip 安装 Easy Rip: `pip install -U easyrip`
3. The you can use Easy Rip directly, run the command `easyrip`  
  然后你就可以直接 Easy Rip 了，运行命令 `easyrip`

* (If you have special requirements and want to use a separate file, you can download it from [Github Actions](https://github.com/op200/EasyRip/actions))  
  (如果你有特殊需求，想使用独立文件，可以在 [Github Actions](https://github.com/op200/EasyRip/actions) 中下载)
* (The file `BatchScriptPackage` in [Releases](https://github.com/op200/EasyRip/releases) is a bat script collection. It is used to facilitate ordinary users, it only has Chinese.)  
  ([Releases](https://github.com/op200/EasyRip/releases) 中每隔一段时间发布一次名为 `BatchScriptPackage` 的 bat 脚本包，用于方便一般用户，其内只有中文。)

## Usage

Run `easyrip`, input `help` to get help doc  
运行 `easyrip`，键入 `help` 获取帮助文档

[View usage in wiki  
在 Wiki 中查看用法](https://github.com/op200/EasyRip/wiki)

## Dependency

* ### Python 3.14 (must >=3.12)

  If you want to develop, you need to install dependencies. If you just want to use them, you don't need to manually install dependencies.  
  如果你想开发，需要安装依赖，如果你只是想使用，不需要手动安装依赖。

  ```pwsh
  pip install -U prompt-toolkit fonttools pycryptodome
  ```

  * [prompt-toolkit](https://pypi.org/project/prompt-toolkit/)
  * [fonttools](https://pypi.org/project/fonttools/)
  * [pycryptodome](https://pypi.org/project/pycryptodome/)

* ### CLI

  Command line dependencies are necessary.  
  命令行依赖是必须的。

  * [ffmpeg & ffprobe](https://ffmpeg.org/)
  * [flac](https://xiph.org/flac/)
  * [mp4box](https://gpac.io/)
  * [mp4fpsmod](https://github.com/nu774/mp4fpsmod)
  * [mkvpropedit & mkvmerge](https://mkvtoolnix.download/)
  <!-- * [MediaInfo](https://mediaarea.net/en/MediaInfo) -->

## Supported languages

* en
* zh-Hans-CN

If you want to add or modify translation, edit the `easyrip/easyrip_mlang`

Or add translate file, see [Wiki](https://github.com/op200/EasyRip/wiki/Language-file) for details

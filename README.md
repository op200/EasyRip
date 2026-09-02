# Easy Rip

Self-use codec tool: param preset, auto mux, intelligent terminal...  
自用压制工具: 参数预设、自动封装、智能终端...

**[Easy Rip Web Panel (relatively outdated)  
Easy Rip 网页版控制台 (较为过时)](https://op200.github.io/EasyRip-WebPanel/)**

[![Star History Chart](https://api.star-history.com/chart?repos=op200/EasyRip&type=date&legend=top-left&sealed_token=mREINCr-gQ9RaM_m6OtSqvakGorAkEKgNKsLyI3RPjSYawB7oyPx489GA3zMeBAQkAo-5w0sgKmfEPSnsbdz0_7gAysuGtzFm2ef1o9AQgSZHS6aTCt8fg)](https://www.star-history.com/?repos=op200%2FEasyRip&type=date&legend=top-left)

## Start

1. Install [Python][python]  
   安装 [Python][python]
2. Install Easy Rip using pip: `pip install -U easyrip`  
   使用 pip 安装 Easy Rip: `pip install -U easyrip`
3. Then you can use Easy Rip directly, run the command `easyrip`  
   然后你就可以直接使用 Easy Rip 了，运行命令 `easyrip`

- _If you have special requirements and want to use a separate file, you can download it from [Releases][this.github.releases] or [Github Actions][this.github.actions]  
  如果你有特殊需求，想使用独立文件，可以在 [Releases][this.github.releases] 或 [Github Actions][this.github.actions] 中下载_

## Usage

Run `easyrip`, input `help` to get help doc  
运行 `easyrip`，键入 `help` 获取帮助文档

[View usage in wiki  
在 Wiki 中查看用法](https://github.com/op200/EasyRip/wiki)

## Development

- ### Python 3.15 (must >=3.13)

  ```pwsh
  pip install -e . --config-settings editable_mode=strict
  # or
  # (pip >= 26.2)
  pip install . --only-deps
  ```

  - [pyperclip](https://pypi.org/project/pyperclip/)
  - [prompt-toolkit](https://pypi.org/project/prompt-toolkit/)
  - [fonttools](https://pypi.org/project/fonttools/)
  - [pycryptodome](https://pypi.org/project/pycryptodome/)

- ### Check

  #### Install

  ```pwsh
  pip install -U ruff ty
  pnpm i -g pyright oxfmt tombi
  ```

  #### Run

  ```pwsh
  pyright
  py -m ty check
  py -m ruff check --fix
  py -m ruff format
  oxfmt
  tombi lint
  tombi format
  ```

- ### CLI

  - [ffmpeg & ffprobe](https://ffmpeg.org/)
  - [flac](https://xiph.org/flac/)
  - [mp4box](https://gpac.io/)
  - [mkvpropedit & mkvmerge](https://mkvtoolnix.download/)

## Supported languages

- en
- zh-Hans-CN

If you want to add or modify translation, edit the `easyrip/easyrip_mlang`

Or add translation file, see [Wiki/Language-file](https://github.com/op200/EasyRip/wiki/Language-file) for details

[python]: https://www.python.org
[this.github.actions]: https://github.com/op200/EasyRip/actions
[this.github.releases]: https://github.com/op200/EasyRip/releases

from pathlib import Path

from ..easyrip_web.third_party_api import zhconvert
from .global_lang_val import (
    Lang_tag,
    Lang_tag_language,
    Lang_tag_script,
    Lang_tag_region,
)


def translate_subtitles(
    directory: Path, infix: str, target_lang: str | Lang_tag
) -> list[tuple[Path, str]]:
    """
    #### 自动搜索符合中缀的字幕文件，翻译为目标语言
    Return: list[tuple[file, content]]
    """

    from ..easyrip_mlang import gettext
    from ..ripper.utils import read_text

    if isinstance(target_lang, str):
        target_lang_tag: Lang_tag = Lang_tag.from_str(target_lang)
    else:
        target_lang_tag = target_lang

    file_list = list[tuple[Path, str]]()
    for f in directory.iterdir():
        if f.suffix not in {".ass", ".ssa", ".srt"}:
            continue

        if len(_stems := f.stem.split(".")) < 1:
            continue
        if infix == _stems[-1]:
            file_list.append(
                (
                    f.with_name(
                        f"{'.'.join(f.stem.split('.')[:-1])}.{target_lang_tag}{f.suffix}"
                    ),
                    read_text(f),
                )
            )

    match Lang_tag.from_str(infix):
        case (
            Lang_tag(
                language=Lang_tag_language.zh,
                script=Lang_tag_script.Hans,
                region=_,
            )
            | Lang_tag(
                language=Lang_tag_language.zh,
                script=_,
                region=Lang_tag_region.CN,
            )
        ):
            # 简体 -> 繁体
            match target_lang_tag:
                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.HK,
                ):
                    file_list = [
                        (
                            f[0],
                            zhconvert.translate(org_text=f[1], target_lang="Hongkong"),
                        )
                        for f in file_list
                    ]

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.TW,
                ):
                    file_list = [
                        (
                            f[0],
                            zhconvert.translate(org_text=f[1], target_lang="Taiwan"),
                        )
                        for f in file_list
                    ]

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=Lang_tag_script.Hant,
                    region=_,
                ):
                    file_list = [
                        (
                            f[0],
                            zhconvert.translate(
                                org_text=f[1], target_lang="Traditional"
                            ),
                        )
                        for f in file_list
                    ]

                case _:
                    Exception(
                        gettext("Unsupported language tag: {}").format(target_lang_tag)
                    )

        case (
            Lang_tag(
                language=Lang_tag_language.zh,
                script=Lang_tag_script.Hant,
                region=_,
            )
            | Lang_tag(
                language=Lang_tag_language.zh,
                script=_,
                region=Lang_tag_region.HK | Lang_tag_region.TW,
            )
        ):
            # 繁体 -> 简体
            match target_lang_tag:
                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.CN,
                ):
                    file_list = [
                        (
                            f[0],
                            zhconvert.translate(org_text=f[1], target_lang="China"),
                        )
                        for f in file_list
                    ]

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=Lang_tag_script.Hans,
                    region=_,
                ):
                    file_list = [
                        (
                            f[0],
                            zhconvert.translate(
                                org_text=f[1], target_lang="Simplified"
                            ),
                        )
                        for f in file_list
                    ]

                case _:
                    Exception(
                        gettext("Unsupported language tag: {}").format(target_lang_tag)
                    )

        case _:
            Exception(gettext("Unsupported language tag: {}").format(infix))

    return file_list

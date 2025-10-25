from collections.abc import Iterable
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Final

from ..easyrip_web.third_party_api import zhconvert
from .global_lang_val import (
    Lang_tag,
    Lang_tag_language,
    Lang_tag_region,
    Lang_tag_script,
)


def translate_subtitles(
    directory: Path,
    infix: str,
    target_lang: str | Lang_tag,
    *,
    file_intersection_selector: Iterable[Path] | None = None,
    enable_multithreading: bool = True,
) -> list[tuple[Path, str]]:
    """
    自动搜索符合中缀的字幕文件，翻译为目标语言

    :param 文件交集选择器: 不为 None 时，与选择器有交集的 Path 才会选择

    :return: list[tuple[file, content]]
    """
    from ..easyrip_log import log
    from ..easyrip_mlang import gettext
    from ..utils import read_text

    if isinstance(target_lang, str):
        target_lang_tag: Lang_tag = Lang_tag.from_str(target_lang)
    else:
        target_lang_tag = target_lang

    if file_intersection_selector is not None:
        file_intersection_selector = set(file_intersection_selector)

    file_list: Final[list[tuple[Path, str]]] = []
    for f in directory.iterdir():
        if f.suffix not in {".ass", ".ssa", ".srt"} or (
            file_intersection_selector is not None
            and f not in file_intersection_selector
        ):
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

    zhconvert_target_lang: zhconvert.Target_lang
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
            # 简体 -> 繁体 or 非 CN 简体 CN 化
            match target_lang_tag:
                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.HK,
                ):
                    zhconvert_target_lang = zhconvert.Target_lang.HK

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.TW,
                ):
                    zhconvert_target_lang = zhconvert.Target_lang.TW

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=Lang_tag_script.Hant,
                    region=_,
                ):
                    zhconvert_target_lang = zhconvert.Target_lang.Hant

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=Lang_tag_script.Hant,
                    region=Lang_tag_region.CN,
                ):  # 特殊情况
                    raise Exception(
                        gettext("Unsupported language tag: {}", target_lang_tag)
                    )

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=_,
                    region=Lang_tag_region.CN,
                ):
                    zhconvert_target_lang = zhconvert.Target_lang.CN

                case _:
                    raise Exception(
                        gettext("Unsupported language tag: {}", target_lang_tag)
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
                    zhconvert_target_lang = zhconvert.Target_lang.CN

                case Lang_tag(
                    language=Lang_tag_language.zh,
                    script=Lang_tag_script.Hans,
                    region=_,
                ):
                    zhconvert_target_lang = zhconvert.Target_lang.Hans

                case _:
                    raise Exception(
                        gettext("Unsupported language tag: {}", target_lang_tag)
                    )

        case _:
            raise Exception(gettext("Unsupported language tag: {}", infix))

    res_file_list: Final[list[tuple[Path, str]]] = []
    res_file_dict: Final[dict[int, tuple[Path, str]]] = {}

    def _tr(index: int, path: Path, org_text: str) -> None:
        log.info('Start translating file "{}"', path)
        res_file_dict[index] = (
            path,
            zhconvert.translate(
                org_text=org_text,
                target_lang=zhconvert_target_lang,
            ),
        )
        log.info("Successfully translated: {}", path)

    threads: Final[list[Thread]] = []

    for i, f in enumerate(file_list):
        t = Thread(target=_tr, args=(i, f[0], f[1]), daemon=False)
        threads.append(t)
        t.start()
        if not enable_multithreading:
            t.join()
        else:
            sleep(0.1)

    for t in threads:
        t.join()

    assert len(res_file_dict) == len(file_list)

    for _, f in sorted(res_file_dict.items()):
        res_file_list.append(f)

    return res_file_list

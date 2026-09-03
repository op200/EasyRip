import itertools
import locale
from collections.abc import Hashable, Mapping

from . import lang_en, lang_zh_Hans_CN
from .global_lang_val import Global_lang_val, Lang_map, Lang_tag
from .lang_tag_val import Lang_tag_val
from .translator import translate_subtitles

__all__ = [
    "Global_lang_val",
    "Lang_tag",
    "Lang_tag_val",
    "Mlang_exception",
    "get_system_language",
    "gettext",
    "translate_subtitles",
]


all_supported_lang_map: dict[Lang_tag, Lang_map] = {
    lang_en.LANG_TAG: lang_en.LANG_MAP,
    lang_zh_Hans_CN.LANG_TAG: lang_zh_Hans_CN.LANG_MAP,
}


def get_system_language() -> Lang_tag:
    return (
        Lang_tag()
        if (sys_lang := locale.getdefaultlocale()[0]) is None
        else Lang_tag.from_str(sys_lang.replace("_", "-"))
    )


def gettext(
    input_val: str | tuple[str, Hashable] | Mapping[Lang_tag | str, str],
    *fmt_args: object,
    is_format: bool = True,
    lang_tag: Lang_tag | None = None,
    **fmt_kwargs: object,
) -> str:
    def_lang_tag = (
        lang_tag
        or Global_lang_val.gettext_target_lang.match(all_supported_lang_map)
        or lang_en.LANG_TAG
    )

    if isinstance(input_val, Mapping):
        try:
            new_text = {
                (k if isinstance(k, Lang_tag) else Lang_tag.from_str(k)): v
                for k, v in input_val.items()
            }.get(def_lang_tag, next(iter(input_val.values())))
        except StopIteration:
            from ..easyrip_log import log

            log.error(
                f"The input `{input_val}` of function `{gettext.__name__}` is empty",
                deep=True,
                is_format=False,
            )
            return str(input_val)
    else:
        new_text = all_supported_lang_map[def_lang_tag].get(input_val)

        new_text = (
            str(input_val if isinstance(input_val, str) else input_val[0])
            if new_text is None
            else str(new_text)
        )

    need_join: bool = True
    if is_format and (fmt_args or fmt_kwargs):
        from ..easyrip_log import log

        try:
            new_text = new_text.format(*fmt_args, **fmt_kwargs)
        except (IndexError, KeyError) as e:
            log.debug(
                f"`{e!r}` in `{gettext.__name__}` when str.format",
                deep=True,
                is_format=False,
                print_level=log.LogLevel._detail,
            )
        else:
            need_join = False

    if need_join:
        new_text = " ".join(
            map(
                str,
                itertools.chain(
                    [new_text],
                    fmt_args,
                    (f"{k}={v!r}" for k, v in fmt_kwargs.items()),
                ),
            )
        )

    return new_text


class Mlang_exception(Exception):
    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        msg = args[0]
        if isinstance(msg, str):
            new_msg: str = gettext(
                msg, *args[1:], is_format=True, lang_tag=None, **kwargs
            )
            super().__init__(new_msg)
        else:
            super().__init__(*args)

import locale

from . import lang_en, lang_zh_Hans_CN
from .global_lang_val import (
    Global_lang_val,
    Lang_tag,
    Lang_tag_language,
    Lang_tag_region,
    Lang_tag_script,
    Lang_tag_val,
)
from .translator import translate_subtitles

__all__ = [
    "Global_lang_val",
    "Lang_tag",
    "Lang_tag_language",
    "Lang_tag_region",
    "Lang_tag_script",
    "Lang_tag_val",
    "Mlang_exception",
    "get_system_language",
    "gettext",
    "translate_subtitles",
]


all_supported_lang_map: dict[Lang_tag, dict[str, str]] = {
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
    org_text: str,
    *fmt_args: object,
    is_format: bool = True,
    **fmt_kwargs: object,
) -> str:
    new_text: str | None = None

    new_text = all_supported_lang_map[
        Global_lang_val.gettext_target_lang.match(all_supported_lang_map)
        or lang_en.LANG_TAG
    ].get(org_text)

    new_text = str(org_text) if new_text is None else str(new_text)

    if is_format and (fmt_args or fmt_kwargs):
        from ..easyrip_log import log

        try:
            new_text = new_text.format(*fmt_args, **fmt_kwargs)
        except Exception as e:
            log.debug(f"{e!r} in gettext when str.format", deep=True, is_format=False)

    return new_text


class Mlang_exception(Exception):
    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        msg = args[0]
        if isinstance(msg, str):
            new_msg: str = gettext(msg, *args[1:], is_format=True, **kwargs)
            super().__init__(new_msg)
        else:
            super().__init__(msg, *args[1:])

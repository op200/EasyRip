import ctypes

from . import lang_en, lang_zh_CN
from .global_lang_val import (
    Global_lang_val,
    Lang_tag,
    Lang_tag_language,
    Lang_tag_region,
    Lang_tag_script,
    Lang_tag_val,
)
from .translator import translate_subtitles

Extra_text_index = Global_lang_val.Extra_text_index

__all__ = [
    "Global_lang_val",
    "Lang_tag",
    "Lang_tag_language",
    "Lang_tag_region",
    "Lang_tag_script",
    "Lang_tag_val",
    "get_system_language",
    "gettext",
    "translate_subtitles",
]


all_supported_lang_map: dict[Lang_tag, dict[str | Extra_text_index, str]] = {
    lang_en.LANG_TAG: lang_en.LANG_MAP,
    lang_zh_CN.LANG_TAG: lang_zh_CN.LANG_MAP,
}


def get_system_language() -> Lang_tag:
    # 获取系统默认的 UI 语言
    user_default_ui_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    lang_int = user_default_ui_lang & 0xFF  # 主要语言
    sub_lang_int = user_default_ui_lang >> 10  # 次要语言

    # 语言代码映射
    lang_map = {
        0x09: Lang_tag_language.en,  # 英语
        0x04: Lang_tag_language.zh,  # 中文
        0x0C: Lang_tag_language.fr,  # 法语
        0x07: Lang_tag_language.de,  # 德语
        0x0A: Lang_tag_language.es,  # 西班牙语
        0x10: Lang_tag_language.it,  # 意大利语
        0x13: Lang_tag_language.ja,  # 日语
        0x14: Lang_tag_language.ko,  # 韩语
        0x16: Lang_tag_language.ru,  # 俄语
    }

    # 次要语言代码映射
    sub_lang_map = {
        0x01: Lang_tag_region.US,  # 美国
        0x02: Lang_tag_region.GB,  # 英国
        0x03: Lang_tag_region.AU,  # 澳大利亚
        0x04: Lang_tag_region.CA,  # 加拿大
        0x05: Lang_tag_region.NZ,  # 新西兰
        0x06: Lang_tag_region.IE,  # 爱尔兰
        0x07: Lang_tag_region.ZA,  # 南非
        0x08: Lang_tag_region.JM,  # 牙买加
        0x09: Lang_tag_region.TT,  # 加勒比地区
        0x0A: Lang_tag_region.BZ,  # 伯利兹
        0x0B: Lang_tag_region.TT,  # 特立尼达和多巴哥
        0x0D: Lang_tag_region.PH,  # 菲律宾
        0x0E: Lang_tag_region.IN,  # 印度
        0x0F: Lang_tag_region.MY,  # 马来西亚
        0x10: Lang_tag_region.SG,  # 新加坡
        0x11: Lang_tag_region.HK,  # 香港特别行政区
        0x12: Lang_tag_region.MO,  # 澳门特别行政区
        0x13: Lang_tag_region.TW,  # 台湾地区
        0x00: Lang_tag_region.CN,  # 中国大陆
    }

    return Lang_tag(
        language=lang_map.get(lang_int, Lang_tag_language.Unknown),
        region=sub_lang_map.get(sub_lang_int, Lang_tag_region.Unknown),
    )


def gettext(
    org_text: str | Extra_text_index,
    *vals: object,
    is_format: bool = True,
) -> str:
    new_text: str | None = None

    new_text = all_supported_lang_map[
        Global_lang_val.gettext_target_lang.match(all_supported_lang_map)
        or lang_en.LANG_TAG
    ].get(org_text)

    new_text = str(org_text) if new_text is None else str(new_text)

    if is_format:
        from ..easyrip_log import log

        try:
            new_text = new_text.format(*vals)
        except Exception as e:
            log.debug(f"{e!r} in gettext when str.format", deep=True, is_format=False)

    return new_text

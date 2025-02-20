import ctypes

from . import lang_en
from . import lang_zh_CN
from . import global_val

Language, Region, GlobalLangVal = (
    global_val.Language,
    global_val.Region,
    global_val.GlobalLangVal,
)
ExtraTextIndex = GlobalLangVal.ExtraTextIndex


def get_system_language():
    # 获取系统默认的 UI 语言
    user_default_ui_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    lang_int = user_default_ui_lang & 0xFF  # 主要语言
    sub_lang_int = user_default_ui_lang >> 10  # 次要语言

    # 语言代码映射
    lang_map = {
        0x09: Language.en,  # 英语
        0x04: Language.zh,  # 中文
        0x0C: Language.fr,  # 法语
        0x07: Language.de,  # 德语
        0x0A: Language.es,  # 西班牙语
        0x10: Language.it,  # 意大利语
        0x13: Language.ja,  # 日语
        0x14: Language.ko,  # 韩语
        0x16: Language.ru,  # 俄语
    }

    # 次要语言代码映射（以英语为例）
    sub_lang_map = {
        0x01: Region.US,  # 美国
        0x02: Region.UK,  # 英国
        0x03: Region.AU,  # 澳大利亚
        0x04: Region.CA,  # 加拿大
        0x05: Region.NZ,  # 新西兰
        0x06: Region.IE,  # 爱尔兰
        0x07: Region.ZA,  # 南非
        0x08: Region.JM,  # 牙买加
        0x09: Region.TT,  # 加勒比地区
        0x0A: Region.BZ,  # 伯利兹
        0x0B: Region.TT,  # 特立尼达和多巴哥
        0x0D: Region.PH,  # 菲律宾
        0x0E: Region.IN,  # 印度
        0x0F: Region.MY,  # 马来西亚
        0x10: Region.SG,  # 新加坡
        0x11: Region.HK,  # 香港特别行政区
        0x12: Region.MO,  # 澳门特别行政区
        0x13: Region.TW,  # 台湾地区
        0x00: Region.CN,  # 中国大陆
    }

    lang = lang_map.get(lang_int, Language.Unknow)
    sub_lang = sub_lang_map.get(sub_lang_int, Region.Unknow)

    return (lang, sub_lang)


def gettext(org_text: str | ExtraTextIndex, *vals):
    new_text: str | None = None

    if GlobalLangVal.gettext_target_lang[0] is Language.zh:
        new_text = lang_zh_CN.lang_map.get(org_text)

    new_text = new_text or lang_en.lang_map.get(org_text) or org_text
    try:
        new_text = new_text.format(*vals)
    except IndexError:
        from easyrip_log import log

        log.error("IndexError in gettext when str.format")

    return new_text

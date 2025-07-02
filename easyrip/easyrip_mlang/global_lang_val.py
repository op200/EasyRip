import enum


class Language(enum.Enum):
    Unknow = ("Unknow", "Unknow")
    en = ("en", "English")
    zh = ("zh", "Chinese")
    fr = ("fr", "French")
    de = ("de", "German")
    es = ("es", "Spanish")
    it = ("it", "Italian")
    ja = ("ja", "Japanese")
    ko = ("ko", "Korean")
    ru = ("ru", "Russian")


class Region(enum.Enum):
    Unknow = ("Unknow", "Unknow")
    US = ("US", "United States")
    UK = ("UK", "United Kingdom")
    AU = ("AU", "Australia")
    CA = ("CA", "Canada")
    NZ = ("NZ", "New Zealand")
    IE = ("IE", "Ireland")
    ZA = ("ZA", "South Africa")
    JM = ("JM", "Jamaica")
    TT = ("TT", "Caribbean")
    BZ = ("BZ", "Belize")
    PH = ("PH", "Philippines")
    IN = ("IN", "India")
    MY = ("MY", "Malaysia")
    SG = ("SG", "Singapore")
    HK = ("HK", "Hong Kong SAR")
    MO = ("MO", "Macau SAR")
    TW = ("TW", "Taiwan")
    CN = ("CN", "China")


class Global_lang_val:
    class Extra_text_index(enum.Enum):
        HELP_DOC = enum.auto()
        NEW_VER_TIP = enum.auto()

    gettext_target_lang: tuple[Language, Region] = (Language.Unknow, Region.Unknow)

    language_tag__local_str: dict[str, str] = {
        # 语言代码
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",  # 韩文
        "fr": "Français",  # 法文
        "de": "Deutsch",  # 德文
        "es": "Español",  # 西班牙文
        "ru": "Русский",  # 俄文
        "ar": "العربية",  # 阿拉伯文
        "yue": "粵語",
        # 文字变体
        "Hans": "简体",  # 简体中文
        "Hant": "繁體",  # 繁体中文
        # 地区
        "CN": "中国大陆",
        "HK": "香港",
        "TW": "台灣",
        "US": "United States",
        "JP": "日本",
        "GB": "United Kingdom",
        # 方言 / 变体
        "cmn": "普通话",
        "wuu": "吴语",
    }

    @staticmethod
    def language_tag_to_local_str(language_tag: str) -> str:
        return "-".join(
            Global_lang_val.language_tag__local_str.get(s, s)
            for s in language_tag.split("-")
        )

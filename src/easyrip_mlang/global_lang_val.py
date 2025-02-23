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


class GlobalLangVal:
    class ExtraTextIndex(enum.Enum):
        HELP_DOC = enum.auto()
        NEW_VER_TIP = enum.auto()

    gettext_target_lang: tuple[Language, Region] = (Language.Unknow, Region.Unknow)

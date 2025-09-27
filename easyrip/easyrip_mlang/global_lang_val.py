from dataclasses import dataclass
import enum
from typing import Self


@dataclass(slots=True)
class Lang_tag_val:
    en_name: str
    local_name: str


class Lang_tag_language(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown", local_name="Unknown")
    en = Lang_tag_val(en_name="English", local_name="English")
    zh = Lang_tag_val(en_name="Chinese", local_name="中文")
    fr = Lang_tag_val(en_name="French", local_name="Français")
    de = Lang_tag_val(en_name="German", local_name="Deutsch")
    es = Lang_tag_val(en_name="Spanish", local_name="Español")
    it = Lang_tag_val(en_name="Italian", local_name="Italiano")
    ja = Lang_tag_val(en_name="Japanese", local_name="日本語")
    ko = Lang_tag_val(en_name="Korean", local_name="한국어")
    ru = Lang_tag_val(en_name="Russian", local_name="Русский")
    ar = Lang_tag_val(en_name="", local_name="العربية")

    cmn = Lang_tag_val(en_name="Mandarin", local_name="普通话")
    wuu = Lang_tag_val(en_name="Wu", local_name="")  # 吴语
    yue = Lang_tag_val(en_name="Cantonese", local_name="")  # 粤语
    hak = Lang_tag_val(en_name="Hakka", local_name="")  # 客家话
    nan = Lang_tag_val(en_name="Min Nan", local_name="")  # 闽南语

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown


class Lang_tag_script(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown", local_name="Unknown")
    Hans = Lang_tag_val(en_name="Simplified Chinese", local_name="简体")
    Hant = Lang_tag_val(en_name="Traditional Chinese", local_name="繁體")
    Latn = Lang_tag_val(en_name="Latin", local_name="")
    Cyrl = Lang_tag_val(en_name="Cyrillic", local_name="")
    Arab = Lang_tag_val(en_name="Arabic", local_name="")

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown


class Lang_tag_region(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown", local_name="")
    US = Lang_tag_val(en_name="United States", local_name="United States")
    GB = Lang_tag_val(en_name="United Kingdom", local_name="United Kingdom")
    AU = Lang_tag_val(en_name="Australia", local_name="")
    CA = Lang_tag_val(en_name="Canada", local_name="")
    NZ = Lang_tag_val(en_name="New Zealand", local_name="")
    IE = Lang_tag_val(en_name="Ireland", local_name="")
    ZA = Lang_tag_val(en_name="South Africa", local_name="")
    JM = Lang_tag_val(en_name="Jamaica", local_name="")
    TT = Lang_tag_val(en_name="Caribbean", local_name="")
    BZ = Lang_tag_val(en_name="Belize", local_name="")
    PH = Lang_tag_val(en_name="Philippines", local_name="")
    IN = Lang_tag_val(en_name="India", local_name="")
    MY = Lang_tag_val(en_name="Malaysia", local_name="")
    SG = Lang_tag_val(en_name="Singapore", local_name="")
    MO = Lang_tag_val(en_name="Macau SAR", local_name="")
    HK = Lang_tag_val(en_name="Hong Kong SAR", local_name="香港")
    TW = Lang_tag_val(en_name="Taiwan", local_name="台灣")
    CN = Lang_tag_val(en_name="China", local_name="中国大陆")

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown


@dataclass(slots=True)
class Lang_tag:
    language: Lang_tag_language = Lang_tag_language.Unknown
    script: Lang_tag_script = Lang_tag_script.Unknown
    region: Lang_tag_region = Lang_tag_region.Unknown

    @classmethod
    def from_str(
        cls,
        str_tag: str,
    ) -> Self:
        """
        #### 输入语言标签字符串，输出标签对象
        e.g. zh-Hans-CN -> (Language.zh, Script.Hans, Region.CN)
        """

        from ..easyrip_mlang import gettext

        str_tag_tuple = tuple(s for s in str_tag.split("-"))

        language = Lang_tag_language[str_tag_tuple[0]]
        script: Lang_tag_script = Lang_tag_script.Unknown
        region: Lang_tag_region = Lang_tag_region.Unknown

        for i, s in enumerate(str_tag_tuple[1:]):
            if s in Lang_tag_script._member_names_:
                if i != 0:
                    Exception(
                        gettext("The input language tag string format is illegal")
                    )
                script = Lang_tag_script[s]
            elif s in Lang_tag_region._member_names_:
                region = Lang_tag_region[s]

        return cls(
            language=language,
            script=script,
            region=region,
        )

    def __str__(self) -> str:
        """返回语言标签字符串"""
        if self.language == Lang_tag_language.Unknown:
            Exception("The Language is Unknown")

        res_str: str = self.language.name
        if self.script != Lang_tag_script.Unknown:
            res_str += f"-{self.script.name}"
        if self.region != Lang_tag_region.Unknown:
            res_str += f"-{self.region.name}"

        return res_str


class Global_lang_val:
    class Extra_text_index(enum.Enum):
        HELP_DOC = enum.auto()
        NEW_VER_TIP = enum.auto()

    gettext_target_lang: Lang_tag = Lang_tag()

    @staticmethod
    def language_tag_to_local_str(language_tag: str) -> str:
        from ..easyrip_mlang import gettext

        tag_list = language_tag.split("-")
        tag_list_len = len(tag_list)

        if tag_list_len == 0:
            Exception(gettext("The input language tag string format is illegal"))

        res_str_list: list[str] = [
            _local_name
            if (_org_name := tag_list[0]) in Lang_tag_language._member_names_
            and (_local_name := Lang_tag_language[_org_name].value.local_name)
            else _org_name
        ]

        if tag_list_len >= 2:
            _org_name = tag_list[1]

            if _org_name in Lang_tag_script._member_names_:
                _local_name = Lang_tag_script[_org_name].value.local_name
            elif _org_name in Lang_tag_region._member_names_:
                _local_name = Lang_tag_region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        if tag_list_len >= 3:
            _org_name = tag_list[2]

            if _org_name in Lang_tag_region._member_names_:
                _local_name = Lang_tag_region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        return "-".join(res_str_list)

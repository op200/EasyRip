import enum
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self, final


@final
@dataclass(slots=True, init=False, eq=False)
class Lang_tag_val:
    en_name: str
    _local_name: str | None

    @property
    def local_name(self) -> str:
        return self.en_name if self._local_name is None else self._local_name

    @local_name.setter
    def local_name(self, val: str | None) -> None:
        if val is not None and len(val) == 0:
            raise ValueError("The length of the name cannot be 0")

        self._local_name = val

    def __init__(self, *, en_name: str, local_name: str | None = None) -> None:
        if len(en_name) == 0:
            raise ValueError("The length of the name cannot be 0")

        self.en_name = en_name
        self.local_name = local_name

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(en_name={self.en_name}, local_name={self._local_name})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Lang_tag_val):
            return self.en_name == other.en_name
        return False

    def __hash__(self) -> int:
        return hash(self.en_name)


class Lang_tag_language(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown")

    # ISO 639-1
    en = Lang_tag_val(en_name="English", local_name="English")
    zh = Lang_tag_val(en_name="Chinese", local_name="中文")
    fr = Lang_tag_val(en_name="French", local_name="Français")
    de = Lang_tag_val(en_name="German", local_name="Deutsch")
    es = Lang_tag_val(en_name="Spanish", local_name="Español")
    it = Lang_tag_val(en_name="Italian", local_name="Italiano")
    ja = Lang_tag_val(en_name="Japanese", local_name="日本語")
    ko = Lang_tag_val(en_name="Korean", local_name="한국어")
    ru = Lang_tag_val(en_name="Russian", local_name="Русский")
    ar = Lang_tag_val(en_name="Arabic", local_name="العربية")

    # ISO 639-2
    eng = en
    zho = chi = zh
    fra = fre = fr
    deu = ger = de
    spa = es
    ita = it
    jpn = ja
    kor = ko
    rus = ru
    ara = ar

    # ISO 639-3
    # 与 p2 重叠的放在 p2
    cdo = Lang_tag_val(en_name="Min Dong Chinese", local_name="闽东语")
    cjy = Lang_tag_val(en_name="Jinyu Chinese", local_name="晋语")
    cmn = Lang_tag_val(en_name="Mandarin Chinese", local_name="普通话")
    cnp = Lang_tag_val(en_name="Northern Ping Chinese", local_name="北平语")
    wuu = Lang_tag_val(en_name="Wu Chinese", local_name="吴语")
    yue = Lang_tag_val(en_name="Yue Chinese", local_name="粤语")
    hak = Lang_tag_val(en_name="Hakka Chinese", local_name="客家话")
    nan = Lang_tag_val(en_name="Min Nan Chinese", local_name="闽南语")
    och = Lang_tag_val(en_name="Old Chinese", local_name="古汉语")

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown

    @classmethod
    def from_name(cls, name: str):
        try:
            return cls[name]
        except KeyError:
            return cls.Unknown


class Lang_tag_script(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown")

    Hans = Lang_tag_val(en_name="Simplified Chinese", local_name="简体")
    Hant = Lang_tag_val(en_name="Traditional Chinese", local_name="繁體")
    Latn = Lang_tag_val(en_name="Latin", local_name="Latina")
    Cyrl = Lang_tag_val(en_name="Cyrillic", local_name="Кириллица")
    Arab = Lang_tag_val(en_name="Arabic", local_name="العربية")

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown

    @classmethod
    def from_name(cls, name: str):
        try:
            return cls[name]
        except KeyError:
            return cls.Unknown


class Lang_tag_region(enum.Enum):
    Unknown = Lang_tag_val(en_name="Unknown")

    US = Lang_tag_val(en_name="United States", local_name="United States")
    GB = Lang_tag_val(en_name="United Kingdom", local_name="United Kingdom")
    AU = Lang_tag_val(en_name="Australia", local_name="Australia")
    CA = Lang_tag_val(en_name="Canada", local_name="Canada")
    NZ = Lang_tag_val(en_name="New Zealand", local_name="New Zealand")
    IE = Lang_tag_val(en_name="Ireland", local_name="Éire")
    ZA = Lang_tag_val(en_name="South Africa", local_name="South Africa")
    JM = Lang_tag_val(en_name="Jamaica", local_name="Jamaica")
    TT = Lang_tag_val(en_name="Caribbean", local_name="Caribbean")
    BZ = Lang_tag_val(en_name="Belize", local_name="Belize")
    PH = Lang_tag_val(en_name="Philippines", local_name="Pilipinas")
    IN = Lang_tag_val(en_name="India", local_name="भारत")
    MY = Lang_tag_val(en_name="Malaysia", local_name="Malaysia")
    SG = Lang_tag_val(en_name="Singapore", local_name="Singapura")
    MO = Lang_tag_val(en_name="Macau SAR", local_name="澳門")
    HK = Lang_tag_val(en_name="Hong Kong SAR", local_name="香港")
    TW = Lang_tag_val(en_name="Taiwan", local_name="台灣")
    CN = Lang_tag_val(en_name="China", local_name="中国大陆")

    @classmethod
    def _missing_(cls, value: object):
        return cls.Unknown

    @classmethod
    def from_name(cls, name: str):
        try:
            return cls[name]
        except KeyError:
            return cls.Unknown


@final
@dataclass(slots=True, kw_only=True)
class Lang_tag:
    language: Lang_tag_language = Lang_tag_language.Unknown
    script: Lang_tag_script = Lang_tag_script.Unknown
    region: Lang_tag_region = Lang_tag_region.Unknown

    class Match_priority(enum.Enum):
        script = enum.auto()
        region = enum.auto()

    def match(
        self,
        target_tags: Iterable[Self],
        *,
        is_incomplete_match: bool = True,
        priority: Match_priority = Match_priority.script,
        is_allow_mismatch_language: bool = False,
    ) -> Self | None:
        """启用不完整匹配时，找到最匹配的第一项"""
        target_tags_tuple = tuple(target_tags)
        del target_tags

        matching_tags_tuple = tuple(
            tag for tag in target_tags_tuple if tag.language is self.language
        )
        if not matching_tags_tuple:
            if is_allow_mismatch_language:
                matching_tags_tuple = target_tags_tuple
            else:
                return None

        if self in matching_tags_tuple:
            return self
        if not is_incomplete_match:
            return None

        same_region_tuple = tuple(
            tag for tag in matching_tags_tuple if tag.region is self.region
        )

        same_script_tuple = tuple(
            tag for tag in matching_tags_tuple if tag.script is self.script
        )

        if priority_same_tuple := (
            same_script_tuple + same_region_tuple
            if priority is Lang_tag.Match_priority.script
            else same_region_tuple + same_script_tuple
        ):
            return priority_same_tuple[0]

        return matching_tags_tuple[0]

    @classmethod
    def from_str(
        cls,
        str_tag: str,
    ) -> Self:
        """
        输入语言标签字符串，输出标签对象

        e.g. zh-Hans-CN -> Self(Language.zh, Script.Hans, Region.CN)
        """
        from ..easyrip_mlang import gettext

        str_tag_list = str_tag.split("-")

        language = Lang_tag_language.from_name(str_tag_list[0])
        script: Lang_tag_script = Lang_tag_script.Unknown
        region: Lang_tag_region = Lang_tag_region.Unknown

        for i, s in enumerate(str_tag_list[1:]):
            if s in Lang_tag_script._member_map_:
                if i != 0:
                    raise ValueError(
                        gettext("The input language tag string format is illegal")
                    )
                script = Lang_tag_script[s]
            elif s in Lang_tag_region._member_map_:
                region = Lang_tag_region[s]

        return cls(
            language=language,
            script=script,
            region=region,
        )

    def __str__(self) -> str:
        """返回语言标签字符串"""
        if self.language == Lang_tag_language.Unknown:
            raise Exception("The Language is Unknown")

        res_str: str = self.language.name
        if self.script != Lang_tag_script.Unknown:
            res_str += f"-{self.script.name}"
        if self.region != Lang_tag_region.Unknown:
            res_str += f"-{self.region.name}"

        return res_str

    def __hash__(self) -> int:
        return hash((self.language, self.script, self.region))


class Global_lang_val:
    gettext_target_lang: Lang_tag = Lang_tag()

    @staticmethod
    def language_tag_to_local_str(language_tag: str) -> str:
        from ..easyrip_mlang import gettext

        tag_list = language_tag.split("-")
        tag_list_len = len(tag_list)

        if tag_list_len == 0:
            raise Exception(gettext("The input language tag string format is illegal"))

        res_str_list: list[str] = [
            _local_name
            if (_org_name := tag_list[0]) in Lang_tag_language._member_map_
            and (_local_name := Lang_tag_language[_org_name].value.local_name)
            else _org_name
        ]

        if tag_list_len >= 2:
            _org_name = tag_list[1]

            if _org_name in Lang_tag_script.__members__:
                _local_name = Lang_tag_script[_org_name].value.local_name
            elif _org_name in Lang_tag_region._member_map_:
                _local_name = Lang_tag_region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        if tag_list_len >= 3:
            _org_name = tag_list[2]

            if _org_name in Lang_tag_region._member_map_:
                _local_name = Lang_tag_region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        return (" - " if any(" " in s for s in res_str_list) else "-").join(
            res_str_list
        )

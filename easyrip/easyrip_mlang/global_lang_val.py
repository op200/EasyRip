import enum
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self, final


@final
@dataclass(slots=True, kw_only=True)
class Lang_tag:
    from .lang_tag_val import Lang_tag_language as Language
    from .lang_tag_val import Lang_tag_region as Region
    from .lang_tag_val import Lang_tag_script as Script

    language: Language = Language.Unknown
    script: Script = Script.Unknown
    region: Region = Region.Unknown

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
            if priority is self.__class__.Match_priority.script
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

        language: Lang_tag.Language = cls.Language.from_name(str_tag_list[0])
        script: Lang_tag.Script = cls.Script.Unknown
        region: Lang_tag.Region = cls.Region.Unknown

        for i, s in enumerate(str_tag_list[1:]):
            if s in cls.Script._member_map_:
                if i != 0:
                    raise ValueError(
                        gettext("The input language tag string format is illegal")
                    )
                script = cls.Script[s]
            elif s in cls.Region._member_map_:
                region = cls.Region[s]

        return cls(
            language=language,
            script=script,
            region=region,
        )

    def __str__(self) -> str:
        """返回语言标签字符串"""
        if self.language == self.__class__.Language.Unknown:
            raise Exception("The Language is Unknown")

        res_str: str = self.language.name
        if self.script != self.__class__.Script.Unknown:
            res_str += f"-{self.script.name}"
        if self.region != self.__class__.Region.Unknown:
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
            if (_org_name := tag_list[0]) in Lang_tag.Language._member_map_
            and (_local_name := Lang_tag.Language[_org_name].value.local_name)
            else _org_name
        ]

        if tag_list_len >= 2:
            _org_name = tag_list[1]

            if _org_name in Lang_tag.Script.__members__:
                _local_name = Lang_tag.Script[_org_name].value.local_name
            elif _org_name in Lang_tag.Region._member_map_:
                _local_name = Lang_tag.Region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        if tag_list_len >= 3:
            _org_name = tag_list[2]

            if _org_name in Lang_tag.Region._member_map_:
                _local_name = Lang_tag.Region[_org_name].value.local_name
            else:
                _local_name = _org_name

            res_str_list.append(_local_name)

        return (" - " if any(" " in s for s in res_str_list) else "-").join(
            res_str_list
        )

import enum
import textwrap
from functools import reduce
from typing import Final, LiteralString


class Preset_name(enum.Enum):
    custom = "custom"

    subset = "subset"

    flac = "flac"

    copy = "copy"

    x264 = "x264"
    x264fast = "x264fast"
    x264slow = "x264slow"

    x265 = "x265"
    x265fast4 = "x265fast4"
    x265fast3 = "x265fast3"
    x265fast2 = "x265fast2"
    x265fast = "x265fast"
    x265slow = "x265slow"
    x265full = "x265full"

    svtav1 = "svtav1"

    vvenc = "vvenc"

    h264_amf = "h264_amf"
    h264_nvenc = "h264_nvenc"
    h264_qsv = "h264_qsv"

    hevc_amf = "hevc_amf"
    hevc_nvenc = "hevc_nvenc"
    hevc_qsv = "hevc_qsv"

    av1_amf = "av1_amf"
    av1_nvenc = "av1_nvenc"
    av1_qsv = "av1_qsv"

    @classmethod
    def _missing_(cls, value: object):
        from ..easyrip_log import log

        DEFAULT = cls.custom
        log.error(
            "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
            value,
            cls.__name__,
            DEFAULT.name,
            list(cls.__members__.values()),
        )
        return DEFAULT

    @classmethod
    def to_help_string(cls, prefix: str = ""):
        return textwrap.indent(
            reduce(
                lambda acc,
                add: f"{acc}{' ' if add.startswith(acc.split()[-1][:4]) else '\n'}{add}",
                tuple[str](cls._value2member_map_),
            ),
            prefix=prefix,
        )


class Audio_codec(enum.Enum):
    copy = "copy"
    libopus = "libopus"
    flac = "flac"

    # 别名
    opus = libopus

    @classmethod
    def _missing_(cls, value: object):
        from ..easyrip_log import log

        DEFAULT = cls.copy
        log.error(
            "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
            value,
            cls.__name__,
            DEFAULT.name,
            list(cls.__members__.values()),
        )
        return DEFAULT

    @classmethod
    def to_help_string(cls, prefix: str = ""):
        return textwrap.indent(
            reduce(
                lambda acc,
                add: f"{acc}{' ' if add.endswith(acc.split()[-1][-4:]) else '\n'}{add}",
                tuple[str](cls._member_map_),
            ),
            prefix=prefix,
        )


class Muxer(enum.Enum):
    mp4 = "mp4"
    mkv = "mkv"

    @classmethod
    def _missing_(cls, value: object):
        from ..easyrip_log import log

        DEFAULT = cls.mkv
        log.error(
            "'{}' is not a valid '{}', set to default value '{}'. Valid options are: {}",
            value,
            cls.__name__,
            DEFAULT.name,
            list(cls.__members__.values()),
        )
        return DEFAULT


X265_PARAMS_NAME: Final[tuple[LiteralString, ...]] = (
    "crf",
    "qpmin",
    "qpmax",
    "psy-rd",
    "rd",
    "rdoq-level",
    "psy-rdoq",
    "qcomp",
    "keyint",
    "min-keyint",
    "deblock",
    "me",
    "merange",
    "hme",
    "hme-search",
    "hme-range",
    "aq-mode",
    "aq-strength",
    "tu-intra-depth",
    "tu-inter-depth",
    "limit-tu",
    "bframes",
    "ref",
    "subme",
    "open-gop",
    "gop-lookahead",
    "rc-lookahead",
    "rect",
    "amp",
    "cbqpoffs",
    "crqpoffs",
    "ipratio",
    "pbratio",
    "early-skip",
    "ctu",
    "min-cu-size",
    "max-tu-size",
    "level-idc",
    "sao",
)
X264_PARAMS_NAME: Final[tuple[LiteralString, ...]] = (
    "threads",
    "crf",
    "psy-rd",
    "qcomp",
    "keyint",
    "deblock",
    "qpmin",
    "qpmax",
    "bframes",
    "ref",
    "subme",
    "me",
    "merange",
    "aq-mode",
    "rc-lookahead",
    "min-keyint",
    "trellis",
    "fast-pskip",
    "partitions",
    "direct",
)


_DEFAULT_X265_PARAMS: Final[dict[LiteralString, LiteralString]] = {
    "crf": "20",
    "qpmin": "6",
    "qpmax": "32",
    "rd": "3",
    "psy-rd": "2",
    "rdoq-level": "0",
    "psy-rdoq": "0",
    "qcomp": "0.68",
    "keyint": "250",
    "min-keyint": "2",
    "deblock": "0,0",
    "me": "umh",
    "merange": "57",
    "hme": "1",
    "hme-search": "hex,hex,hex",
    "hme-range": "16,57,92",
    "aq-mode": "2",
    "aq-strength": "1",
    "tu-intra-depth": "1",
    "tu-inter-depth": "1",
    "limit-tu": "0",
    "bframes": "16",
    "ref": "8",
    "subme": "2",
    "open-gop": "1",
    "gop-lookahead": "0",
    "rc-lookahead": "20",
    "rect": "0",
    "amp": "0",
    "cbqpoffs": "0",
    "crqpoffs": "0",
    "ipratio": "1.4",
    "pbratio": "1.3",
    "early-skip": "1",
    "ctu": "64",
    "min-cu-size": "8",
    "max-tu-size": "32",
    "level-idc": "0",
    "sao": "0",
    "weightb": "1",
    "info": "1",
}


PRESET_OPT_NAME: Final[dict[Preset_name, tuple[LiteralString, ...]]] = {
    Preset_name.x264: X264_PARAMS_NAME,
    Preset_name.x264fast: X264_PARAMS_NAME,
    Preset_name.x264slow: X264_PARAMS_NAME,
    Preset_name.x265: X265_PARAMS_NAME,
    Preset_name.x265fast4: X265_PARAMS_NAME,
    Preset_name.x265fast3: X265_PARAMS_NAME,
    Preset_name.x265fast2: X265_PARAMS_NAME,
    Preset_name.x265fast: X265_PARAMS_NAME,
    Preset_name.x265slow: X265_PARAMS_NAME,
    Preset_name.x265full: X265_PARAMS_NAME,
}
DEFAULT_PRESET_PARAMS: Final[dict[Preset_name, dict[LiteralString, LiteralString]]] = {
    Preset_name.x264fast: {
        "threads": "auto",
        "crf": "20",
        "psy-rd": "0.6,0.15",
        "qcomp": "0.66",
        "keyint": "250",
        "deblock": "0,0",
        "qpmin": "8",
        "qpmax": "32",
        "bframes": "8",
        "ref": "4",
        "subme": "5",
        "me": "hex",
        "merange": "16",
        "aq-mode": "1",
        "rc-lookahead": "60",
        "min-keyint": "2",
        "trellis": "1",
        "fast-pskip": "1",
        "weightb": "1",
        "partitions": "all",
        "direct": "auto",
    },
    Preset_name.x264slow: {
        "threads": "auto",
        "crf": "21",
        "psy-rd": "0.6,0.15",
        "qcomp": "0.66",
        "keyint": "250",
        "deblock": "-1,-1",
        "qpmin": "8",
        "qpmax": "32",
        "bframes": "16",
        "ref": "8",
        "subme": "7",
        "me": "umh",
        "merange": "24",
        "aq-mode": "3",
        "rc-lookahead": "120",
        "min-keyint": "2",
        "trellis": "2",
        "fast-pskip": "0",
        "weightb": "1",
        "partitions": "all",
        "direct": "auto",
    },
    Preset_name.x265fast4: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "18",
            "qpmin": "12",
            "qpmax": "28",
            "rd": "2",
            "rdoq-level": "1",
            "me": "hex",
            "merange": "57",
            "hme-search": "hex,hex,hex",
            "hme-range": "16,32,48",
            "aq-mode": "1",
            "tu-intra-depth": "1",
            "tu-inter-depth": "1",
            "limit-tu": "4",
            "bframes": "8",
            "ref": "6",
            "subme": "3",
            "open-gop": "0",
            "gop-lookahead": "0",
            "rc-lookahead": "48",
            "cbqpoffs": "-1",
            "crqpoffs": "-1",
            "pbratio": "1.28",
        }
    ),
    Preset_name.x265fast3: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "18",
            "qpmin": "12",
            "qpmax": "28",
            "rdoq-level": "1",
            "deblock": "-0.5,-0.5",
            "me": "hex",
            "merange": "57",
            "hme-search": "hex,hex,hex",
            "hme-range": "16,32,57",
            "aq-mode": "3",
            "tu-intra-depth": "2",
            "tu-inter-depth": "2",
            "limit-tu": "4",
            "bframes": "12",
            "ref": "6",
            "subme": "3",
            "open-gop": "0",
            "gop-lookahead": "0",
            "rc-lookahead": "120",
            "cbqpoffs": "-1",
            "crqpoffs": "-1",
            "pbratio": "1.27",
        }
    ),
    Preset_name.x265fast2: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "18",
            "qpmin": "12",
            "qpmax": "28",
            "rdoq-level": "2",
            "deblock": "-1,-1",
            "me": "hex",
            "merange": "57",
            "hme-search": "hex,hex,hex",
            "hme-range": "16,57,92",
            "aq-mode": "3",
            "tu-intra-depth": "3",
            "tu-inter-depth": "2",
            "limit-tu": "4",
            "ref": "6",
            "subme": "4",
            "open-gop": "0",
            "gop-lookahead": "0",
            "rc-lookahead": "192",
            "cbqpoffs": "-1",
            "crqpoffs": "-1",
            "pbratio": "1.25",
        }
    ),
    Preset_name.x265fast: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "18",
            "qpmin": "12",
            "qpmax": "28",
            "psy-rd": "1.8",
            "rdoq-level": "2",
            "psy-rdoq": "0.4",
            "keyint": "312",
            "deblock": "-1,-1",
            "me": "umh",
            "merange": "57",
            "hme-search": "umh,hex,hex",
            "hme-range": "16,57,92",
            "aq-mode": "4",
            "tu-intra-depth": "4",
            "tu-inter-depth": "3",
            "limit-tu": "4",
            "subme": "5",
            "gop-lookahead": "8",
            "rc-lookahead": "216",
            "cbqpoffs": "-2",
            "crqpoffs": "-2",
            "pbratio": "1.2",
        }
    ),
    Preset_name.x265slow: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "17.5",
            "qpmin": "12",
            "qpmax": "28",
            "rd": "5",
            "psy-rd": "1.8",
            "rdoq-level": "2",
            "psy-rdoq": "0.4",
            "qcomp": "0.7",
            "keyint": "312",
            "deblock": "-1,-1",
            "me": "umh",
            "merange": "57",
            "hme-search": "umh,hex,hex",
            "hme-range": "16,57,184",
            "aq-mode": "4",
            "aq-strength": "1",
            "tu-intra-depth": "4",
            "tu-inter-depth": "3",
            "limit-tu": "2",
            "subme": "6",
            "gop-lookahead": "14",
            "rc-lookahead": "250",
            "rect": "1",
            "min-keyint": "2",
            "cbqpoffs": "-2",
            "crqpoffs": "-2",
            "pbratio": "1.2",
            "early-skip": "0",
        }
    ),
    Preset_name.x265full: _DEFAULT_X265_PARAMS
    | dict[LiteralString, LiteralString](
        {
            "crf": "17",
            "qpmin": "3",
            "qpmax": "21.5",
            "psy-rd": "2.2",
            "rd": "5",
            "rdoq-level": "2",
            "psy-rdoq": "1.6",
            "qcomp": "0.72",
            "keyint": "266",
            "min-keyint": "2",
            "deblock": "-1,-1",
            "me": "umh",
            "merange": "160",
            "hme-search": "full,umh,hex",
            "hme-range": "16,92,320",
            "aq-mode": "4",
            "aq-strength": "1.2",
            "tu-intra-depth": "4",
            "tu-inter-depth": "4",
            "limit-tu": "2",
            "subme": "7",
            "open-gop": "1",
            "gop-lookahead": "14",
            "rc-lookahead": "250",
            "rect": "1",
            "amp": "1",
            "cbqpoffs": "-3",
            "crqpoffs": "-3",
            "ipratio": "1.43",
            "pbratio": "1.2",
            "early-skip": "0",
        }
    ),
}


SUBTITLE_SUFFIX_SET: Final[set[LiteralString]] = {
    ".srt",
    ".ass",
    ".ssa",
    ".sup",
    ".idx",
}
FONT_SUFFIX_SET: Final[set[LiteralString]] = {
    ".otf",
    ".ttf",
    ".ttc",
}

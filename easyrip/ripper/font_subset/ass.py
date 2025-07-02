from dataclasses import dataclass, field
import enum
from pathlib import Path

from ...easyrip_log import log
from ..utils import read_text


class Style_fmt_it(enum.Enum):
    Name = "Name"
    Fontname = "Fontname"
    Fontsize = "Fontsize"
    PrimaryColour = "PrimaryColour"
    SecondaryColour = "SecondaryColour"
    OutlineColour = "OutlineColour"
    BackColour = "BackColour"
    Bold = "Bold"
    Italic = "Italic"
    Underline = "Underline"
    StrikeOut = "StrikeOut"
    ScaleX = "ScaleX"
    ScaleY = "ScaleY"
    Spacing = "Spacing"
    Angle = "Angle"
    BorderStyle = "BorderStyle"
    Outline = "Outline"
    Shadow = "Shadow"
    Alignment = "Alignment"
    MarginL = "MarginL"
    MarginR = "MarginR"
    MarginV = "MarginV"
    Encoding = "Encoding"


# class Script_info_type(enum.Enum):
#     Comment = "Comment"
#     Data = "Dialogue"


@dataclass
class Script_info_data:
    # type: Script_info_type
    raw_str: str


@dataclass
class Script_info:
    data: list[Script_info_data] = field(default_factory=list)

    def to_ass_str(self) -> str:
        return "\n".join(
            (
                "[Script Info]",
                *(info.raw_str for info in self.data),
            )
        )


@dataclass
class Style_data:
    Name: str
    Fontname: str
    Fontsize: int
    PrimaryColour: str
    SecondaryColour: str
    OutlineColour: str
    BackColour: str
    Bold: int
    Italic: int
    Underline: int
    StrikeOut: int
    ScaleX: float
    ScaleY: float
    Spacing: float
    Angle: float
    BorderStyle: int
    Outline: float
    Shadow: float
    Alignment: int
    MarginL: int
    MarginR: int
    MarginV: int
    Encoding: int


DEFAULT_STYLE_FMT_ORDER = (
    Style_fmt_it.Name,
    Style_fmt_it.Fontname,
    Style_fmt_it.Fontsize,
    Style_fmt_it.PrimaryColour,
    Style_fmt_it.SecondaryColour,
    Style_fmt_it.OutlineColour,
    Style_fmt_it.BackColour,
    Style_fmt_it.Bold,
    Style_fmt_it.Italic,
    Style_fmt_it.Underline,
    Style_fmt_it.StrikeOut,
    Style_fmt_it.ScaleX,
    Style_fmt_it.ScaleY,
    Style_fmt_it.Spacing,
    Style_fmt_it.Angle,
    Style_fmt_it.BorderStyle,
    Style_fmt_it.Outline,
    Style_fmt_it.Shadow,
    Style_fmt_it.Alignment,
    Style_fmt_it.MarginL,
    Style_fmt_it.MarginR,
    Style_fmt_it.MarginV,
    Style_fmt_it.Encoding,
)


@dataclass
class Style:
    fmt_order: tuple[
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
        Style_fmt_it,
    ] = field(default_factory=lambda: DEFAULT_STYLE_FMT_ORDER)
    fmt_index: dict[Style_fmt_it, int] = field(
        default_factory=lambda: {
            Style_fmt_it.Name: 0,
            Style_fmt_it.Fontname: 1,
            Style_fmt_it.Fontsize: 2,
            Style_fmt_it.PrimaryColour: 3,
            Style_fmt_it.SecondaryColour: 4,
            Style_fmt_it.OutlineColour: 5,
            Style_fmt_it.BackColour: 6,
            Style_fmt_it.Bold: 7,
            Style_fmt_it.Italic: 8,
            Style_fmt_it.Underline: 9,
            Style_fmt_it.StrikeOut: 10,
            Style_fmt_it.ScaleX: 11,
            Style_fmt_it.ScaleY: 12,
            Style_fmt_it.Spacing: 13,
            Style_fmt_it.Angle: 14,
            Style_fmt_it.BorderStyle: 15,
            Style_fmt_it.Outline: 16,
            Style_fmt_it.Shadow: 17,
            Style_fmt_it.Alignment: 18,
            Style_fmt_it.MarginL: 19,
            Style_fmt_it.MarginR: 20,
            Style_fmt_it.MarginV: 21,
            Style_fmt_it.Encoding: 22,
        }
    )
    data: list[Style_data] = field(default_factory=list)

    def flush_fmt_order_index(self):
        for it in self.fmt_order:
            if index := next(
                (i for i, v in enumerate(DEFAULT_STYLE_FMT_ORDER) if v == it), None
            ):
                self.fmt_index[it] = index
            else:
                raise Ass_generation_failed(
                    f"Style Format flush order index err: can not find {it}"
                )

    def new_data(
        self,
        style_tuple: tuple[
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
        ],
    ) -> Style_data:
        try:
            res = Style_data(
                Name=style_tuple[self.fmt_index[Style_fmt_it.Name]],
                Fontname=style_tuple[self.fmt_index[Style_fmt_it.Fontname]],
                Fontsize=int(style_tuple[self.fmt_index[Style_fmt_it.Fontsize]]),
                PrimaryColour=style_tuple[self.fmt_index[Style_fmt_it.PrimaryColour]],
                SecondaryColour=style_tuple[
                    self.fmt_index[Style_fmt_it.SecondaryColour]
                ],
                OutlineColour=style_tuple[self.fmt_index[Style_fmt_it.OutlineColour]],
                BackColour=style_tuple[self.fmt_index[Style_fmt_it.BackColour]],
                Bold=int(style_tuple[self.fmt_index[Style_fmt_it.Bold]]),
                Italic=int(style_tuple[self.fmt_index[Style_fmt_it.Italic]]),
                Underline=int(style_tuple[self.fmt_index[Style_fmt_it.Underline]]),
                StrikeOut=int(style_tuple[self.fmt_index[Style_fmt_it.StrikeOut]]),
                ScaleX=float(style_tuple[self.fmt_index[Style_fmt_it.ScaleX]]),
                ScaleY=float(style_tuple[self.fmt_index[Style_fmt_it.ScaleY]]),
                Spacing=float(style_tuple[self.fmt_index[Style_fmt_it.Spacing]]),
                Angle=float(style_tuple[self.fmt_index[Style_fmt_it.Angle]]),
                BorderStyle=int(style_tuple[self.fmt_index[Style_fmt_it.BorderStyle]]),
                Outline=float(style_tuple[self.fmt_index[Style_fmt_it.Outline]]),
                Shadow=float(style_tuple[self.fmt_index[Style_fmt_it.Shadow]]),
                Alignment=int(style_tuple[self.fmt_index[Style_fmt_it.Alignment]]),
                MarginL=int(style_tuple[self.fmt_index[Style_fmt_it.MarginL]]),
                MarginR=int(style_tuple[self.fmt_index[Style_fmt_it.MarginR]]),
                MarginV=int(style_tuple[self.fmt_index[Style_fmt_it.MarginV]]),
                Encoding=int(style_tuple[self.fmt_index[Style_fmt_it.Encoding]]),
            )
        except ValueError as e:
            raise Ass_generation_failed(e)

        return res

    def to_ass_str(self) -> str:
        return "\n".join(
            (
                "[V4+ Styles]",
                f"Format: {', '.join(f.value for f in self.fmt_order)}",
                *(
                    "Style: "
                    + ",".join((str(getattr(style, k.value)) for k in self.fmt_order))
                    for style in self.data
                ),
            )
        )


class Event_fmt_it(enum.Enum):
    Layer = "Layer"
    Start = "Start"
    End = "End"
    Style = "Style"
    Name = "Name"
    MarginL = "MarginL"
    MarginR = "MarginR"
    MarginV = "MarginV"
    Effect = "Effect"
    Text = "Text"


class Event_type(enum.Enum):
    Dialogue = "Dialogue"
    Comment = "Comment"


@dataclass
class Event_data:
    type: Event_type

    Layer: int
    Start: str
    End: str
    Style: str
    Name: str
    MarginL: int
    MarginR: int
    MarginV: int
    Effect: str
    Text: str


DEFAULT_EVENT_FMT_ORDER = (
    Event_fmt_it.Layer,
    Event_fmt_it.Start,
    Event_fmt_it.End,
    Event_fmt_it.Style,
    Event_fmt_it.Name,
    Event_fmt_it.MarginL,
    Event_fmt_it.MarginR,
    Event_fmt_it.MarginV,
    Event_fmt_it.Effect,
    Event_fmt_it.Text,
)


@dataclass
class Event:
    fmt_order: tuple[
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
        Event_fmt_it,
    ] = field(default_factory=lambda: DEFAULT_EVENT_FMT_ORDER)
    fmt_index: dict[Event_fmt_it, int] = field(
        default_factory=lambda: {
            Event_fmt_it.Layer: 0,
            Event_fmt_it.Start: 1,
            Event_fmt_it.End: 2,
            Event_fmt_it.Style: 3,
            Event_fmt_it.Name: 4,
            Event_fmt_it.MarginL: 5,
            Event_fmt_it.MarginR: 6,
            Event_fmt_it.MarginV: 7,
            Event_fmt_it.Effect: 8,
            Event_fmt_it.Text: 9,
        }
    )
    data: list[Event_data] = field(default_factory=list)

    def flush_fmt_order_index(self):
        for it in self.fmt_order:
            if index := next(
                (i for i, v in enumerate(DEFAULT_EVENT_FMT_ORDER) if v == it), None
            ):
                self.fmt_index[it] = index
            else:
                raise Ass_generation_failed(
                    f"Event Format flush order index err: can not find {it}"
                )

    def new_data(
        self,
        event_tuple: tuple[
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
        ],
        event_type,
    ) -> Event_data:
        try:
            res = Event_data(
                type=event_type,
                Layer=int(event_tuple[self.fmt_index[Event_fmt_it.Layer]]),
                Start=event_tuple[self.fmt_index[Event_fmt_it.Start]],
                End=event_tuple[self.fmt_index[Event_fmt_it.End]],
                Style=event_tuple[self.fmt_index[Event_fmt_it.Style]],
                Name=event_tuple[self.fmt_index[Event_fmt_it.Name]],
                MarginL=int(event_tuple[self.fmt_index[Event_fmt_it.MarginL]]),
                MarginR=int(event_tuple[self.fmt_index[Event_fmt_it.MarginR]]),
                MarginV=int(event_tuple[self.fmt_index[Event_fmt_it.MarginV]]),
                Effect=event_tuple[self.fmt_index[Event_fmt_it.Effect]],
                Text=event_tuple[self.fmt_index[Event_fmt_it.Text]],
            )
        except ValueError as e:
            raise Ass_generation_failed(e)

        return res

    def to_ass_str(self, drop_unrander: bool = False) -> str:
        return "\n".join(
            (
                "[Events]",
                f"Format: {', '.join(f.value for f in self.fmt_order)}",
                *(
                    f"{'Comment' if event.type == Event_type.Comment else 'Dialogue'}: "
                    + ",".join((str(getattr(event, k.value)) for k in self.fmt_order))
                    for event in self.data
                    if drop_unrander is False
                    or (event.type != Event_type.Comment and event.Text)
                ),
            )
        )


@dataclass
class Unknow_data:
    head: str
    data: list[str] = field(default_factory=list)

    def to_ass_str(self) -> str:
        return "\n".join(
            (
                self.head,
                *(text for text in self.data),
            )
        )


class Ass_generation_failed(Exception):
    pass


class Ass:
    def __init__(self, path: str | Path):
        path = Path(path)
        if not path.is_file():
            log.error("Not a file: {}", path)

        self.script_info: Script_info = Script_info()
        self.style: Style = Style()
        self.event: Event = Event()
        self.unknow_data: list[Unknow_data] = []

        class State(enum.Enum):
            unknow = enum.auto()
            script_info = enum.auto()
            styles = enum.auto()
            events = enum.auto()

        state: State = State.unknow
        new_unknow_data: Unknow_data | None = None

        for line in read_text(path).splitlines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("[") and line.endswith("]"):
                if new_unknow_data is not None:
                    self.unknow_data.append(new_unknow_data)

                match head := line[1:-1]:
                    case "Script Info":
                        state = State.script_info
                    case "V4+ Styles":
                        state = State.styles
                    case "Events":
                        state = State.events
                    case _:
                        state = State.unknow
                        new_unknow_data = Unknow_data(head)

            elif line.startswith("Format:"):
                formats_generator = (v.strip() for v in line[7:].split(","))
                match state:
                    case State.styles:
                        format_order = tuple(Style_fmt_it(v) for v in formats_generator)
                        if len(format_order) != 23:
                            raise Ass_generation_failed("Style Format len != 23")

                        self.style.fmt_order = format_order

                    case State.events:
                        format_order = tuple(Event_fmt_it(v) for v in formats_generator)
                        if len(format_order) != 10:
                            raise Ass_generation_failed("Event Format != 10")

                        self.event.fmt_order = format_order

            else:
                match state:
                    case State.script_info:
                        self.script_info.data.append(Script_info_data(raw_str=line))

                    case State.styles:
                        if not line.startswith("Style:"):
                            log.warning("Skip a Style line (illegal format): {}", line)
                            continue

                        style_tuple = tuple(v.strip() for v in line[6:].split(","))
                        if len(style_tuple) != 23:
                            log.warning(
                                "Skip a Style line (Style Format len != 23): {}", line
                            )
                            continue

                        self.style.data.append(self.style.new_data(style_tuple))

                    case State.events:
                        event_type: Event_type
                        if line.startswith("Dialogue:"):
                            event_type = Event_type.Dialogue
                        elif line.startswith("Comment:"):
                            event_type = Event_type.Comment
                        else:
                            log.warning("Skip a Event line (illegal format): {}", line)
                            continue

                        event_tuple = tuple(
                            v.strip()
                            for v in line.split(":", maxsplit=1)[1].split(
                                ",", maxsplit=9
                            )
                        )
                        if len(event_tuple) != 10:
                            log.warning(
                                "Skip a Event line (Event Format len != 10): {}", line
                            )
                            continue

                        self.event.data.append(
                            self.event.new_data(event_tuple, event_type)
                        )

                    case State.unknow:
                        if new_unknow_data is None:
                            log.error(
                                "Unknown error occurred when read line: {}",
                                line,
                                deep=True,
                            )
                            raise Ass_generation_failed()
                        new_unknow_data.data.append(line)

        if new_unknow_data is not None:
            self.unknow_data.append(new_unknow_data)

    def __str__(
        self, drop_unrander: bool = False, drop_unkow_data: bool = False
    ) -> str:
        generator = (
            self.script_info.to_ass_str(),
            self.style.to_ass_str(),
            self.event.to_ass_str(drop_unrander),
            *(
                data.to_ass_str()
                for data in (() if drop_unkow_data else self.unknow_data)
            ),
        )
        return "\n\n".join(generator)


def parse_ass_text(text: str, use_libass_spec: bool) -> list[tuple[bool, str]]:
    if not use_libass_spec:
        # 模式1: 不处理转义字符
        result: list[tuple[bool, str]] = []
        current = []  # 当前累积的字符
        in_tag = False  # 是否在标签内

        for char in text:
            if in_tag is False:
                if char == "{":
                    # 开始新标签，先保存当前累积的普通文本
                    if current:
                        result.append((False, "".join(current)))
                        current = []
                    current.append(char)
                    in_tag = True
                else:
                    current.append(char)  # 普通文本
            else:
                current.append(char)  # 标签内容
                if char == "}":
                    # 标签结束
                    result.append((True, "".join(current)))
                    current = []
                    in_tag = False

        # 处理剩余部分
        if current:
            result.append((False, "".join(current)))
        return result

    else:
        # 模式2: 处理转义字符（libass规范）
        result = []
        current = []  # 当前累积的字符
        in_tag = False  # 是否在标签内
        escape_next = False  # 下一个字符是否转义

        for char in text:
            if escape_next:
                # 处理转义字符（任何字符直接作为普通字符）
                current.append(char)
                escape_next = False
            elif char == "\\":
                # 标记下一个字符为转义
                current.append(char)
                escape_next = True
            elif char == "{":
                if not in_tag:
                    # 开始新标签（非转义的{）
                    if current:
                        result.append((False, "".join(current)))
                        current = []
                    current.append(char)
                    in_tag = True
                else:
                    current.append(char)  # 标签内的{
            elif char == "}":
                if in_tag:
                    # 非转义的}结束标签
                    current.append(char)
                    result.append((True, "".join(current)))
                    current = []
                    in_tag = False
                else:
                    current.append(char)  # 普通文本的}
            else:
                current.append(char)  # 普通字符

        # 处理剩余部分
        if current:
            result.append((False, "".join(current)))
        return result

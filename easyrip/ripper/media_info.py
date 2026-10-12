import itertools
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self, cast

from ..easyrip_log import log
from ..easyrip_mlang import Mlang_exception
from ..utils import JsonObj, obj_fmt, time_str_to_sec, type_match


class Stream_error(Mlang_exception):
    pass


@dataclass(slots=False, kw_only=True)
class Stream_info:
    _org_data: dict[str, Any] = field(default_factory=dict)

    index: int


@dataclass(slots=True, kw_only=True)
class Audio_info(Stream_info):
    sample_fmt: str = ""
    sample_rate: int = 0
    bits_per_sample: int = 0
    bits_per_raw_sample: int = 0


@dataclass(slots=True, kw_only=True)
class Video_info(Stream_info):
    width: int = 0
    height: int = 0

    nb_frames: int = 0
    """封装帧数 (f)"""

    r_frame_rate: tuple[int, int] = (0, 1)
    """基本帧率 (fps分数)"""

    duration: float = 0
    """时长 (s)"""


@dataclass(slots=True, kw_only=True)
class Subtitle_info(Stream_info):
    pass


@dataclass(slots=True, kw_only=True)
class Attachment_info(Stream_info):
    pass


@dataclass(slots=True, kw_only=True)
class Chapter_info:
    _org_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class Media_info:
    _org_streams: list[JsonObj]
    video: list[Video_info] = field(default_factory=list[Video_info])
    audio: list[Audio_info] = field(default_factory=list[Audio_info])
    subtitle: list[Stream_info] = field(default_factory=list[Stream_info])
    attachment: list[Attachment_info] = field(default_factory=list[Attachment_info])
    other_streams: list[Stream_info] = field(default_factory=list[Stream_info])
    chapter: list[Chapter_info] = field(default_factory=list[Chapter_info])

    @property
    def streams(self) -> list[Stream_info]:
        return sorted(
            itertools.chain(
                self.video,
                self.audio,
                self.subtitle,
                self.attachment,
                self.other_streams,
            ),
            key=lambda s: s.index,
        )

    @classmethod
    def from_path(cls, path: str | Path, /) -> Self:
        path = Path(path)
        _cmd = [
            "ffprobe",
            "-v",
            "0",
            "-show_streams",
            "-show_chapters",
            "-of",
            "json",
            path,
        ]
        log.debug(_cmd, print_level=log.LogLevel._detail)
        _info: dict = json.loads(
            subprocess.Popen(
                _cmd,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            ).communicate()[0]
        )
        streams = _info.get("streams", [])

        if not type_match(streams, list[JsonObj]):
            raise Stream_error("Streams type error: {}", obj_fmt(streams))

        media_info = cls(_org_streams=streams)

        for stream in streams:
            index = stream.get("index")
            if not isinstance(index, int):
                raise Stream_error(
                    "The key 'index' is not int in stream: {}",
                    obj_fmt(stream),
                )
            stream_info = Stream_info(_org_data=stream, index=index)

            match stream["codec_type"]:
                case "video":  # 视频轨
                    video_info = Video_info(**vars(stream_info))

                    video_info.width = int(cast("int", stream.get("width", 0)))
                    video_info.height = int(cast("int", stream.get("height", 0)))

                    _fps_str: str = str(stream.get("r_frame_rate", "0")) + "/1"
                    _fps = [int(s) for s in _fps_str.split("/")]
                    video_info.r_frame_rate = (_fps[0], _fps[1])

                    video_info.nb_frames = int(cast("int", stream.get("nb_frames", 0)))

                    if (_duration := stream.get("duration")) is None:
                        _duration = stream.get("tags")
                        if isinstance(_duration, dict):
                            _duration = str(_duration.get("DURATION", "0"))
                            _duration = time_str_to_sec(_duration)
                        else:
                            _duration = 0
                    else:
                        _duration = float(str(_duration))
                    video_info.duration = _duration

                    media_info.video.append(video_info)

                case "audio":  # 音频轨
                    ERROR_FMT = 'Failed to get audio info: {}. file "{}" track index {}'
                    sample_fmt = cast("str | None", stream.get("sample_fmt"))
                    if sample_fmt is None:
                        log.debug(ERROR_FMT, "sample_fmt", path, index)
                        sample_fmt = ""

                    sample_rate = cast("str | None", stream.get("sample_rate"))
                    if sample_rate is None:
                        log.debug(ERROR_FMT, "sample_rate", path, index)
                        sample_rate = 0

                    bits_per_sample = cast("int | None", stream.get("bits_per_sample"))
                    if bits_per_sample is None:
                        log.debug(ERROR_FMT, "bits_per_sample", path, index)
                        bits_per_sample = 0

                    bits_per_raw_sample = cast(
                        "str | None", stream.get("bits_per_raw_sample")
                    )
                    if bits_per_raw_sample is None:
                        log.debug(ERROR_FMT, "bits_per_raw_sample", path, index)
                        bits_per_raw_sample = 0

                    media_info.audio.append(
                        Audio_info(
                            **vars(stream_info),
                            sample_fmt=str(sample_fmt),
                            sample_rate=int(sample_rate),
                            bits_per_sample=int(bits_per_sample),
                            bits_per_raw_sample=int(bits_per_raw_sample),
                        )
                    )

                case "subtitle":
                    media_info.subtitle.append(Subtitle_info(**vars(stream_info)))

                case "attachment":
                    media_info.attachment.append(Attachment_info(**vars(stream_info)))

                case _:
                    media_info.other_streams.append(stream_info)

        del streams

        chapters = _info.get("chapters", [])

        if not type_match(chapters, list[JsonObj]):
            raise Stream_error("Chapters type error: {}", obj_fmt(chapters))

        for chapter in chapters:
            media_info.chapter.append(Chapter_info(_org_data=chapter))

        return media_info

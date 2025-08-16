from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess

from ..easyrip_log import log


@dataclass
class Audio_info:
    index: int
    sample_fmt: str = ""
    sample_rate: int = 0
    bits_per_sample: int = 0
    bits_per_raw_sample: int = 0


@dataclass
class Media_info:
    nb_frames: int = 0
    """封装帧数 (f)"""

    r_frame_rate: tuple[int, int] = (0, 1)
    """基本帧率 (fps分数)"""

    duration: float = 0
    """时长 (s)"""

    audio_info: list[Audio_info] = field(default_factory=list)


def get_media_info(path: str | Path) -> Media_info:
    path = Path(path)
    media_info = Media_info()

    # 第一个视频轨
    _info: dict = json.loads(
        subprocess.Popen(
            [
                "ffprobe",
                "-v",
                "0",
                "-select_streams",
                "v:0",
                "-show_streams",
                "-print_format",
                "json",
                path,
            ],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        ).communicate()[0]
    )
    _info_list: list = _info.get("streams", [])

    _video_info_dict: dict = _info_list[0] if _info_list else dict()

    _fps_str: str = _video_info_dict.get("r_frame_rate", "0") + "/1"
    _fps = [int(s) for s in _fps_str.split("/")]
    media_info.r_frame_rate = (_fps[0], _fps[1])

    media_info.nb_frames = int(_video_info_dict.get("nb_frames", 0))
    media_info.duration = float(_video_info_dict.get("duration", 0))

    # 遍历所有音频轨
    _info: dict = json.loads(
        subprocess.Popen(
            [
                "ffprobe",
                "-v",
                "0",
                "-select_streams",
                "a",
                "-show_streams",
                "-print_format",
                "json",
                path,
            ],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        ).communicate()[0]
    )
    _info_list: list = _info.get("streams", [])

    for _audio_info_dict in _info_list:
        if not isinstance(_audio_info_dict, dict):
            _audio_info_dict = dict()

        index = _audio_info_dict.get("index")
        if index is None:
            raise Exception()

        sample_fmt = _audio_info_dict.get("sample_fmt")
        if sample_fmt is None:
            log.debug(
                'Faild to get audio info: {}. file "{}" track index {}',
                "sample_fmt",
                path,
                index,
            )
            sample_fmt = ""

        sample_rate = _audio_info_dict.get("sample_rate")
        if sample_rate is None:
            log.debug(
                'Faild to get audio info: {}. file "{}" track index {}',
                "sample_rate",
                path,
                index,
            )
            sample_rate = 0

        bits_per_sample = _audio_info_dict.get("bits_per_sample")
        if bits_per_sample is None:
            log.debug(
                'Faild to get audio info: {}. file "{}" track index {}',
                "bits_per_sample",
                path,
                index,
            )
            bits_per_sample = 0

        bits_per_raw_sample = _audio_info_dict.get("bits_per_raw_sample")
        if bits_per_raw_sample is None:
            log.debug(
                'Faild to get audio info: {}. file "{}" track index {}',
                "bits_per_raw_sample",
                path,
                index,
            )
            bits_per_raw_sample = 0

        media_info.audio_info.append(
            Audio_info(
                index=int(index),
                sample_fmt=str(sample_fmt),
                sample_rate=int(sample_rate),
                bits_per_sample=int(bits_per_sample),
                bits_per_raw_sample=int(bits_per_raw_sample),
            )
        )

    return media_info

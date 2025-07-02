import json
from pathlib import Path
import subprocess

from ..easyrip_log import log


class Media_info:
    nb_frames: int
    """封装帧数 (f)"""
    r_frame_rate: tuple[int, int]
    """基本帧率 (fps分数)"""
    duration: float
    """时长 (s)"""
    sample_fmt: str
    sample_rate: int
    bits_per_sample: int
    bits_per_raw_sample: int

    def __init__(self):
        self.nb_frames = 0
        self.r_frame_rate = (0, 1)
        self.duration = 0
        self.sample_fmt = ""
        self.sample_rate = 0
        self.bits_per_sample = 0
        self.bits_per_raw_sample = 0


def get_media_info(path: str | Path) -> Media_info:
    path = Path(path)
    media_info = Media_info()

    try:
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

        # 第一个音频轨
        _info: dict = json.loads(
            subprocess.Popen(
                [
                    "ffprobe",
                    "-v",
                    "0",
                    "-select_streams",
                    "a:0",
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

        _audio_info_dict: dict = _info_list[0] if _info_list else dict()

        media_info.sample_fmt = str(_audio_info_dict.get("sample_fmt", ""))
        media_info.sample_rate = int(_audio_info_dict.get("sample_rate", 0))
        media_info.bits_per_sample = int(_audio_info_dict.get("bits_per_sample", 0))
        media_info.bits_per_raw_sample = int(
            _audio_info_dict.get("bits_per_raw_sample", 0)
        )

    except Exception as e:
        log.error(f"{repr(e)} {e}", deep=True, is_format=False)

    return media_info

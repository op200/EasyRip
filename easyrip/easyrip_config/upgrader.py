from pathlib import Path
from typing import ClassVar

from ..global_val import get_CONFIG_DIR


class upgrader:
    download_dir: ClassVar[Path]

    @classmethod
    def init(cls) -> None:
        cls.download_dir = get_CONFIG_DIR() / "downloads"
        cls.download_dir.mkdir(parents=True, exist_ok=True)

import re
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_VERSION_VAR_NAME = "PROJECT_VERSION"
GLOBAL_VAL_PY_FILE_PATH_STR = "easyrip/global_val.py"


def get_version():
    version_match = re.search(
        rf'{PROJECT_VERSION_VAR_NAME}\s*=\s*[\'"]([^\'"]*)[\'"]',
        Path(GLOBAL_VAL_PY_FILE_PATH_STR).read_text("utf-8"),
        re.M,
    )

    if version_match is None:
        raise RuntimeError(
            f"Cannot find '{PROJECT_VERSION_VAR_NAME}' in \"{GLOBAL_VAL_PY_FILE_PATH_STR}\""
        )

    return version_match.group(1) if version_match else "0.0.0"


setup(
    name="easyrip",
    version=get_version(),
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "pycryptodome>=3.21.0",
        "fonttools>=4.60.1",
    ],
    entry_points={
        "console_scripts": [
            "easyrip=easyrip.__main__:run",
        ],
    },
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
)

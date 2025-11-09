import re
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_VERSION_VAR_NAME = "PROJECT_VERSION"
GLOBAL_VAL_PY_FILE_PATH_STR = "easyrip/global_val.py"


def get_version():
    version_match = re.search(
        rf'{PROJECT_VERSION_VAR_NAME}\s*=\s*[\'"]([^\'"]*)[\'"]',
        Path(GLOBAL_VAL_PY_FILE_PATH_STR).read_text("utf-8"),
        re.MULTILINE,
    )

    assert version_match is not None, (
        f"Cannot find '{PROJECT_VERSION_VAR_NAME}' in \"{GLOBAL_VAL_PY_FILE_PATH_STR}\""
    )

    return version_match.group(1) if version_match else "0.0.0-dev"


setup(
    name="easyrip",
    version=get_version(),
    project_urls={
        "Repository": "https://github.com/op200/EasyRip",
    },
    classifiers=[
        "Topic :: Multimedia",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        # "Operating System :: MacOS",
        # "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Typing :: Typed",
    ],
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

from pathlib import Path
import re
from setuptools import setup, find_packages


def get_version():
    with open("easyrip/global_val.py", "r", encoding="utf-8") as f:
        version_match = re.search(
            r'PROJECT_VERSION\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.M
        )

    return version_match.group(1) if version_match else "0.0.0"


setup(
    name="easyrip",
    version=get_version(),
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "pycryptodome>=3.21.0",
        "fonttools>=4.58.4",
    ],
    entry_points={
        "console_scripts": [
            "easyrip=easyrip.__main__:run",
        ],
    },
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
)

import subprocess
import json

from global_val import GlobalVal
from . import http_server


PROJECT_RELEASE_API = GlobalVal.PROJECT_RELEASE_API


def get_sys_proxy(target_url: str) -> str | None:
    try:
        # PowerShell 命令：获取系统的代理设置
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                f'[System.Net.WebRequest]::GetSystemWebProxy().GetProxy("{target_url}")',
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except:  # noqa: E722
        pass

    url = None
    for line in result.stdout.split("\n"):
        if line.startswith("AbsoluteUri"):
            url = line.split(":", 1)[1].strip()
            break

    return url if url.rstrip("/") != target_url.rstrip("/") else None


def get_easyrip_ver() -> str | None:
    proxy = get_sys_proxy(PROJECT_RELEASE_API)

    cmd = f"curl --ssl-no-revoke{f' -x {proxy}' if proxy else ''} {PROJECT_RELEASE_API}"

    version = None
    try:
        response = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
        )
        data: dict = json.loads(response.stdout.decode("utf-8"))
        version = data.get("tag_name")
    except:  # noqa: E722
        pass

    return version


run_server = http_server.run_server

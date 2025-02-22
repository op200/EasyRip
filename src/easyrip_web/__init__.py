import subprocess
import json

from . import http_server


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
    target_url = "https://api.github.com/repos/op200/EasyRip/releases/latest"
    proxy = get_sys_proxy(target_url)

    cmd = f"curl --ssl-no-revoke{f" -x {proxy}" if proxy else ""} {target_url}"

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

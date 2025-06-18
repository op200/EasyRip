import subprocess
import json

from . import http_server


def get_sys_proxy(target_url: str) -> str:
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

        url = ""
        for line in result.stdout.split("\n"):
            if line.startswith("AbsoluteUri"):
                url = line.split(":", 1)[1].strip()
                break

        return url if url.rstrip("/") != target_url.rstrip("/") else ""

    except Exception:
        return ""


def get_github_api_ver(github_api_url: str) -> str | None:
    proxy = get_sys_proxy(github_api_url)

    cmd = f"curl --ssl-no-revoke{f' -x {proxy}' if proxy else ''} {github_api_url}"

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
    except Exception:
        pass

    return version


run_server = http_server.run_server

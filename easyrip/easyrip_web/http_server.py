import hashlib
import json
import os
import secrets
import signal
from collections import deque
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import sleep

from ..utils import AES

__all__ = ["run_server"]


class Event:
    log_queue: deque[tuple[str, str, str]] = deque()

    is_run_command: bool = False
    """用于防止 server 二次运行，以及告知客户端运行状态"""

    progress: deque[dict[str, int | float]] = deque([{}])

    @classmethod
    def post_run_event(cls, cmd: str) -> None:
        from ..easyrip_main import run_command

        try:
            run_command(cmd)
        finally:
            cls.is_run_command = False


class MainHTTPRequestHandler(BaseHTTPRequestHandler):
    token: str | None = None
    password: str | None = None
    password_sha3_512_last8: str | None = None
    aes_key: bytes | None = None

    @staticmethod
    def str_to_aes(text: str) -> str:
        return (
            text
            if MainHTTPRequestHandler.aes_key is None
            else AES.encrypt(text.encode("utf-8"), MainHTTPRequestHandler.aes_key).hex()
        )

    @staticmethod
    def aes_to_str(text: str) -> str:
        return (
            text.strip('"')
            if MainHTTPRequestHandler.aes_key is None
            else AES.decrypt(bytes.fromhex(text), MainHTTPRequestHandler.aes_key)
            .decode("utf-8")
            .strip('"')
        )

    def _send_cors_headers(self) -> None:
        """统一设置 CORS 头"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        # self.send_header("Access-Control-Allow-Credentials", "true")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self) -> None:
        from ..easyrip_log import log

        # 获取请求体的长度
        content_length = int(self.headers.get("Content-Length", 0))

        # 获取 Content-Type 请求头
        content_type = self.headers.get("Content-Type", "")

        # 从 Content-Type 中提取字符编码
        charset = (
            content_type.split("charset=")[-1].strip()
            if "charset=" in content_type
            else "utf-8"
        )

        # 读取请求体数据并使用指定的编码解码
        post_data = self.rfile.read(content_length).decode(charset)

        status_code: int
        header: tuple[str, str]
        response: str

        if MainHTTPRequestHandler.token is None:
            status_code = 500
            response = "Missing token in server"
            header = ("Content-type", "text/html")

        elif self.headers.get("Content-Type") == "application/json":
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                data: dict[str, str] = {}

            # 设置标志请求关闭服务
            if data.get("shutdown") == "shutdown":
                self.server.shutdown_requested = True  # pyright: ignore[reportAttributeAccessIssue]

            # 通过 token 判断一致性
            if (
                not (_token := data.get("token"))
                or _token != MainHTTPRequestHandler.token
            ):
                status_code = 401
                response = "Wrong token in client"
                header = ("Content-type", "text/html")

            # 验证密码
            elif MainHTTPRequestHandler.password is not None and (
                not (_password := data.get("password"))
                or _password != MainHTTPRequestHandler.password_sha3_512_last8
            ):
                status_code = 401
                response = "Wrong password"
                header = ("Content-type", "text/html")

            elif _cmd := data.get("run_command"):
                _cmd = MainHTTPRequestHandler.aes_to_str(_cmd)

                log.send(
                    _cmd,
                    is_server=True,
                    http_send_header=f"{os.path.realpath(os.getcwd())}>",
                )

                status_code = 200
                response = json.dumps({"res": "success"})
                header = ("Content-type", "application/json")

                if _cmd == "kill":
                    try:
                        os.kill(os.getpid(), signal.CTRL_C_EVENT)
                        while True:
                            sleep(1)
                    except KeyboardInterrupt:
                        log.error("Manually force exit")

                elif Event.is_run_command is True:
                    log.warning("There is a running command, terminate this request")

                elif Event.is_run_command is False:
                    if not MainHTTPRequestHandler.password and _cmd.startswith("$"):
                        _cmd = "$log.error('Prohibited from use $ <code> in web service when no password')"

                    post_run = Thread(
                        target=Event.post_run_event, args=(_cmd,), daemon=True
                    )
                    Event.is_run_command = True
                    post_run.start()

            elif data.get("clear_log_queue") == "clear":
                Event.log_queue.clear()
                status_code = 200
                response = json.dumps({"res": "success"})
                header = ("Content-type", "application/json")

            else:
                status_code = 406
                response = "Unknown requests"
                header = ("Content-type", "text/html")

        else:
            status_code = 400
            response = "Must send JSON"
            header = ("Content-type", "text/html")

        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header(*header)
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode(encoding="utf-8"))

    def do_GET(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "token": MainHTTPRequestHandler.token,
                    "cwd": MainHTTPRequestHandler.str_to_aes(
                        json.dumps(os.path.realpath(os.getcwd()))
                    ),
                    "log_queue": MainHTTPRequestHandler.str_to_aes(
                        json.dumps(list(Event.log_queue))
                    ),
                    "is_run_command": Event.is_run_command,
                    "progress": MainHTTPRequestHandler.str_to_aes(
                        json.dumps(Event.progress[-1])
                    ),
                }
            ).encode("utf-8")
        )


def run_server(
    host: str = "",
    port: int = 0,
    password: str | None = None,
    *,
    after_start_server_hook: Callable[[], None] = lambda: None,
) -> None:
    from ..easyrip_log import log

    MainHTTPRequestHandler.token = secrets.token_urlsafe(16)
    if password:
        MainHTTPRequestHandler.password = password
        _pw_sha3_512 = hashlib.sha3_512(MainHTTPRequestHandler.password.encode())
        MainHTTPRequestHandler.password_sha3_512_last8 = _pw_sha3_512.hexdigest()[-8:]
        MainHTTPRequestHandler.aes_key = _pw_sha3_512.digest()[:16]
    else:
        MainHTTPRequestHandler.password = None
        MainHTTPRequestHandler.password_sha3_512_last8 = None
        MainHTTPRequestHandler.aes_key = None

    server_address = (host, port)
    httpd = HTTPServer(server_address, MainHTTPRequestHandler)

    protocol = "HTTP"

    def _hook() -> None:
        try:
            after_start_server_hook()
        finally:
            Event.is_run_command = False

    Event.is_run_command = True
    Thread(target=_hook, daemon=True).start()

    log.info(
        "Starting {protocol} service on port {port}...",
        protocol=protocol,
        port=httpd.server_port,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("{} service stopped by ^C", protocol)

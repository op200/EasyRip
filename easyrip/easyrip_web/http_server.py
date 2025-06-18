from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from threading import Thread
import secrets
import hashlib
from collections import deque
import os
import signal
from time import sleep

from Crypto.Cipher import AES as CryptoAES
from Crypto.Util.Padding import pad, unpad


__all__ = ["Event", "run_server"]


class AES:
    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> bytes:
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC)  # 使用 CBC 模式
        ciphertext = cipher.encrypt(pad(plaintext, CryptoAES.block_size))  # 加密并填充
        return bytes(cipher.iv) + ciphertext  # 返回 IV 和密文

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes) -> bytes:
        iv = ciphertext[:16]  # 提取 IV
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC, iv=iv)
        plaintext = unpad(
            cipher.decrypt(ciphertext[16:]), CryptoAES.block_size
        )  # 解密并去除填充
        return plaintext


class Event:
    log_queue: deque[tuple[str, str, str]] = deque()
    is_run_command: deque[bool] = deque([False])
    """
    用于防止 server 二次运行，以及告知客户端运行状态
    """
    progress: deque[dict] = deque([{}])

    class log:
        @staticmethod
        def info(message: object, *vals):
            pass

        @staticmethod
        def warning(message: object, *vals):
            pass

        @staticmethod
        def error(message: object, *vals):
            pass

        @staticmethod
        def send(
            header: str,
            message: object,
            *vals,
            is_format: bool = True,
            is_server: bool = False,
        ):
            pass

    @staticmethod
    def post_run_event(cmd: str):
        pass


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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
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
                self.server.shutdown_requested = True  # type: ignore

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

                Event.log.send(
                    f"{os.path.realpath(os.getcwd())}>", _cmd, is_server=True
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
                        Event.log.error("Manually force exit")
                        # Event.is_run_command.append(False)
                        # Event.is_run_command.popleft()
                        # sleep(1)
                        # Event.progress.append({})
                        # Event.progress.popleft()

                elif Event.is_run_command[-1] is True:
                    Event.log.warning(
                        "There is a running command, terminate this request"
                    )

                elif Event.is_run_command[-1] is False:
                    if not MainHTTPRequestHandler.password and _cmd.startswith("$"):
                        _cmd = "$log.error('Prohibited from use $ <code> in web service when no password')"

                    post_run = Thread(
                        target=Event.post_run_event, args=(_cmd,), daemon=True
                    )
                    Event.is_run_command.append(True)
                    Event.is_run_command.popleft()
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(*header)
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode(encoding="utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
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
                    "is_run_command": Event.is_run_command[-1],
                    "progress": MainHTTPRequestHandler.str_to_aes(
                        json.dumps(Event.progress[-1])
                    ),
                }
            ).encode("utf-8")
        )


def run_server(host: str = "", port: int = 0, password: str | None = None):
    MainHTTPRequestHandler.token = secrets.token_urlsafe(16)
    if password:
        MainHTTPRequestHandler.password = password
        _pw_sha3_512 = hashlib.sha3_512(MainHTTPRequestHandler.password.encode())
        MainHTTPRequestHandler.password_sha3_512_last8 = _pw_sha3_512.hexdigest()[-8:]
        MainHTTPRequestHandler.aes_key = _pw_sha3_512.digest()[:16]

    server_address = (host, port)
    httpd = HTTPServer(server_address, MainHTTPRequestHandler)
    Event.log.info("Starting HTTP service on port {}...", httpd.server_port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        Event.log.info("HTTP service stopped by ^C")

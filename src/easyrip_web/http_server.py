from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from threading import Thread
import secrets
import hashlib
from collections import deque

from Crypto.Cipher import AES as CryptoAES
from Crypto.Util.Padding import pad, unpad


__all__ = ["Event", "run_server"]


class AES:
    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> bytes:
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC)  # 使用 CBC 模式
        ciphertext = cipher.encrypt(pad(plaintext, CryptoAES.block_size))  # 加密并填充
        return cipher.iv + ciphertext  # 返回 IV 和密文

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes) -> bytes:
        iv = ciphertext[:16]  # 提取 IV
        cipher = CryptoAES.new(key, CryptoAES.MODE_CBC, iv=iv)
        plaintext = unpad(
            cipher.decrypt(ciphertext[16:]), CryptoAES.block_size
        )  # 解密并去除填充
        return plaintext


class Event:
    log_queue: deque = deque()
    is_run_command: bool = False

    class log:
        @staticmethod
        def info(message, *vals):
            print(message, *vals)

    def post_event(data: dict):
        pass


class MainHTTPRequestHandler(BaseHTTPRequestHandler):
    token: str | None = None
    password: str | None = None
    password_sha3_512_last8: str | None = None
    aes_key: bytes | None = None

    @staticmethod
    def str_to_aes_hex(text: str) -> str | None:
        if MainHTTPRequestHandler.aes_key is None:
            return None
        return AES.encrypt(text.encode("utf-8"), MainHTTPRequestHandler.aes_key).hex()

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

        if MainHTTPRequestHandler.token is None:
            self.send_response(500)
            response = "Missing token in server"
            self.send_header("Content-type", "text/html")

        elif self.headers.get("Content-Type") == "application/json":
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                data = {}

            # 设置标志请求关闭服务器
            if data.get("shutdown") == "true":
                self.server.shutdown_requested = True

            # 通过 token 判断一致性
            if (
                not (_token := data.get("token"))
                or _token != MainHTTPRequestHandler.token
            ):
                self.send_response(401)
                response = "Wrong token in client"
                self.send_header("Content-type", "text/html")

            # 验证密码加密后的正确性
            elif MainHTTPRequestHandler.password is not None and (
                not (
                    _password := data.get(
                        MainHTTPRequestHandler.str_to_aes_hex("password")
                    )
                )
                or _password != MainHTTPRequestHandler.password_sha3_512_last8
            ):
                self.send_response(401)
                response = "Wrong password"
                self.send_header("Content-type", "text/html")

            elif _cmd := data.get("run_command"):
                if Event.is_run_command is False:
                    _cmd = AES.decrypt(
                        bytes.fromhex(_cmd), MainHTTPRequestHandler.aes_key
                    ).decode("utf-8")
                    Thread(
                        target=Event.post_event,
                        args=(
                            "$log.error('Prohibited from use $ <code> in web service')"
                            if _cmd.startswith("$")
                            else _cmd,
                        ),
                    ).start()
                    Event.is_run_command = True

                    self.send_response(200)
                    response = json.dumps({"res": "true"})
                    self.send_header("Content-type", "application/json")

            elif data.get("clear_log_queue") == "true":
                Event.log_queue.clear()
                self.send_response(200)
                response = json.dumps({"res": "true"})
                self.send_header("Content-type", "application/json")

            else:
                self.send_response(406)
                response = "Unknown requests"
                self.send_header("Content-type", "text/html")

        else:
            self.send_response(400)
            response = "Must send JSON"
            self.send_header("Content-type", "text/html")

        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode(encoding="utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        s = MainHTTPRequestHandler.str_to_aes_hex(json.dumps([1, "asd", "zh驱蚊扣"]))
        msg = json.dumps(
            {
                "token": MainHTTPRequestHandler.token,
                "log_queue": MainHTTPRequestHandler.str_to_aes_hex(
                    json.dumps(list(Event.log_queue))
                ),
                "is_run_command": Event.is_run_command,
                "test": s,
            }
        ).encode("utf-8")
        print(f"msg: {msg.decode('utf-8')}")
        print(
            f"test: {json.loads(msg.decode('utf-8'))['test']}"
        )
        print(
            f"test decode: {AES.decrypt(bytes.fromhex(json.loads(msg.decode('utf-8'))['test']), MainHTTPRequestHandler.aes_key)}"
        )
        print(f"key: {MainHTTPRequestHandler.aes_key.hex()}")
        # print(f"msg.en: {msg.encode('utf-8')}")
        self.wfile.write(msg)

        # test
        # en = MainHTTPRequestHandler.str_to_aes_hex(json.dumps([1, "asd", "zh驱蚊扣"]))
        # print(f"en: {en}")
        # de = AES.decrypt(bytes.fromhex(en), MainHTTPRequestHandler.aes_key).decode(
        #     "utf-8"
        # )
        # print(f"de: {de}")


def run_server(host: str = "", port: int = 0, password: str | None = None):
    MainHTTPRequestHandler.token = secrets.token_urlsafe(16)
    if password:
        MainHTTPRequestHandler.password = password
        _pw_sha3_512 = hashlib.sha3_512(MainHTTPRequestHandler.password.encode())
        MainHTTPRequestHandler.password_sha3_512_last8 = _pw_sha3_512.hexdigest()[-8]
        MainHTTPRequestHandler.aes_key = _pw_sha3_512.digest()[:16]
        print("@@@", MainHTTPRequestHandler.aes_key.hex())

    server_address = (host, port)
    httpd = HTTPServer(server_address, MainHTTPRequestHandler)
    Event.log.info("Starting HTTP service on port {}...", httpd.server_port)
    httpd.serve_forever()

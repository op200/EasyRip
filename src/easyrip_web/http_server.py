from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from threading import Thread
import secrets
import hashlib


__all__ = ["Event", "run_server"]


class Event:
    log_queue: list = []
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

            if (
                not (_token := data.get("token"))
                or _token != MainHTTPRequestHandler.token
            ):
                self.send_response(401)
                response = "Wrong token in client"
                self.send_header("Content-type", "text/html")

            elif MainHTTPRequestHandler.password is not None and (
                not (_password := data.get("password"))
                or _password
                != hashlib.sha256(MainHTTPRequestHandler.password.encode()).hexdigest()
            ):
                self.send_response(401)
                response = "Wrong password"
                self.send_header("Content-type", "text/html")

            elif data.get("run_command"):
                if Event.is_run_command is False:
                    Thread(target=Event.post_event, args=(data["run_command"],)).start()
                    Event.is_run_command = True

                    self.send_response(200)
                    response = json.dumps({"res": "true"})
                    self.send_header("Content-type", "application/json")

            elif data.get("clear_log_queue") == "true":
                Event.log_queue = []
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
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "token": MainHTTPRequestHandler.token,
                    "log_queue": Event.log_queue,
                    "is_run_command": Event.is_run_command,
                }
            ).encode("utf-8")
        )


def run_server(host: str = "", port: int = 0, password: str | None = None):
    MainHTTPRequestHandler.token = secrets.token_urlsafe(16)
    MainHTTPRequestHandler.password = password

    server_address = (host, port)
    httpd = HTTPServer(server_address, MainHTTPRequestHandler)
    Event.log.info("Starting HTTP server on port {}...", httpd.server_port)
    httpd.serve_forever()

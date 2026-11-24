# 熬鹰监控 · 币安接口中转 (Hugging Face Spaces 版, 替代 Deno Deploy)
# 仅允许币安官方域名, 防止被滥用
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request

ALLOW = [
    "www.binance.com",
    "www.binance.info",
    "www.binancezh.com",
    "www.binancezh.top",
]

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "clienttype": "web",
    "lang": "zh-CN",
    "Referer": "https://www.binance.com/zh-CN/copy-trading",
    "Origin": "https://www.binance.com",
}

PORT = int(os.environ.get("PORT", 7860))


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        target = qs.get("url", [None])[0]
        if not target:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("aoying relay OK (HF Space)\n".encode())
            return
        self._proxy(target)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        target = qs.get("url", [None])[0]
        if not target:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"missing ?url=")
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self._proxy(target, body)

    def _proxy(self, target, body=None):
        try:
            host = urllib.parse.urlparse(target).hostname
            if host not in ALLOW:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"host not allowed")
                return
            req = urllib.request.Request(target, data=body, headers=HEADERS, method="POST")
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type",
                                 resp.headers.get("Content-Type") or "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type",
                             e.headers.get("Content-Type") or "text/plain")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(("relay error: " + str(e)).encode())

    def log_message(self, fmt, *args):
        pass  # 静音访问日志


if __name__ == "__main__":
    print("relay listening on port", PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

# -*- coding: utf-8 -*-
"""
================================================================================
عميل Chrome DevTools Protocol مصغّر (بلا مكتبات خارجية)
--------------------------------------------------------------------------------
يوفّر طباعة PDF موثوقة: ينتظر تحميل الصفحة وجاهزية الخطوط (document.fonts.ready)
قبل إصدار أمر الطباعة — وهو ما يضمن تضمين الخطوط في الملف النهائي.

مرجع: https://chromedevtools.github.io/devtools-protocol/
================================================================================
"""

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request


class WebSocket:
    """عميل WebSocket نصّي الحد الأدنى (RFC 6455) — كافٍ لطلبات CDP."""

    def __init__(self, url, timeout=30):
        assert url.startswith("ws://")
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self.path = "/" + path
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {hostport}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("فشل مصافحة WebSocket")
            buf += chunk
        self.buf = buf.split(b"\r\n\r\n", 1)[1]

    # ---------------- الإرسال ----------------
    def _send_frame(self, payload: bytes):
        header = bytearray([0x81])  # FIN + text
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def send(self, method, params=None, msg_id=None):
        msg = {"id": msg_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._send_frame(json.dumps(msg).encode())

    # ---------------- الاستقبال ----------------
    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("انقطع الاتصال")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def recv(self):
        while True:
            b0, b1 = self._read(2)
            opcode = b0 & 0x0F
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read(8))[0]
            masked = b1 & 0x80
            mask = self._read(4) if masked else None
            payload = self._read(length)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            if opcode == 0x8:
                raise ConnectionError("أغلق الخادم الاتصال")
            if opcode == 0x9:  # ping
                self.sock.sendall(b"\x8a\x80" + os.urandom(4))
                continue
            if opcode in (0x1, 0x2):
                return json.loads(payload.decode("utf-8"))

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Chrome:
    """يشغّل Chrome بلا واجهة ويتيح الطباعة عبر CDP."""

    def __init__(self, chrome_path, port=None):
        self.chrome = chrome_path
        self.port = port or _free_port()
        self.profile = tempfile.mkdtemp(prefix="cdp-profile-")
        self.proc = None

    def __enter__(self):
        cmd = [
            self.chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--disable-background-networking",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.profile}",
            "about:blank",
        ]
        self.log = open(os.path.join(self.profile, "chrome.log"), "w+b")
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self._wait_ready()
        return self

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)

    def _wait_ready(self, timeout=30):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=2) as r:
                    r.read()
                return True
            except Exception as e:
                last = e
                if self.proc.poll() is not None:
                    break
                time.sleep(0.25)
        log = ""
        try:
            self.log.seek(0)
            log = self.log.read().decode("utf-8", "ignore")[-600:]
        except Exception:
            pass
        raise RuntimeError(f"تعذّر تشغيل Chrome: {last}\n{log}")

    def new_page(self, url):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/json/new?{url}",
            method="PUT")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())

    def print_pdf(self, url, dest, wait_ms=1200, timeout=180):
        """يطبع رابطًا إلى PDF بعد انتظار جاهزية الصفحة والخطوط."""
        target = self.new_page("about:blank")
        ws = WebSocket(target["webSocketDebuggerUrl"])
        try:
            ws.send("Page.enable", {}, msg_id=1)
            ws.send("Runtime.enable", {}, msg_id=2)
            ws.send("Page.navigate", {"url": url}, msg_id=3)

            loaded = False
            deadline = time.time() + timeout
            while time.time() < deadline:
                msg = ws.recv()
                if msg.get("method") == "Page.loadEventFired":
                    loaded = True
                    break
            if not loaded:
                raise TimeoutError("لم يكتمل تحميل الصفحة")

            # انتظار الخطوط ثم estabilidade
            time.sleep(wait_ms / 1000)
            ws.send("Runtime.evaluate", {
                "expression": "document.fonts.ready.then(()=>1)",
                "awaitPromise": True, "returnByValue": True}, msg_id=4)
            fonts_ok = False
            deadline = time.time() + 30
            while time.time() < deadline:
                msg = ws.recv()
                if msg.get("id") == 4:
                    fonts_ok = True
                    break
            time.sleep(0.4)

            ws.send("Page.printToPDF", {
                "printBackground": True,
                "preferCSSPageSize": True,
                "displayHeaderFooter": False,
                "marginTop": 0, "marginBottom": 0,
                "marginLeft": 0, "marginRight": 0,
            }, msg_id=5)

            data = None
            deadline = time.time() + timeout
            while time.time() < deadline:
                msg = ws.recv()
                if msg.get("id") == 5:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    data = msg["result"]["data"]
                    break
            if not data:
                raise TimeoutError("لم تصل نتيجة الطباعة")

            with open(dest, "wb") as f:
                f.write(base64.b64decode(data))
            return True
        finally:
            ws.close()
            try:
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"http://127.0.0.1:{self.port}/json/close/{target['id']}", method="GET"),
                    timeout=5).read()
            except Exception:
                pass


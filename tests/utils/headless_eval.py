#!/usr/bin/env python3
"""
Headless Chrome Evaluation Harness for Dar Al-Khashab Feasibility.

This module provides an automated, zero-dependency Chrome DevTools Protocol (CDP)
driver for opaque-box browser testing, lifecycle evaluation, responsive viewports,
console log interception, and interactive DOM manipulation.

Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
"""

import atexit
import base64
import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Root directory of the feasibility project
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

# Chrome candidates
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]


def find_chrome_binary() -> Optional[str]:
    """Find local Chrome or Chromium executable."""
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    return None


def get_free_port() -> int:
    """Find an available OS-assigned TCP port."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class EphemeralServer:
    """Threaded HTTP server serving static project files."""

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    def __init__(self, directory: Path, port: Optional[int] = None):
        self.directory = directory
        self.port = port or get_free_port()
        handler = lambda *a, **k: self.QuietHandler(*a, directory=str(self.directory), **k)
        self.server = self.Server(("127.0.0.1", self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception:
            pass


class HeadlessSession:
    """Headless Chrome CDP test driver."""

    def __init__(self, chrome_path: Optional[str] = None):
        self.chrome_path = chrome_path or find_chrome_binary()
        if not self.chrome_path:
            raise RuntimeError("Chrome binary not found on system.")

        self.port = get_free_port()
        self.profile_dir = tempfile.mkdtemp(prefix="cdp-test-profile-")
        self.proc: Optional[subprocess.Popen] = None
        self.log_file = None
        self.server: Optional[EphemeralServer] = None
        self.ws = None
        self.target_id: Optional[str] = None
        self.msg_id_counter = 1
        self.console_messages: List[Dict[str, Any]] = []
        self.network_requests: List[str] = []
        self._connected = False

    def start(self):
        """Start local HTTP server and launch Chrome."""
        self.server = EphemeralServer(WORKSPACE_ROOT)
        self.server.start()

        cmd = [
            self.chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.profile_dir}",
            "about:blank",
        ]
        self.log_file = open(os.path.join(self.profile_dir, "chrome.log"), "w+b")
        self.proc = subprocess.Popen(cmd, stdout=self.log_file, stderr=subprocess.STDOUT)
        self._wait_ready(timeout=15)
        self._attach_cdp()
        self._connected = True

    def _wait_ready(self, timeout: float = 15.0):
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=2) as r:
                    r.read()
                return True
            except Exception as e:
                last_err = e
                if self.proc and self.proc.poll() is not None:
                    break
                time.sleep(0.2)
        raise RuntimeError(f"Failed to start Chrome: {last_err}")

    def _attach_cdp(self):
        """Create new page target and establish WebSocket connection."""
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/json/new?about:blank", method="PUT")
        with urllib.request.urlopen(req, timeout=10) as r:
            target = json.loads(r.read().decode())

        self.target_id = target["id"]
        ws_url = target["webSocketDebuggerUrl"]

        # Import WebSocket from tools/cdp.py
        sys.path.insert(0, str(WORKSPACE_ROOT / "tools"))
        from cdp import WebSocket  # noqa: E402
        self.ws = WebSocket(ws_url, timeout=30)

        # Enable domains
        self.send_cdp("Page.enable", {})
        self.send_cdp("Runtime.enable", {})
        self.send_cdp("Console.enable", {})
        self.send_cdp("Network.enable", {})

    def send_cdp(self, method: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Send CDP command and return message ID."""
        msg_id = self.msg_id_counter
        self.msg_id_counter += 1
        self.ws.send(method, params or {}, msg_id=msg_id)
        return msg_id

    def recv_until(self, target_id: Optional[int] = None, timeout: float = 15.0) -> Optional[Dict[str, Any]]:
        """Receive CDP messages until specific message ID or condition."""
        deadline = time.time() + timeout
        result_msg = None
        while time.time() < deadline:
            try:
                msg = self.ws.recv()
            except Exception:
                break
            if not msg:
                continue

            method = msg.get("method")
            if method == "Console.messageAdded":
                self.console_messages.append(msg.get("params", {}).get("message", {}))
            elif method == "Runtime.exceptionThrown":
                self.console_messages.append({
                    "level": "error",
                    "text": str(msg.get("params", {}).get("exceptionDetails", {})),
                })
            elif method == "Network.requestWillBeSent":
                req_url = msg.get("params", {}).get("request", {}).get("url", "")
                if req_url:
                    self.network_requests.append(req_url)

            if target_id is not None and msg.get("id") == target_id:
                result_msg = msg
                break
        return result_msg

    def navigate(self, relative_path: str = "index.html", timeout: float = 15.0) -> bool:
        """Navigate to relative path or file URL."""
        if relative_path.startswith("file://") or relative_path.startswith("http://"):
            url = relative_path
        else:
            url = f"http://127.0.0.1:{self.server.port}/{relative_path.lstrip('/')}"

        msg_id = self.send_cdp("Page.navigate", {"url": url})
        deadline = time.time() + timeout
        loaded = False
        while time.time() < deadline:
            msg = self.recv_until(target_id=None, timeout=1.0)
            if msg and msg.get("method") == "Page.loadEventFired":
                loaded = True
                break
            # Also poll data-ready attribute
            res = self.evaluate("document.documentElement.getAttribute('data-ready')")
            if res == "1" or res == "error":
                loaded = True
                break
            time.sleep(0.1)

        time.sleep(0.3)
        return loaded

    def evaluate(self, expression: str, timeout: float = 10.0) -> Any:
        """Evaluate JavaScript expression and return Python native value."""
        msg_id = self.send_cdp(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
        )
        msg = self.recv_until(target_id=msg_id, timeout=timeout)
        if not msg:
            return None
        result = msg.get("result", {})
        if "exceptionDetails" in result:
            err = result["exceptionDetails"].get("text", "JS Exception")
            raise RuntimeError(f"JavaScript evaluation error: {err}")
        return result.get("result", {}).get("value")

    def click(self, selector: str) -> bool:
        """Simulate click on selector via JavaScript."""
        script = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.click();
            return true;
        }})()
        """
        return bool(self.evaluate(script))

    def set_value(self, selector: str, value: Any) -> bool:
        """Set value of input slider and dispatch input/change events."""
        script = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return false;
            el.value = {json.dumps(value)};
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }})()
        """
        return bool(self.evaluate(script))

    def set_viewport(self, width: int, height: int, mobile: bool = False):
        """Set device viewport dimensions."""
        self.send_cdp(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": mobile,
            },
        )
        time.sleep(0.2)

    def get_console_errors(self) -> List[Dict[str, Any]]:
        """Return captured console errors and exceptions."""
        errors = []
        for m in self.console_messages:
            level = m.get("level", "")
            if level in {"error", "assert"}:
                errors.append(m)
        return errors

    def get_network_leakages(self) -> List[str]:
        """Return any network requests made to external hosts (non-localhost)."""
        leakages = []
        for url in self.network_requests:
            if not (url.startswith("http://127.0.0.1") or url.startswith("http://localhost") or url.startswith("data:")):
                leakages.append(url)
        return leakages

    def close(self):
        """Clean up CDP WebSocket, Chrome process, and temp profile."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        if self.server:
            self.server.stop()
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
        shutil.rmtree(self.profile_dir, ignore_errors=True)
        self._connected = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Shared singleton session for rapid test execution across multiple test cases
_SHARED_SESSION: Optional[HeadlessSession] = None
_SHARED_LOCK = threading.Lock()


def get_shared_session() -> Optional[HeadlessSession]:
    """Retrieve or initialize the shared headless browser session."""
    global _SHARED_SESSION
    with _SHARED_LOCK:
        if _SHARED_SESSION is None or not _SHARED_SESSION._connected:
            try:
                session = HeadlessSession()
                session.start()
                _SHARED_SESSION = session
            except Exception as e:
                print(f"[headless_eval] Warning: Headless Chrome unavailable ({e}). Fallback to static.")
                _SHARED_SESSION = None
        return _SHARED_SESSION


def shutdown_shared_session():
    """Tear down shared headless browser session on exit."""
    global _SHARED_SESSION
    with _SHARED_LOCK:
        if _SHARED_SESSION:
            try:
                _SHARED_SESSION.close()
            except Exception:
                pass
            _SHARED_SESSION = None


atexit.register(shutdown_shared_session)


if __name__ == "__main__":
    chrome = find_chrome_binary()
    print("Found Chrome:", chrome)
    if chrome:
        with HeadlessSession(chrome) as s:
            s.navigate("index.html")
            ready = s.evaluate("document.documentElement.getAttribute('data-ready')")
            print("Evaluated data-ready:", ready)
            title = s.evaluate("document.title")
            print("Evaluated title:", title)

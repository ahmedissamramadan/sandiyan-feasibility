#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
استخراج وثائق PDF من القالب
--------------------------------------------------------------------------------
  python3 tools/export_pdf.py                 # القالبان (عربي + إنجليزي)
  python3 tools/export_pdf.py --docs          # مستندات المولّد أيضًا
  python3 tools/export_pdf.py --lang en

يشغّل خادمًا محليًّا مؤقتًا ثم يطبع عبر Chrome DevTools Protocol، بعد انتظار
تحميل الصفحة **وجاهزية الخطوط** (document.fonts.ready) — فتكون الخطوط مضمّنة
في الملف النهائي. بلا أي مكتبة خارجية.
================================================================================
"""

import argparse
import http.server
import re
import shutil
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    return None


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(directory, port):
    handler = lambda *a, **k: QuietHandler(*a, directory=str(directory), **k)
    srv = Server(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page_count(pdf: Path):
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def embedded_fonts(pdf: Path):
    raw = pdf.read_bytes()
    return sorted(set(x.decode() for x in re.findall(rb"/BaseFont\s*/([A-Za-z0-9+#,\-]+)", raw)))


def main():
    ap = argparse.ArgumentParser(description="استخراج PDF من قالب دراسة الجدوى")
    ap.add_argument("--lang", choices=["ar", "en", "both"], default="both")
    ap.add_argument("--docs", action="store_true", help="تصدير مستندات المولّد أيضًا")
    args = ap.parse_args()

    chrome = find_chrome()
    if not chrome:
        sys.exit("لم يُعثر على Chrome/Chromium — ثبّت المتصفح أو صدّر PDF من داخل القالب (Ctrl+P).")

    port = free_port()
    srv = start_server(ROOT, port)
    base = f"http://127.0.0.1:{port}"
    langs = ["ar", "en"] if args.lang == "both" else [args.lang]

    jobs = []
    for lg in langs:
        if lg == "ar":
            jobs.append((f"{base}/index.html?theme=light",
                         ROOT / "out" / "feasibility-ar.pdf", "القالب العربي"))
        else:
            jobs.append((f"{base}/en/index.html?theme=light",
                         ROOT / "out" / "en" / "feasibility-en.pdf", "English template"))

    if args.docs:
        for lg in langs:
            folder = ROOT / "out" if lg == "ar" else ROOT / "out" / "en"
            for html in sorted(folder.glob("*.html")):
                rel = html.relative_to(ROOT).as_posix()
                jobs.append((f"{base}/{rel}", html.with_suffix(".pdf"), html.stem))

    print(f"→ تصدير {len(jobs)} ملف PDF عبر {Path(chrome).name}")
    ok = 0
    with Chrome(chrome) as ch:
        for url, dest, label in jobs:
            dest.parent.mkdir(parents=True, exist_ok=True)
            done = False
            for attempt in (1, 2, 3):
                try:
                    ch.print_pdf(url, dest)
                    done = True
                    break
                except Exception as e:
                    err = e
                    time.sleep(1.2 * attempt)
            if done:
                pages = page_count(dest)
                fonts = [f for f in embedded_fonts(dest) if "Plex" in f]
                size_kb = dest.stat().st_size // 1024
                print(f"   ✓ {label:24} → {dest.relative_to(ROOT)}  ({pages} صفحة · {size_kb}KB · {len(fonts)} خط مضمَّن)")
                ok += 1
            else:
                print(f"   ✗ {label}: {err}")

    srv.shutdown()
    print(f"\nتمّ: {ok}/{len(jobs)} ملف")


if __name__ == "__main__":
    main()

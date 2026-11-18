#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
بناء نسخة مستقلة في ملف واحد (standalone HTML)
--------------------------------------------------------------------------------
  python3 tools/build_standalone.py

يُنتج out/feasibility-standalone.html — ملف واحد يحتوي:
  · كل صفحات CSS مدمجة
  · الخطوط محمّلة كـ base64 داخل الملف (بلا أي طلب خارجي)
  · كل ملفات JS مدمجة بالترتيب الصحيح
  · طبقتا البيانات (العربية + الإنجليزية) مدمجتان
النتيجة: ملف يُرسل لأي شخص ويفتح مباشرة بلا خادم وبلا إنترنت،
مع بقاء كل التفاعلات: المحرك المالي الحيّ، الرسوم، التحرير، التصدير،
تبديل اللغة والسمة والأرقام، والطباعة إلى PDF.
================================================================================
"""

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "feasibility-standalone.html"

CSS_FILES = ["tokens", "base", "layout", "components", "charts", "ltr", "print"]
JS_FILES = ["i18n", "i18n-num", "store", "finance", "charts", "tables", "toc", "render", "app"]
DATA_FILES = [("assets/data/project.js", "__PROJECT__"),
              ("assets/data/project-en.js", "__PROJECT_EN__")]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def inline_fonts() -> str:
    """يحوّل ملفات الخطوط إلى base64 داخل قاعدة @font-face."""
    css = read(ROOT / "assets" / "css" / "fonts.css")
    d = ROOT / "assets" / "fonts"

    def repl(m):
        name = m.group(1)
        f = d / name
        if not f.exists():
            return m.group(0)
        b64 = base64.b64encode(f.read_bytes()).decode()
        return "src: url(data:font/woff2;base64,%s) format('woff2');" % b64

    out = re.sub(r"src: url\('\.\./fonts/([^']+)'\) format\('woff2'\);", repl, css)
    # الخطوط مستقلة داخل الملف الواحد: المسار النسبي غير لازم
    return out


def build() -> str:
    html = read(ROOT / "index.html")

    # ---------- 1) الأنماط ----------
    css_parts = ["/* ================= الأنماط المدمجة ================= */"]
    for name in CSS_FILES:
        css_parts.append(f"\n/* ---- {name}.css ---- */\n" + read(ROOT / "assets" / "css" / f"{name}.css"))
    css_parts.append("\n/* ---- fonts.css (مضمّنة base64) ---- */\n" + inline_fonts())
    merged_css = "\n".join(css_parts)

    html = re.sub(
        r'<link rel="stylesheet" href="assets/css/fonts\.css">',
        "<style id=\"fs-fonts\">\n%s\n</style>" % inline_fonts(),
        html,
    )
    html = re.sub(
        r'<link rel="stylesheet" href="assets/css/[a-z]+\.css">',
        "",
        html,
    )
    html = html.replace(
        "</head>",
        "<style id=\"fs-all\">\n%s\n</style>\n</head>" % merged_css,
        1,
    )

    # ---------- 2) الخطوط المسبقة: غير لازمة داخل ملف واحد ----------
    html = re.sub(r'<link rel="preload"[^>]*>\n?', "", html)
    html = re.sub(r'<link rel="preconnect"[^>]*>\n?', "", html)
    html = re.sub(r'<noscript>[\s\S]*?</noscript>\n?', "", html)

    # ---------- 3) البيانات ----------
    for path, var in DATA_FILES:
        js = read(ROOT / path)
        js = js.replace("</script>", "<\\/script>")
        html = html.replace(
            f'<script src="{path}"></script>',
            "<script>/* %s */\n%s</script>" % (path, js),
        )

    # ---------- 4) الشيفرة ----------
    for name in JS_FILES:
        js = read(ROOT / "assets" / "js" / f"{name}.js")
        js = js.replace("</script>", "<\\/script>")
        html = html.replace(
            f'<script src="assets/js/{name}.js"></script>',
            "<script>/* ---- %s.js ---- */\n%s</script>" % (name, js),
        )

    # ---------- 5) متغيّرات الملف الواحد ----------
    html = html.replace(
        '<script>window.__ASSET_BASE__ = "assets/";</script>',
        '<script>window.__ASSET_BASE__ = ""; window.__STANDALONE__ = true;</script>',
    )

    # ---------- 6) وسوم وصفية لملف واحد ----------
    html = html.replace(
        '<link rel="stylesheet" href="../assets/css/fonts.css">',
        "",
    )
    html = html.replace(
        '<meta name="description" content="قالب دراسة جدوى عربي RTL لمشروع تجارة إلكترونية قائم على ورشة نجارة، بطبقة ذكاء اصطناعي ومحرك مالي حيّ.">',
        '<meta name="description" content="Feasibility study template — Arabic (RTL) and English (LTR), e-commerce project built on an existing carpentry workshop, with an AI agent layer and a live financial engine. Fully self-contained single file.">',
    )

    # رسالة عند تعطيل JavaScript
    html = html.replace(
        "<body>",
        "<body>\n<noscript><div style=\"padding:2rem;font-family:system-ui;text-align:center\">"
        "هذا المستند تفاعلي ويحتاج JavaScript للعمل (المحرك المالي والرسوم والتحرير).</div></noscript>",
        1,
    )

    return html


def main():
    html = build()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(html, encoding="utf-8")

    kb = len(html.encode("utf-8")) // 1024
    # تحقّق: لا مراجع خارجية متبقية
    external = re.findall(r'(?:src|href)="(?!#|data:)([^"]+)"', html)
    external = [u for u in external if not u.startswith("mailto:")]
    print(f"✓ {DEST.relative_to(ROOT)}  ({kb} KB)")
    print(f"  مراجع خارجية متبقية: {len(external)}" + (f" → {external[:5]}" if external else " ✓"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
بناء القالب الإنجليزي
--------------------------------------------------------------------------------
  python3 tools/build_en_html.py

يقرأ:  index.html  +  tools/translations_en_html.py
يكتب:  en/index.html  (+  en/README.md)
================================================================================
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT_DIR = ROOT / "en"
DST = OUT_DIR / "index.html"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translations_en_html import EN_HTML  # noqa: E402

ARABIC = re.compile(r"[\u0600-\u06FF]")


def main():
    raw = SRC.read_text(encoding="utf-8")
    missing = []

    # 1) استبدال النصوص
    def repl(m):
        s = m.group(0)
        core = s[1:-1] if len(s) > 1 else s
        if core in EN_HTML:
            return '"%s"' % EN_HTML[core]
        if ARABIC.search(core):
            missing.append(core)
        return s

    # النصوص بين الوسوم
    raw = re.sub(r">([^<>]+)<", lambda m: ">" + repl_text(m.group(1)) + "<", raw)

    # السمات title / placeholder / aria-label
    def attr_repl(m):
        key, val = m.group(1), m.group(2)
        if val in EN_HTML:
            return '%s="%s"' % (key, EN_HTML[val])
        if ARABIC.search(val):
            missing.append(val)
        return m.group(0)

    raw = re.sub(r'\b(title|placeholder|aria-label|data-toc|data-toc-sub)="([^"]*)"', attr_repl, raw)

    # 2) الاتجاه واللغة
    raw = raw.replace('<html lang="ar" dir="rtl"', '<html lang="en" dir="ltr"')
    raw = raw.replace("data-nums=\"latn\"", "data-nums=\"latn\"")

    # 3) مسارات الملفات (مجلد فرعي)
    raw = raw.replace('href="assets/', 'href="../assets/')
    raw = raw.replace('src="assets/', 'src="../assets/')
    raw = raw.replace('href="assets/fonts/', 'href="../assets/fonts/')

    # 4) ورقة أنماط LTR والخطوط المحلية
    # المسارات النسبية للخطوط تُعالَج مع بقية المسارات
    raw = raw.replace(
        '<link rel="stylesheet" href="../assets/css/print.css">',
        '<link rel="stylesheet" href="../assets/css/ltr.css">\n<link rel="stylesheet" href="../assets/css/print.css">',
    )

    # 5) مسار الأصول
    raw = raw.replace('window.__ASSET_BASE__ = "assets/";', 'window.__ASSET_BASE__ = "../assets/";')

    # 6) الوسوم الوصفية
    raw = raw.replace(
        '<meta name="description" content="قالب دراسة جدوى عربي RTL لمشروع تجارة إلكترونية قائم على ورشة نجارة، بطبقة ذكاء اصطناعي ومحرك مالي حيّ.">',
        '<meta name="description" content="An RTL/LTR bilingual feasibility study template for an e-commerce project built on an existing carpentry workshop, with an AI agent layer and a live financial engine.">',
    )
    raw = raw.replace(
        '<meta name="author" content="إدارة التحوّل الرقمي">',
        '<meta name="author" content="Digital Transformation Unit">',
    )

    # 7) العنوان
    raw = raw.replace(
        "<title>دراسة جدوى: التوسّع في التجارة الإلكترونية | سنديان</title>",
        "<title>Feasibility Study: E-commerce Expansion | Sandiyan</title>",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DST.write_text(raw, encoding="utf-8")

    print(f"✓ {DST.relative_to(ROOT)}")
    if missing:
        uniq = sorted(set(missing))
        print(f"\n⚠ نصوص لم تُترجم في HTML ({len(uniq)}):")
        for s in uniq:
            print(f"   {s}")
    else:
        print("  لا توجد نصوص عربية متبقية في القالب ✓")


def repl_text(t):
    """يترجم النص مع الحفاظ على المسافات المحيطة به."""
    if t in EN_HTML:
        return EN_HTML[t]
    stripped = t.strip()
    if stripped and stripped in EN_HTML:
        lead = t[: len(t) - len(t.lstrip())]
        trail = t[len(t.rstrip()):]
        return lead + EN_HTML[stripped] + trail
    return t


if __name__ == "__main__":
    main()

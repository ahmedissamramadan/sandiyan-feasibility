#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
تعليم نصوص القالب الثابتة ببيانات قابلة للتبديل (data-copy-ar / data-copy-en)
--------------------------------------------------------------------------------
  python3 tools/annotate_copy.py

يحوّل كل نص عربي ثابت في index.html إلى:
  <h2 class="sec__title" data-copy-ar="…" data-copy-en="…">النص العربي</h2>

فيبقى النص العربي محفوظًا كمحتوى أولي (يعمل بلا JavaScript)،
ويستطيع محرّك اللغة تبديله وقت التشغيل إلى الإنجليزية.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from translations_en_html import EN_HTML  # noqa: E402

INDEX = ROOT / "index.html"

# وسوم نصوصها قابلة للترجمة
TAGS = ["h1", "h2", "h3", "h4", "p", "span", "div", "td", "th", "li", "caption", "strong", "b", "em", "a", "button", "label", "dt", "dd"]

TAG_RE = "|".join(TAGS)


def escape_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def annotate(html: str) -> tuple:
    """يضيف data-copy-ar / data-copy-en إلى العناصر ذات النص العربي."""
    added = 0
    skipped = []

    # عنصر بنص داخله فقط (بلا وسوم متداخلة)
    pattern = re.compile(
        r"(<(?P<tag>" + TAG_RE + r")(?P<attrs>[^>]*?)>)(?P<text>[^<>]*[\u0600-\u06FF][^<>]*)(</(?P=tag)>)")

    def repl(m):
        nonlocal added
        tag, attrs, text = m.group("tag"), m.group("attrs"), m.group("text")
        stripped = text.strip()
        if not stripped:
            return m.group(0)
        if "data-copy-ar" in attrs:
            return m.group(0)
        en = EN_HTML.get(stripped)
        if not en:
            skipped.append(stripped)
            return m.group(0)
        # نحافظ على المسافات المحيطة
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        new_attrs = attrs + ' data-copy-text-ar="%s" data-copy-text-en="%s"' % (
            escape_attr(stripped), escape_attr(en))
        added += 1
        return "<%s%s>%s%s%s</%s>" % (tag, new_attrs, lead, stripped, trail, tag)

    out = pattern.sub(repl, html)

    # الأقسام: نضيفPair( data-copy-ar/en ) مبنية على data-toc
    def sect_repl(m):
        nonlocal added
        attrs, toc = m.group("attrs"), m.group("toc")
        if "data-toc-ar" in attrs:
            return m.group(0)
        en = EN_HTML.get(toc)
        if not en:
            return m.group(0)
        added += 1
        new_attrs = attrs + ' data-toc-ar="%s" data-toc-en="%s"' % (
            escape_attr(toc), escape_attr(en))
        return '<section%s data-toc="%s">' % (new_attrs, escape_attr(toc))

    out = re.sub(r'<section(?P<attrs>[^>]*?)data-toc="(?P<toc>[^"]+)"', sect_repl, out)

    # النصوص التي تقف وحدها داخل عنصر له عناصر أخرى (مثل أزرار شريط الأدوات)
    def wrap_text_node(m):
        nonlocal added
        before, text, after = m.group(1), m.group(2), m.group(3)  # (>) (نص) (<)
        stripped = text.strip()
        if not stripped or not re.search(r"[\u0600-\u06FF]", stripped):
            return m.group(0)
        en = EN_HTML.get(stripped)
        if not en:
            return m.group(0)
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        added += 1
        return ('%s<span data-copy-text-ar="%s" data-copy-text-en="%s">%s%s%s</span>%s'
                % (before, escape_attr(stripped), escape_attr(en), lead, stripped, trail, after))

    # نستثني كتل <script> و <style>
    blocks = []

    def stash(m):
        blocks.append(m.group(0))
        return "\x00BLOCK%d\x00" % (len(blocks) - 1)

    out = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", stash, out)
    out = re.sub(r"(>)([^<>]*[\u0600-\u06FF][^<>]*)(<)", wrap_text_node, out)
    for i, b in enumerate(blocks):
        out = out.replace("\x00BLOCK%d\x00" % i, b)
    return out, added, sorted(set(skipped))


def main():
    html = INDEX.read_text(encoding="utf-8")
    out, added, skipped = annotate(html)
    INDEX.write_text(out, encoding="utf-8")
    print(f"✓ {INDEX.relative_to(ROOT)}: {added} عنصرًا موسومًا")
    if skipped:
        print(f"  نصوص عربية بلا ترجمة ({len(skipped)}):")
        for s in skipped:
            print(f"    · {s}")


if __name__ == "__main__":
    main()

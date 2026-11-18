#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
بناء النسخة الإنجليزية من طبقة البيانات
--------------------------------------------------------------------------------
  python3 tools/build_en.py

يقرأ:  assets/data/project.json  +  tools/translations_en.py
يكتب:  assets/data/project-en.json  و  assets/data/project-en.js
ويطبع قائمة النصوص غير المترجمة.
================================================================================
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "data" / "project.json"
DST = ROOT / "assets" / "data" / "project-en.json"
EMBED = ROOT / "assets" / "data" / "project-en.js"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translations_en import EN  # noqa: E402

ARABIC = re.compile(r"[\u0600-\u06FF]")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    missing = []

    def walk(node, path):
        if isinstance(node, dict):
            return {k: walk(v, f"{path}.{k}") for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(node)]
        if isinstance(node, str):
            if node in EN:
                return EN[node]
            if ARABIC.search(node):
                missing.append((path, node))
            return node
        return node

    out = walk(data, "")
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    EMBED.write_text(
        "/* نسخة مضمّنة من project-en.json - تُحدَّث آليًّا عبر tools/build_en.py\n"
        "   الغرض منها: السماح بتشغيل القالب باللغة الإنجليزية بلا خادم. */\n"
        "window.__PROJECT_EN__ = " + json.dumps(out, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"✓ {DST.relative_to(ROOT)}")
    print(f"✓ {EMBED.relative_to(ROOT)}")
    print(f"  الترجمات المطبَّقة: {len(EN)}")

    if missing:
        print(f"\n⚠ نصوص عربية لم تُترجم ({len(missing)}):")
        for p, s in missing:
            print(f"   {p}\n      {s}")
    else:
        print("  لا توجد نصوص عربية متبقية ✓")


if __name__ == "__main__":
    main()

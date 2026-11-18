#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 مولّد مستندات دراسة الجدوى
--------------------------------------------------------------------------------
 يقرأ  assets/data/project.json  ويولّد حزمة مستندات تنفيذية كاملة:

   out/01-sop-playbook.md|.html     دليل التنفيذ (SOP) لكل قسم
   out/02-agent-registry.md|.html   سجل الوكلاء التفصيلي
   out/03-content-plan-90d.md|.html خطة المحتوى الرقمي لـ 90 يومًا
   out/04-kpi-dictionary.md|.html   قاموس مؤشرات الأداء
   out/05-executive-onepager.md|.html  الملخّص التنفيذي (صفحة واحدة)
   out/06-financial-model.csv|.json النموذج المالي
   assets/data/project.js            نسخة مضمّنة للعمل عبر file://

 الاستعمال:
     python3 tools/generate_docs.py            # توليد كل شيء
     python3 tools/generate_docs.py --sync     # مزامنة نسخة project.js فقط
================================================================================
"""

import argparse
import csv
import html
import json
import math
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILES = {
    "ar": ROOT / "assets" / "data" / "project.json",
    "en": ROOT / "assets" / "data" / "project-en.json",
}
EMBED_FILES = {
    "ar": ROOT / "assets" / "data" / "project.js",
    "en": ROOT / "assets" / "data" / "project-en.js",
}
OUT_DIR = ROOT / "out"
OUT_DIR_EN = ROOT / "out" / "en"

# ==============================================================================
# 1) المحرك المالي (مطابق لمنطق assets/js/finance.js)
# ==============================================================================


def npv_at(rate, flows):
    total = 0.0
    for t, cf in enumerate(flows):
        d = (1.0 + rate) ** t
        if d == 0 or not math.isfinite(d):
            return float("nan")
        total += cf / d
    return total


def irr(flows):
    lo, hi = -0.95, 5.0
    f_lo, f_hi = npv_at(lo, flows), npv_at(hi, flows)
    if not math.isfinite(f_lo) or not math.isfinite(f_hi) or f_lo * f_hi > 0:
        return None

    r = 0.1
    for _ in range(60):
        f = npv_at(r, flows)
        if not math.isfinite(f):
            break
        if abs(f) < 1e-7:
            return r
        h = 1e-5
        df = (npv_at(r + h, flows) - npv_at(r - h, flows)) / (2 * h)
        if not math.isfinite(df) or df == 0:
            break
        nxt = r - f / df
        if not math.isfinite(nxt) or nxt <= lo or nxt >= hi:
            break
        if abs(nxt - r) < 1e-9:
            return nxt
        r = nxt

    a, b, fa = lo, hi, f_lo
    for _ in range(200):
        mid = (a + b) / 2
        fm = npv_at(mid, flows)
        if not math.isfinite(fm):
            break
        if abs(fm) < 1e-7:
            return mid
        if fa * fm < 0:
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2


def compute_model(fin, over=None):
    """نموذج مالي خماسي مع Sensitivity جاهزة."""
    o = over or {}
    price_f = o.get("priceFactor", 1.0)
    units_f = o.get("unitsFactor", 1.0)
    opex_f = o.get("opexFactor", 1.0)
    capex_f = o.get("capexFactor", 1.0)
    growth_d = o.get("growthDelta", 0.0)
    discount = o.get("discountRate", fin.get("discount_rate", 0.24))
    tax_rate = fin.get("tax_rate", 0.0)
    infl = fin.get("inflation", 0.0)
    horizon = int(fin.get("horizon_years", 5))

    capex0 = 0.0
    capex_by_year = {}
    capex_total = 0.0
    for c in fin.get("capex", []):
        amt = float(c.get("qty", 0)) * float(c.get("unit_cost", 0)) * capex_f
        capex_total += amt
        y = int(c.get("year", 1))
        if y <= 0:
            capex0 += amt
        else:
            capex_by_year[y] = capex_by_year.get(y, 0.0) + amt

    dep_years = max(1, int(fin.get("depreciation_years", 5)))
    annual_dep = max(0.0, capex_total) / dep_years

    wc = fin.get("working_capital", {})
    ar_days = float(wc.get("ar_days", 0))
    inv_days = float(wc.get("inventory_days", 0))
    ap_days = float(wc.get("ap_days", 0))

    years = []
    prev_wc = 0.0
    cumulative = -capex0

    for y in range(1, horizon + 1):
        units = revenue = cogs = 0.0
        for r in fin.get("revenue", []):
            # النمو مخزَّن كنسبة مئوية (12 = 12%) → تُحوَّل إلى عدد عشري قبل compounding
            growth = float(r.get("growth", 0)) / 100 + growth_d
            u = float(r.get("monthly_units", 0)) * 12 * units_f * ((1 + growth) ** (y - 1))
            price = float(r.get("price", 0)) * price_f
            vc = float(r.get("variable_cost", 0)) * price_f
            units += u
            revenue += u * price
            cogs += u * vc

        opex_fixed = opex_var = 0.0
        for o_item in fin.get("opex", []):
            if o_item.get("type") == "pct_revenue":
                opex_var += revenue * (float(o_item.get("monthly", 0)) / 100.0)
            else:
                opex_fixed += float(o_item.get("monthly", 0)) * 12 * ((1 + infl) ** (y - 1))
        opex_fixed *= opex_f
        opex_var *= opex_f

        gross = revenue - cogs
        ebitda = gross - opex_fixed - opex_var
        dep = annual_dep if y <= dep_years else 0.0
        ebit = ebitda - dep
        tax = max(0.0, ebit) * tax_rate
        net = ebit - tax

        wc_now = (revenue * ar_days) / 365 + (cogs * inv_days) / 365 - (cogs * ap_days) / 365
        d_wc = wc_now - prev_wc
        prev_wc = wc_now

        capex_y = capex_by_year.get(y, 0.0)
        fcf = net + dep - capex_y - d_wc
        cumulative += fcf

        years.append(
            {
                "year": y, "units": units, "revenue": revenue, "cogs": cogs, "gross": gross,
                "gross_margin": (gross / revenue) if revenue else 0.0,
                "opex_fixed": opex_fixed, "opex_var": opex_var,
                "opex_total": opex_fixed + opex_var, "ebitda": ebitda,
                "ebitda_margin": (ebitda / revenue) if revenue else 0.0,
                "depreciation": dep, "ebit": ebit, "tax": tax, "net": net,
                "net_margin": (net / revenue) if revenue else 0.0,
                "working_capital": wc_now, "delta_wc": d_wc, "capex": capex_y,
                "fcf": fcf, "cumulative": cumulative,
            }
        )

    flows = [-capex0] + [r["fcf"] for r in years]
    npv = npv_at(discount, flows)
    irr_val = irr(flows)

    y1 = years[0] if years else {"revenue": 0, "cogs": 0, "units": 0, "opex_fixed": 0, "opex_var": 0}
    total_cm = y1["revenue"] - y1["cogs"]
    avg_cm = (total_cm / y1["units"]) if y1["units"] else 0
    fixed_costs = y1["opex_fixed"]
    be_units = (fixed_costs / avg_cm) if avg_cm > 0 else None
    avg_price = (y1["revenue"] / y1["units"]) if y1["units"] else 0
    be_revenue = be_units * avg_price if be_units is not None else None

    return {
        "years": years, "flows": flows, "npv": npv, "irr": irr_val,
        "capex_total": capex_total, "capex0": capex0,
        "discount_rate": discount, "tax_rate": tax_rate,
        "break_even_units": be_units, "break_even_revenue": be_revenue,
        "avg_contribution": avg_cm, "avg_price": avg_price,
        "total_revenue": sum(r["revenue"] for r in years),
        "total_net": sum(r["net"] for r in years),
    }


SCENARIOS = {
    "متحفظ": {"priceFactor": 0.90, "unitsFactor": 0.75, "opexFactor": 1.15, "capexFactor": 1.10, "growthDelta": -0.02},
    "أساسي": {},
    "متفائل": {"priceFactor": 1.08, "unitsFactor": 1.20, "opexFactor": 0.95, "capexFactor": 0.95, "growthDelta": 0.02},
}


# ==============================================================================
# 2) أدوات التنسيق
# ==============================================================================

CUR = "ج.م"
LANG = "ar"
OUT = OUT_DIR
LABELS = {}
SOP = []


def set_lang(lang):
    """يضبط اللغة والمخرجات وقوالب الخطوات."""
    global CUR, LANG, OUT, LABELS, SOP
    LANG = lang
    if lang == "en":
        CUR = "EGP"
        OUT = OUT_DIR_EN
        from sop_steps_en import SOP_EN
        SOP = [
            (code.replace("س", "S"), title, owner, [(s[0], s[1], s[2], s[3]) for s in steps])
            for code, (title, owner, steps) in SOP_EN.items()
        ]
        LABELS = {
            "sopTitle": "Implementation playbook",
            "sopIntro": "This playbook turns every section of the study into executable steps, each with an owner, an output and an acceptance criterion.",
            "owner": "Owner",
            "step": "Step", "output": "Output", "responsible": "Responsible",
            "acceptance": "Acceptance criterion",
            "metricsTitle": "Governing financial indicators",
            "metricsHead": "Indicator", "metricsValue": "Value",
            "agentsTitle": "Agent registry",
            "agentsIntro": "Each agent: a defined mission, tools, outputs, a performance indicator, a human owner and an escalation trigger.",
            "id": "ID", "agent": "Agent", "role": "Role", "tools": "Tools",
            "outputs": "Outputs", "kpi": "Performance metric", "supervisor": "Human owner",
            "autonomy": "Autonomy",
            "govTitle": "AI governance",
            "contentTitle": "Digital content plan: first 90 days",
            "contentIntro": "A fixed rhythm: one piece of content a day, a weekly compilation, and a review of the numbers at the end of the week.",
            "day": "Day", "pillar": "Content pillar", "formats": "Formats",
            "channel": "Channel", "idea": "Creative idea", "metric": "Metric",
            "week": "Week",
            "kpiTitle": "KPI dictionary",
            "kpiIntro": "Every indicator carries a definition, a formula, a target, a source, a cadence and an owner.",
            "indicator": "Indicator", "area": "Area", "definition": "Definition",
            "formula": "Formula", "target": "Target", "source": "Measurement source",
            "cadence": "Cadence",
            "oneTitle": "Executive summary: one page",
            "indicators": "Governing indicators",
            "summary": "Summary", "recommendation": "Recommendation",
            "conditions": "Conditions", "nextSteps": "Next steps",
            "stepName": "Step", "deadline": "Deadline",
            "finTitle": "Financial model",
            "generated": "Generated automatically from the data layer",
            "confidential": "Confidential: internal circulation only",
        }
    else:
        OUT = OUT_DIR
        SOP = SOP_TEMPLATES
        LABELS = {
            "sopTitle": "دليل التنفيذ (SOP)",
            "sopIntro": "هذا الدليل يحوّل كل قسم من الدراسة إلى خطوات تنفيذية لها مالك ومخرَج ومعيار قبول.",
            "owner": "المالك", "step": "الخطوة", "output": "المخرَج",
            "responsible": "المسؤول", "acceptance": "معيار القبول",
            "metricsTitle": "المؤشرات المالية الحاكمة", "metricsHead": "المؤشر", "metricsValue": "القيمة",
            "agentsTitle": "سجلّ الوكلاء",
            "agentsIntro": "كل وكيل: مهمة محدّدة، أدوات، مخرجات، مؤشر أداء، مالك بشري، وشرط تصعيد.",
            "id": "المعرّف", "agent": "الوكيل", "role": "الدور", "tools": "الأدوات",
            "outputs": "المخرجات", "kpi": "مؤشر الأداء", "supervisor": "المشرف البشري",
            "autonomy": "الاستقلالية",
            "govTitle": "حوكمة الذكاء الاصطناعي",
            "contentTitle": "خطة المحتوى الرقمي: أول 90 يومًا",
            "contentIntro": "خطة إيقاعية ثابتة: كل يومٍ يُنشر نوع محتوى واحد، وكل أسبوعٍ تجميعٌ للأرقام، ومراجعة الأرقام في نهاية الأسبوع.",
            "day": "اليوم", "pillar": "عمود المحتوى", "formats": "الصيغ",
            "channel": "القناة", "idea": "الفكرة الإبداعية", "metric": "المؤشر", "week": "الأسبوع",
            "kpiTitle": "قاموس مؤشرات الأداء",
            "kpiIntro": "لكل مؤشر: تعريف، صيغة، مستهدف، مصدر قياس، تواتر، ومالك.",
            "indicator": "المؤشر", "area": "المجال", "definition": "التعريف",
            "formula": "الصيغة", "target": "المستهدف", "source": "مصدر القياس", "cadence": "التواتر",
            "oneTitle": "الملخّص التنفيذي: صفحة واحدة",
            "indicators": "المؤشرات الحاكمة", "summary": "الخلاصة",
            "recommendation": "التوصية", "conditions": "الشروط", "nextSteps": "الخطوات التالية",
            "stepName": "الخطوة", "deadline": "الموعد",
            "finTitle": "النموذج المالي",
            "generated": "مولَّد آليًّا من طبقة البيانات",
            "confidential": "سري: للتداول الداخلي فقط",
        }


def n(v, dec=0):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "-"
    return f"{v:,.{dec}f}"


def money(v, dec=0):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "-"
    return f"{n(v, dec)} {CUR}"


def money_short(v):
    if v is None or not math.isfinite(v):
        return "-"
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1e9:
        return f"{sign}{a/1e9:.2f} مليار {CUR}"
    if a >= 1e6:
        return f"{sign}{a/1e6:.2f} مليون {CUR}"
    if a >= 1e3:
        return f"{sign}{a/1e3:.0f} ألف {CUR}"
    return f"{sign}{a:,.0f} {CUR}"


def pct(v, dec=1):
    if v is None or not math.isfinite(v):
        return "-"
    return f"{v*100:.{dec}f}%"


def esc(s):
    return html.escape(str(s), quote=True)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


# ==============================================================================
# 3) قالب HTML للطباعة (RTL)
# ==============================================================================

DOC_CSS = """
:root{--ink:#1c1713;--muted:#6f6257;--line:#e3dacd;--wood:#553b26;--mint:#0e7c66;
--gold:#a8781d;--paper:#fbf8f3;--surface:#fff;--danger:#b3261e}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:"IBM Plex Sans Arabic","IBM Plex Sans Latin","Tajawal","Noto Sans Arabic","Geeza Pro",system-ui,sans-serif;
font-size:11pt;line-height:1.9;letter-spacing:0}
.page{max-width:210mm;min-height:297mm;margin:0 auto;padding:20mm 18mm;background:#fff}
h1{font-size:22pt;line-height:1.35;margin:0 0 6pt;color:var(--wood)}
h2{font-size:15pt;margin:22pt 0 8pt;padding-bottom:5pt;border-bottom:1.5pt solid var(--wood);color:var(--wood)}
h3{font-size:12.5pt;margin:16pt 0 6pt;color:var(--mint)}
p{margin:0 0 8pt}
ul,ol{margin:0 0 10pt;padding-inline-start:1.5em}
li{margin-bottom:4pt}
table{width:100%;border-collapse:collapse;margin:0 0 12pt;font-size:9.5pt}
th,td{border:1px solid var(--line);padding:6pt 8pt;text-align:right;vertical-align:top}
thead th{background:#f3ede4;font-weight:700}
tbody tr:nth-child(even){background:#faf7f2}
.num{direction:rtl;text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.cover{background:linear-gradient(155deg,#241a12,#553b26);color:#f6efe6;border-radius:8pt;
padding:26pt;margin-bottom:16pt;min-height:150mm;display:flex;flex-direction:column;justify-content:space-between}
.cover h1{color:#fff;font-size:26pt}
.cover .badge{display:inline-block;border:1px solid rgba(255,255,255,.3);border-radius:99pt;
padding:4pt 12pt;font-size:9pt}
.cover dl{display:grid;grid-template-columns:repeat(3,1fr);gap:8pt 14pt;margin:0;
border-top:1px solid rgba(255,255,255,.25);padding-top:12pt}
.cover dt{font-size:8pt;color:rgba(246,239,230,.6)}
.cover dd{margin:0;font-size:10pt;font-weight:700;color:#fff}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8pt;margin:0 0 14pt}
.kpi{border:1px solid var(--line);border-radius:6pt;padding:8pt 10pt;background:#fff}
.kpi .l{font-size:8.5pt;color:var(--muted)}
.kpi .v{font-size:14pt;font-weight:700;color:var(--mint)}
.callout{border:1px solid var(--line);border-inline-start:3pt solid var(--gold);
background:#fbf6e9;border-radius:5pt;padding:9pt 12pt;margin:0 0 12pt}
.callout b{color:var(--gold)}
.foot{margin-top:18pt;padding-top:8pt;border-top:1px solid var(--line);
font-size:8.5pt;color:var(--muted);display:flex;justify-content:space-between}
code{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:9pt;
direction:ltr;unicode-bidi:isolate;background:#f3ede4;padding:1pt 4pt;border-radius:3pt}
@media print{body{background:#fff}.page{padding:0;min-height:auto;max-width:none}
h2{page-break-after:avoid}table{page-break-inside:auto}tr{page-break-inside:avoid}
thead{display:table-header-group}.cover{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def doc_html(title, body, footer_right=""):
    depth = "../" if OUT == OUT_DIR else "../../"
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{depth}assets/css/fonts.css">
<style>{DOC_CSS}</style>
</head>
<body>
<div class="page">
{body}
<div class="foot">
  <span>{esc(title)}</span>
  <span>{esc(footer_right)}</span>
</div>
</div>
</body>
</html>
"""


def write_pair(stem, title, md_body, html_body, footer_right=""):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{stem}.md").write_text(md_body, encoding="utf-8")
    (OUT / f"{stem}.html").write_text(doc_html(title, html_body, footer_right), encoding="utf-8")
    return stem


SOP_TEMPLATES = [
    ("س01", "ضبط الوثيقة وسجلّ المراجعات", "مدير المشروع الرقمي", [
        ("توثيق ملكية المشروع وترخيصه وكل الشروط المعلقة", "ورقة", "مجلس الإدارة", "قائمة موقّعة"),
        ("تجهيز سجلّ الإصدارات وقوالب الاعتماد", "قالب", "مدير المشروع الرقمي", "سجلّ معبّأ"),
        ("جمع المراجعات وربطهم بمحاضر الجلسات", "جلسات", "مدير المشروع الرقمي", "محاضر الجلسات"),
        ("إصدار النسخة 1.0 للاعتماد", "وثيقة", "الرئيس التنفيذي", "وثيقة معتمدة"),
    ]),
    ("س02", "الملخّص التنفيذي وبطاقة قرار الاستثمار", "مدير المشروع الرقمي", [
        ("تحديث المؤشرات الحاكمة من النموذج الحيّ", "ورقة", "وكيل التحليل", "أرقام مطابقة للنموذج"),
        ("صياغة التوصية والطلب المالي", "نص", "مدير المشروع الرقمي", "صياغة معتمدة"),
        ("تحديد الشروط المعلقة وأدوات التحقق منها", "قائمة", "الإدارة التنفيذية", "كل شرط له أداة"),
        ("عرض القرار على مجلس الإدارة", "عرض", "الرئيس التنفيذي", "قرار موثّق"),
    ]),
    ("س03", "الإطار القانوني والمؤسسي", "المدير المالي", [
        ("مراجعة سريان التراخيص ومواعيد التجديد", "سجل", "وكيل الامتثال", "لا تأخير في أي ترخيص"),
        ("توثيق هيكل الملكية وحقوق الملكية الفكرية", "وثيقة", "الشريك المؤسّس", "عقد مسجّل"),
        ("مراجعة متطلبات حماية البيانات", "قائمة", "وكيل الامتثال", "سياسة منشورة"),
    ]),
    ("س04", "وصف المشروع ونطاقه", "مدير الورشة", [
        ("تحديث بيانات الأصول والطاقة الإنتاجية", "سجل", "مدير الورشة", "أرقام موثّقة بالشهر"),
        ("تثبيت أسعار الخامات ومدد التوريد", "قائمة أسعار", "أمين المخزن", "عرض ساري"),
        ("تقدير الطاقة الفعلية بالمحاكاة", "محاكاة", "وكيل مخطط الإنتاج", "جدول إنتاج"),
    ]),
    ("س05", "الأساس المفاهيمي للجدوى", "مدير المشروع الرقمي", [
        ("توثيق مصدر كل رقم في الدراسة", "جدول مصادر", "وكيل التحليل", "كل رقم له مصدر"),
        ("مراجعة الفجوة بين التقدير والقياس", "قائمة", "مدير المشروع الرقمي", "فجوة مغلقة أو مُبرَّرة"),
    ]),
    ("س06", "التحليل الاستراتيجي", "مدير التسويق", [
        ("تحديث مصفوفتي EFE و IFE", "مصفوفتان", "وكيل مراجعة المخاطر", "أوزان منطقة ومبرَّرة"),
        ("مراجعة SWOT و TOWS ربع سنويًا", "مصفوفة", "وكيل محلّل السوق", "استراتيجيات محدّثة"),
        ("تحليل PESTEL وبورتر", "تحليل", "وكيل محلّل السوق", "توصيات محدّدة"),
    ]),
    ("س07", "تحليل السوق والطلب", "مدير التسويق", [
        ("تحديث حجم السوق وتقدير SOM", "تقدير", "وكيل محلّل السوق", "تقدير موثّق بمصدر"),
        ("مراجعة أسعار المنافسين أسبوعيًا", "سجل أسعار", "وكيل محلّل السوق", "سجل محدَّث"),
        ("اختبار نية الشراء وقياس التحويل", "اختبار", "وكيل مدير النمو", "بيانات اختبار"),
    ]),
    ("س08", "طبقة الذكاء الاصطناعي وخريطة الوكلاء", "مدير المشروع الرقمي", [
        ("تعيين المالك البشري لكل وكيل", "جدول", "مدير المشروع الرقمي", "لا وكيل بلا مالك"),
        ("ضبط حدود التنفيذ الآلي", "سياسة", "وكيل مراجعة المخاطر", "سياسة معتمدة"),
        ("مراجعة أداء الوكلاء ربع سنويًا", "تقرير", "وكيل مدير المشروع", "تقرير بخطوات تصحيح"),
    ]),
    ("س09", "استراتيجية التسويق والمبيعات", "مدير التسويق", [
        ("توزيع ميزانية الإعلانات حسب أداء القنوات", "قرار", "وكيل مدير النمو", "إعادة توزيع ربع سنوية"),
        ("تشغيل الاختبارات A/B على مسار الشراء", "اختبار", "وكيل تجربة العملاء", "قرار مبني على بيانات"),
        ("بناء قائمة شرائح مملوكة", "قائمة", "وكيل إدارة وسائل التواصل", "نمو شهري موثّق"),
    ]),
    ("س10", "العمليات والتصنيع", "مدير الورشة", [
        ("ضبط جدول الإنتاج ومطابقة الطلبات", "جدول", "وكيل مخطط الإنتاج", "التزام بالمواعيد ≥ 92%"),
        ("فحص الجودة قبل الشحن", "قائمة فحص", "وكيل مشرف الجودة", "توثيق صور إلزامي"),
        ("قياس دورة الاسترجاع وتكلفةه", "تقرير", "وكيل التحليل", "تكلفة محدّدة"),
    ]),
    ("س11", "التقنية والبنية الرقمية", "قائد الهندسة", [
        ("بناء المنصة ونظام إدارة الطلبات", "إصدار", "وكيل مهندس المنصة", "اختبارات ناجحة"),
        ("اختبار التكاملات ومزامنة المخزون", "اختبار", "وكيل التكامل", "نجاح مزامنة ≥ 95%"),
        ("مراجعة أمنية ونسخ احتياطي", "مراجعة", "وكيل الأمن السيبراني", "لا ثغرة حرجة مفتوحة"),
    ]),
    ("س12", "الموارد البشرية والتنظيم", "مدير المشروع الرقمي", [
        ("اعتماد الهيكل والتوظيف", "خطة", "الإدارة التنفيذية", "اعتماد"),
        ("تدريب فريق الورشة على النظام", "ورشة", "وكيل مدير المشروع", "اختبار عملي ناجح"),
        ("مراجعة سياسات الاستخدام والصلاحيات", "سياسة", "وكيل الامتثال", "توقيع من الجميع"),
    ]),
    ("س13", "الجداول المالية", "المدير المالي", [
        ("مراجعة الافتراضات وتحديث النموذج", "نموذج", "وكيل التحليل", "النموذج محدَّث"),
        ("إعادة ضبط التوقعات بعد الشهر الثالث", "نموذج", "المدير المالي", "فارق مبرَّر وموثَّق"),
        ("إصدار تقرير الحساسية للنواة التنفيذية", "تقرير", "وكيل التحليل", "تقرير صفحة واحدة"),
    ]),
    ("س14", "المخاطر وخطة التخفيف", "مدير المشروع الرقمي", [
        ("تحديث سجلّ المخاطر واحتمالاتها", "سجل", "وكيل مراجعة المخاطر", "كل خطر له إجراء"),
        ("اختبار خطط الطوارئ دوريًا", "اختبار", "وكيل مراجعة المخاطر", "نتيجة موثّقة"),
    ]),
    ("س15", "الجدول الزمني وخارطة الطريق", "مدير المشروع الرقمي", [
        ("تحديث حالة كل مرحلة أسبوعيًا", "لوحة", "وكيل مدير المشروع", "تحديث أسبوعي"),
        ("التحقق من بوابات القرار", "بوابات", "الإدارة التنفيذية", "لا تجاوز لبوابة"),
    ]),
    ("س16", "مؤشرات الأداء وإطار القياس", "وكيل البيانات", [
        ("ضبط أحداث التتبّع والتحقق منها", "خطة تتبّع", "وكيل البيانات", "تغطية ≥ 95%"),
        ("إصدار لوحة الأداء الأسبوعية", "لوحة", "وكيل البيانات", "تقرير منتظم"),
    ]),
    ("س17", "الاستنتاج والتوصيات", "الرئيس التنفيذي", [
        ("مراجعة التوصية وشروطها", "وثيقة", "الإدارة التنفيذية", "توصية معتمدة"),
        ("تثبيت الخطوات التالية ومسؤوليها", "خطة", "مدير المشروع الرقمي", "كل خطوة لها تاريخ"),
    ]),
    ("س18", "الملاحق", "وكيل التحليل", [
        ("تحديث فهرس المصادر", "قائمة", "وكيل التحليل", "كل مصدر قابل للتحقق"),
        ("تحديث المعجم المصطلحات", "معجم", "وكيل التحليل", "محدّث"),
    ]),
]


def gen_sop(d, model):
    L = LABELS
    meta = d["meta"]
    md = [f"# {L['sopTitle']}: {meta['project_name']}", "",
          f"> {L['generated']} · {meta['version']} · {meta['date']}", "",
          L["sopIntro"], ""]

    for code, title, owner, steps in SOP:
        md += [f"## {code}: {title}", "", f"**{L['owner']}:** {owner}", "",
               md_table(["#", L["step"], L["output"], L["responsible"], L["acceptance"]],
                        [[i + 1, s[0], s[1], s[2], s[3]] for i, s in enumerate(steps)]), ""]

    h = [f"<h1>{esc(L['sopTitle'])}: {esc(meta['project_name'])}</h1>",
         f"<p class='note'>{esc(L['generated'])} · {esc(meta['version'])} · {esc(meta['date'])}</p>",
         f"<div class='callout'><b>{esc(L['sopIntro'])}</b></div>"]

    for code, title, owner, steps in SOP:
        h += [f"<h2>{esc(code)}: {esc(title)}</h2>", f"<p><b>{esc(L['owner'])}:</b> {esc(owner)}</p>",
              "<table><thead><tr><th>#</th><th>" + esc(L["step"]) + "</th><th>" + esc(L["output"]) +
              "</th><th>" + esc(L["responsible"]) + "</th><th>" + esc(L["acceptance"]) + "</th></tr></thead><tbody>"]
        for i, s in enumerate(steps, 1):
            h.append(f"<tr><td class='num'>{i}</td><td>{esc(s[0])}</td><td>{esc(s[1])}</td>"
                     f"<td>{esc(s[2])}</td><td>{esc(s[3])}</td></tr>")
        h.append("</tbody></table>")

    h += ["<h2>" + esc(L["metricsTitle"]) + "</h2>",
          "<table><thead><tr><th>" + esc(L["metricsHead"]) + "</th><th>" + esc(L["metricsValue"]) +
          "</th></tr></thead><tbody>",
          f"<tr><td>NPV</td><td class='num'>{esc(money(model['npv']))}</td></tr>",
          f"<tr><td>IRR</td><td class='num'>{esc(pct(model['irr']))}</td></tr>",
          f"<tr><td>Break-even</td><td class='num'>{esc(n(model['break_even_units']))} units / year</td></tr>",
          f"<tr><td>Total revenue ({len(model['years'])} years)</td><td class='num'>{esc(money(model['total_revenue']))}</td></tr>",
          "</tbody></table>"]

    body = "".join(h)
    md += ["## " + L["metricsTitle"], "",
           md_table([L["metricsHead"], L["metricsValue"]],
                    [["NPV", money(model["npv"])],
                     ["IRR", pct(model["irr"])],
                     ["Break-even", f"{n(model['break_even_units'])} units / year"],
                     ["Total revenue", money(model["total_revenue"])]])]

    write_pair("01-sop-playbook", f"{L['sopTitle']}: {meta['project_name']}",
               "\n".join(md), body, L["confidential"])


def gen_agents(d):
    L = LABELS
    agents = d["agents"]
    md = [f"# {L['agentsTitle']}: {d['meta']['project_name']}", "",
          f"> {len(agents)} agents · {L['generated']}", "", L["agentsIntro"], ""]

    groups = {}
    for a in agents:
        groups.setdefault(a["group"], []).append(a)

    h = [f"<h1>{esc(L['agentsTitle'])}: {esc(d['meta']['project_name'])}</h1>",
         f"<p>{L['agentsIntro']}</p>"]

    for g, items in groups.items():
        md += [f"## {g}", "",
               md_table([L["id"], L["agent"], L["role"], L["tools"], L["outputs"], L["kpi"], L["supervisor"], L["autonomy"]],
                        [[a["id"], a["title"], a["role"], " · ".join(a.get("tools", [])),
                          " · ".join(a.get("outputs", [])), a.get("kpi", "-"), a.get("owner", "-"),
                          a.get("autonomy", "-")] for a in items]), ""]
        h += [f"<h2>{esc(g)}</h2>",
              "<table><thead><tr><th>" + esc(L["id"]) + "</th><th>" + esc(L["agent"]) + "</th><th>" +
              esc(L["role"]) + "</th><th>" + esc(L["tools"]) + "</th><th>" + esc(L["outputs"]) + "</th><th>" +
              esc(L["kpi"]) + "</th><th>" + esc(L["supervisor"]) + "</th><th>" + esc(L["autonomy"]) +
              "</th></tr></thead><tbody>"]
        for a in items:
            h.append(
                f"<tr><td class='num'>{esc(a['id'])}</td><td><b>{esc(a['title'])}</b><br>"
                f"<small>{esc(a['role'])}</small></td><td>{esc(a['mission'])}</td>"
                f"<td><small>{esc(' · '.join(a.get('tools', [])))}</small></td>"
                f"<td><small>{esc(' · '.join(a.get('outputs', [])))}</small></td>"
                f"<td>{esc(a.get('kpi', '-'))}</td><td>{esc(a.get('owner', '-'))}</td>"
                f"<td>{esc(a.get('autonomy', '-'))}</td></tr>")
        h.append("</tbody></table>")

    body = "".join(h)
    md += ["## " + L["govTitle"], ""]
    gov_titles = {
        "principles": "Principles", "human_in_loop": "Mandatory human in the loop",
        "model_policy": "Model and data policy", "security": "Security and privacy",
        "cost_model": "Cost control",
    }
    for key, items in d["ai_governance"].items():
        md += [f"### {gov_titles.get(key, key)}", ""] + [f"- {x}" for x in items] + [""]
        body += f"<h3>{esc(gov_titles.get(key, key))}</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"

    write_pair("02-agent-registry", f"{L['agentsTitle']}: {d['meta']['project_name']}",
               "\n".join(md), body, L["confidential"])


PLAN_DAYS_AR = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
PLAN_DAYS_EN = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
PLAN_CHANNELS_AR = ["إنستجرام", "بحث جوجل", "تيك توك", "فيسبوك", "واتساب", "الموقع"]
PLAN_CHANNELS_EN = ["Instagram", "Google Search", "TikTok", "Facebook", "WhatsApp", "Website"]
IDEAS_AR = ["مثال تطبيقي واحد من الورشة مع رقم واضح", "مقارنة قبل وبعد موثّقة", "شرح الفرق التقني بأسلوب مبسّط"]
IDEAS_EN = ["One worked example from the workshop with a hard number",
            "A documented before-and-after comparison",
            "The technical difference explained in plain language"]


def gen_content_plan(d):
    L = LABELS
    mk = d["marketing"]
    pillars = mk["content_pillars"]
    days = PLAN_DAYS_AR if LANG == "ar" else PLAN_DAYS_EN
    channels = PLAN_CHANNELS_AR if LANG == "ar" else PLAN_CHANNELS_EN
    ideas = IDEAS_AR if LANG == "ar" else IDEAS_EN

    md = [f"# {L['contentTitle']}", "", f"> {d['meta']['project_name']}", "", L["contentIntro"], ""]
    h = [f"<h1>{esc(L['contentTitle'])}</h1>", f"<p>{esc(d['meta']['project_name'])}</p>"]

    for week in range(13):
        rows = []
        for di, day in enumerate(days):
            p = pillars[(week * len(days) + di) % len(pillars)]
            ch = channels[(week + di) % len(channels)]
            idea = ideas[(week + di) % len(ideas)]
            rows.append([day, p["pillar"], " · ".join(p["formats"]), ch, idea, p["kpi"]])
        md += [f"## {L['week']} {week+1}", "",
               md_table([L["day"], L["pillar"], L["formats"], L["channel"], L["idea"], L["metric"]], rows), ""]
        h += [f"<h2>{esc(L['week'])} {week+1}</h2>",
              "<table><thead><tr><th>" + esc(L["day"]) + "</th><th>" + esc(L["pillar"]) + "</th><th>" +
              esc(L["formats"]) + "</th><th>" + esc(L["channel"]) + "</th><th>" + esc(L["idea"]) + "</th><th>" +
              esc(L["metric"]) + "</th></tr></thead><tbody>"]
        for r in rows:
            h.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>")
        h.append("</tbody></table>")

    body = "".join(h)
    write_pair("03-content-plan-90d", L["contentTitle"], "\n".join(md), body, L["confidential"])


def gen_kpi(d):
    L = LABELS
    kpis = d["kpis"]
    md = [f"# {L['kpiTitle']}: {d['meta']['project_name']}", "", L["kpiIntro"], "",
          md_table([L["indicator"], L["area"], L["definition"], L["formula"], L["target"],
                    L["source"], L["cadence"], L["supervisor"]],
                   [[k["name"], k["category"], k["definition"], k["formula"], k["target"],
                     k["source"], k["cadence"], k["owner"]] for k in kpis]), ""]

    cats = {}
    for k in kpis:
        cats.setdefault(k["category"], []).append(k)

    h = [f"<h1>{esc(L['kpiTitle'])}: {esc(d['meta']['project_name'])}</h1>"]
    for c, items in cats.items():
        h += [f"<h2>{esc(c)}</h2>",
              "<table><thead><tr><th>" + esc(L["indicator"]) + "</th><th>" + esc(L["definition"]) +
              "</th><th>" + esc(L["formula"]) + "</th><th>" + esc(L["target"]) + "</th><th>" +
              esc(L["source"]) + "</th><th>" + esc(L["cadence"]) + "</th><th>" + esc(L["supervisor"]) +
              "</th></tr></thead><tbody>"]
        for k in items:
            h.append(f"<tr><td><b>{esc(k['name'])}</b></td><td>{esc(k['definition'])}</td>"
                     f"<td><code>{esc(k['formula'])}</code></td><td>{esc(k['target'])}</td>"
                     f"<td>{esc(k['source'])}</td><td>{esc(k['cadence'])}</td><td>{esc(k['owner'])}</td></tr>")
        h.append("</tbody></table>")

    write_pair("04-kpi-dictionary", f"{L['kpiTitle']}: {d['meta']['project_name']}",
               "\n".join(md), "".join(h), L["confidential"])


def gen_onepager(d, model):
    L = LABELS
    meta = d["meta"]
    dec = d["decision"]
    c = d["conclusion"]
    kpis = [
        ("Capital requested", money(dec.get("ask_amount"))),
        ("Year-one revenue", money(model["years"][0]["revenue"] if model["years"] else 0)),
        ("Net present value (NPV)", money(model["npv"])),
        ("Internal rate of return (IRR)", pct(model["irr"])),
        ("Break-even", f"{n(model['break_even_units'])} units / year"),
        (f"Total revenue ({len(model['years'])} years)", money(model["total_revenue"])),
    ]

    md = [f"# {meta['project_name']}: {L['oneTitle']}", "",
          f"**{meta['subtitle']}**", "",
          f"> {meta['prepared_for']} · {meta['date']} · {meta['confidentiality']}", "",
          "## " + L["indicators"], "", md_table([L["metricsHead"], L["metricsValue"]], [[k, v] for k, v in kpis]), "",
          "## " + L["summary"], "", c["summary"], "",
          "## " + L["recommendation"], "", c["recommendation"], "",
          "## " + L["conditions"], ""]
    md += [f"{i+1}. {x}" for i, x in enumerate(dec.get("conditions", []))]
    md += ["", "## " + L["nextSteps"], "",
           md_table([L["stepName"], L["responsible"], L["deadline"]],
                    [[s["step"], s.get("owner", "-"), s.get("deadline", "-")] for s in c["next_steps"]]), ""]

    kpi_html = "".join(
        f"<div class='kpi'><div class='l'>{esc(k)}</div><div class='v'>{esc(v)}</div></div>" for k, v in kpis)
    h = [f"<div class='cover'><div><span class='badge'>{esc(meta['status'])}</span></div>"
         f"<div><h1>{esc(meta['title'])}</h1><p>{esc(meta['subtitle'])}</p></div>"
         f"<dl><div><dt>{esc(meta['prepared_for'])}</dt><dd>{esc(meta['project_name'])}</dd></div>"
         f"<div><dt>{esc(L['generated'])}</dt><dd>{esc(meta['prepared_by'])}</dd></div>"
         f"<div><dt>{esc(meta['date'])}</dt><dd>{esc(meta['version'])}</dd></div></dl></div>",
         "<h2>" + esc(L["indicators"]) + "</h2>", f"<div class='kpis'>{kpi_html}</div>",
         "<h2>" + esc(L["summary"]) + "</h2>", f"<p>{esc(c['summary'])}</p>",
         "<h2>" + esc(L["recommendation"]) + "</h2>", f"<p>{esc(c['recommendation'])}</p>",
         "<h2>" + esc(L["conditions"]) + "</h2>", "<ol>" + "".join(f"<li>{esc(x)}</li>" for x in dec.get("conditions", [])) + "</ol>",
         "<h2>" + esc(L["nextSteps"]) + "</h2>",
         "<table><thead><tr><th>" + esc(L["stepName"]) + "</th><th>" + esc(L["responsible"]) +
         "</th><th>" + esc(L["deadline"]) + "</th></tr></thead><tbody>"]
    for s in c["next_steps"]:
        h.append(f"<tr><td>{esc(s['step'])}</td><td>{esc(s.get('owner','-'))}</td><td>{esc(s.get('deadline','-'))}</td></tr>")
    h.append("</tbody></table>")

    write_pair("05-executive-onepager", f"{L['oneTitle']}: {meta['project_name']}",
               "\n".join(md), "".join(h), L["confidential"])


def gen_financial(d, model):
    OUT.mkdir(parents=True, exist_ok=True)

    labels = [("revenue", "Revenue"), ("cogs", "Cost of goods sold"), ("gross", "Gross profit"),
              ("opex_total", "Operating expenses"), ("ebitda", "EBITDA"), ("depreciation", "Depreciation"),
              ("ebit", "Profit before tax"), ("tax", "Tax"), ("net", "Net profit"),
              ("fcf", "Free cash flow"), ("cumulative", "Cumulative cash flow")]
    header = ["Line item"] + [f"Year {r['year']}" for r in model["years"]]
    rows = []
    for key, lab in labels:
        rows.append([lab] + [round(r[key]) for r in model["years"]])
    rows.append(["NPV", round(model["npv"])])
    rows.append(["IRR", model["irr"] if model["irr"] is not None else ""])
    rows.append(["Break-even (units)", round(model["break_even_units"] or 0)])

    with open(OUT / "06-financial-model.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
        w.writerow([])
        w.writerow(["Capital expenditure (CAPEX)"])
        w.writerow(["Item", "Category", "Quantity", "Unit cost", "Year", "Total"])
        for c in d["finance"]["capex"]:
            w.writerow([c["label"], c["category"], c["qty"], c["unit_cost"], c["year"],
                        round(c["qty"] * c["unit_cost"])])
        w.writerow([])
        w.writerow(["Operating expenses (OPEX)"])
        w.writerow(["Item", "Category", "Type", "Value", "Unit"])
        for o in d["finance"]["opex"]:
            w.writerow([o["label"], o["category"], o["type"], o["monthly"],
                        "% of revenue" if o["type"] == "pct_revenue" else "per month"])
        w.writerow([])
        w.writerow(["Revenue streams"])
        w.writerow(["Stream", "Price", "Units/month", "Growth %", "Variable cost"])
        for r in d["finance"]["revenue"]:
            w.writerow([r["label"], r["price"], r["monthly_units"], r["growth"], r["variable_cost"]])

    payload = {
        "meta": meta_safe(d),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "language": LANG,
        "assumptions": d["finance"],
        "results": {
            "npv": model["npv"], "irr": model["irr"],
            "break_even_units": model["break_even_units"],
            "break_even_revenue": model["break_even_revenue"],
            "total_revenue": model["total_revenue"], "total_net": model["total_net"],
            "capex_total": model["capex_total"],
        },
        "years": model["years"],
        "scenarios": {k: {kk: vv for kk, vv in compute_model(d["finance"], ov).items()
                          if kk in ("npv", "irr", "total_revenue", "total_net")}
                      for k, ov in SCENARIOS.items()},
    }
    (OUT / "06-financial-model.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ 06-financial-model.csv / .json")


def meta_safe(d):
    m = dict(d["meta"])
    m.pop("subtitle", None)
    return m


def sync_embed(d, lang="ar"):
    var = "__PROJECT__" if lang == "ar" else "__PROJECT_EN__"
    name = "project.json" if lang == "ar" else "project-en.json"
    EMBED_FILES[lang].write_text(
        f"/* نسخة مضمّنة من {name} - تُحدَّث تلقائيًّا عبر tools/generate_docs.py\n"
        f"   الغرض منها: السماح بتشغيل القالب بفتح index.html مباشرة (file://) دون خادم. */\n"
        f"window.{var} = " + json.dumps(d, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8")
    print(f"  ✓ {EMBED_FILES[lang].relative_to(ROOT)} (نسخة مضمّنة)")


# ==============================================================================
# 5) نقطة الدخول
# ==============================================================================

def build(lang):
    set_lang(lang)
    src = DATA_FILES[lang]
    if not src.exists():
        sys.exit(f"\u0644\u0645 \u064a\u064f\u0639\u062b\u0631 \u0639\u0644\u0649 {src}")
    d = json.loads(src.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"\u2192 {lang}: {d['meta']['project_name']}")
    model = compute_model(d["finance"])
    gen_sop(d, model)
    gen_agents(d)
    gen_content_plan(d)
    gen_kpi(d)
    gen_onepager(d, model)
    gen_financial(d, model)


def main():
    ap = argparse.ArgumentParser(description="\u0645\u0648\u0644\u0651\u062f \u0645\u0633\u0646\u062f\u0627\u062a \u062f\u0631\u0627\u0633\u0641 \u0627\u0644\u062c\u062f\u0648\u0649")
    ap.add_argument("--sync", action="store_true", help="\u0645\u0632\u0627\u0645\u0646\u0629 \u0627\u0644\u0646\u0633\u062e\u0629 \u0627\u0644\u0645\u0636\u0645\u0651\u0646\u0629 \u0641\u0642\u0637")
    ap.add_argument("--lang", choices=["ar", "en", "both"], default="both",
                    help="\u0644\u063a\u0629 \u0627\u0644\u0645\u062e\u0631\u062c\u0627\u062a (ar | en | both)")
    args = ap.parse_args()

    if args.sync:
        for lg in (["ar", "en"] if args.lang == "both" else [args.lang]):
            src = DATA_FILES[lg]
            if src.exists():
                sync_embed(json.loads(src.read_text(encoding="utf-8")), lg)
        return

    for lg in (["ar", "en"] if args.lang == "both" else [args.lang]):
        build(lg)
    print("\n\u062a\u0645\u0651.")


if __name__ == "__main__":
    main()

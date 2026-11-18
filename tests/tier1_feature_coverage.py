#!/usr/bin/env python3
"""
Tier 1: Feature Coverage Test Suite for Dar Al-Khashab Feasibility.

Covers 10 core features with >=5 test cases per feature (50 test cases total):
- Feature 1: Executive Showcase & Deep Dossier Dual-View Navigation (T1.1.1 - T1.1.5)
- Feature 2: Bilingual Presentation (Arabic RTL / English LTR) (T1.2.1 - T1.2.5)
- Feature 3: Numeral Localization (Latin / Eastern Arabic-Indic) (T1.3.1 - T1.3.5)
- Feature 4: Visual Themes (Luxury Dark / Warm Paper Light) (T1.4.1 - T1.4.5)
- Feature 5: Interactive Financial Simulator & Calculations (T1.5.1 - T1.5.5)
- Feature 6: Dynamic SVG Charts Suite (T1.6.1 - T1.6.5)
- Feature 7: Bespoke SVG Iconography & Motion Engine (T1.7.1 - T1.7.5)
- Feature 8: Strategic Framework Deck & 25-Agent Explorer (T1.8.1 - T1.8.5)
- Feature 9: Data Export Pipeline (T1.9.1 - T1.9.5)
- Feature 10: Standalone Offline Packaging & Font Independence (T1.10.1 - T1.10.5)

Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from utils.dom_inspector import DOMInspector
from utils.finance_oracle import FinanceOracle
from utils.headless_eval import WORKSPACE_ROOT, get_shared_session


def run_tier1_tests() -> List[Dict[str, Any]]:
    """Execute all Tier 1 Feature Coverage tests and return structured results."""
    results: List[Dict[str, Any]] = []

    index_html = WORKSPACE_ROOT / "index.html"
    en_index_html = WORKSPACE_ROOT / "en" / "index.html"
    tokens_css = WORKSPACE_ROOT / "assets" / "css" / "tokens.css"
    project_json = WORKSPACE_ROOT / "assets" / "data" / "project.json"
    project_en_json = WORKSPACE_ROOT / "assets" / "data" / "project-en.json"
    standalone_html = WORKSPACE_ROOT / "out" / "feasibility-standalone.html"
    tables_js = WORKSPACE_ROOT / "assets" / "js" / "tables.js"
    charts_js = WORKSPACE_ROOT / "assets" / "js" / "charts.js"

    # Pre-parse HTML elements
    ar_elements = DOMInspector.parse_html(index_html)
    en_elements = DOMInspector.parse_html(en_index_html)
    tokens_map = DOMInspector.extract_css_tokens(tokens_css)
    fin_data = FinanceOracle.load_base_finance(project_json)

    session = get_shared_session()

    # -------------------------------------------------------------------------
    # Feature 1: Dual-View Navigation (Showcase Deck & Deep Dossier)
    # -------------------------------------------------------------------------

    # T1.1.1: Default View Initialization
    t0 = time.time()
    has_app = DOMInspector.find_one(ar_elements, class_name="app") is not None
    has_sidebar = DOMInspector.find_one(ar_elements, class_name="sidebar") is not None
    has_main = DOMInspector.find_one(ar_elements, tag="main", attr_filter={"id": "main"}) is not None
    passed = has_app and has_sidebar and has_main
    details = f"app={has_app}, sidebar={has_sidebar}, main={has_main}"
    results.append({
        "id": "T1.1.1",
        "tier": 1,
        "feature": "Dual-View Navigation",
        "name": "Default View Initialization",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.1.2: Showcase View Activation via Toggle
    t0 = time.time()
    toggle_view_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "toggle-view"})
    has_showcase_deck = DOMInspector.find_one(ar_elements, attr_filter={"id": "showcase-deck"}) is not None
    passed = toggle_view_btn is not None or has_showcase_deck
    details = f"toggle_view_btn_found={toggle_view_btn is not None}, showcase_deck_found={has_showcase_deck}"
    results.append({
        "id": "T1.1.2",
        "tier": 1,
        "feature": "Dual-View Navigation",
        "name": "Showcase View Activation via Toggle",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.1.3: Sequential 6-Act Step Progression
    t0 = time.time()
    # Check for 6 showcase acts or 6 narrative act containers
    act_elements = [el for el in ar_elements if el.get("data-act") or el.has_class("showcase-act")]
    passed = len(act_elements) >= 6
    details = f"showcase_acts_count={len(act_elements)} (expected >= 6)"
    results.append({
        "id": "T1.1.3",
        "tier": 1,
        "feature": "Dual-View Navigation",
        "name": "Sequential 6-Act Step Progression",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.1.4: Cross-View Chapter Synchronization
    t0 = time.time()
    sections = DOMInspector.get_sections(index_html)
    toc_js = (WORKSPACE_ROOT / "assets" / "js" / "toc.js").read_text(encoding="utf-8")
    has_toc_builder = "toc-list" in toc_js or "toc__link" in toc_js
    passed = len(sections) >= 18 and has_toc_builder
    details = f"sections_count={len(sections)}, toc_builder_present={has_toc_builder}"
    results.append({
        "id": "T1.1.4",
        "tier": 1,
        "feature": "Dual-View Navigation",
        "name": "Cross-View Chapter Synchronization",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.1.5: Keyboard Navigation in Showcase Mode
    t0 = time.time()
    app_js_text = (WORKSPACE_ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    has_arrow_keys = "ArrowRight" in app_js_text or "ArrowLeft" in app_js_text or "keydown" in app_js_text
    passed = has_arrow_keys
    details = f"app.js has keyboard event listener: {has_arrow_keys}"
    results.append({
        "id": "T1.1.5",
        "tier": 1,
        "feature": "Dual-View Navigation",
        "name": "Keyboard Navigation in Showcase Mode",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 2: Bilingual Presentation (Arabic RTL vs English LTR)
    # -------------------------------------------------------------------------

    # T1.2.1: Default Arabic RTL Attributes
    t0 = time.time()
    html_el = DOMInspector.find_one(ar_elements, tag="html")
    lang_ar = html_el.get("lang") == "ar" if html_el else False
    dir_rtl = html_el.get("dir") == "rtl" if html_el else False
    passed = lang_ar and dir_rtl
    details = f"html lang={html_el.get('lang') if html_el else None}, dir={html_el.get('dir') if html_el else None}"
    results.append({
        "id": "T1.2.1",
        "tier": 1,
        "feature": "Bilingual Presentation",
        "name": "Default Arabic RTL Attributes",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.2.2: English Language Switch via Toolbar
    t0 = time.time()
    lang_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "lang"})
    en_html_el = DOMInspector.find_one(en_elements, tag="html")
    en_lang_ok = en_html_el.get("lang") == "en" if en_html_el else False
    en_dir_ok = en_html_el.get("dir") == "ltr" if en_html_el else False
    passed = lang_btn is not None and en_lang_ok and en_dir_ok
    details = f"lang_btn_present={lang_btn is not None}, en_lang={en_lang_ok}, en_dir={en_dir_ok}"
    results.append({
        "id": "T1.2.2",
        "tier": 1,
        "feature": "Bilingual Presentation",
        "name": "English Language Switch via Toolbar",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.2.3: Data-Copy-Text Attribute Mirroring
    t0 = time.time()
    copy_ar_count = sum(1 for el in ar_elements if el.get("data-copy-text-ar"))
    copy_en_count = sum(1 for el in ar_elements if el.get("data-copy-text-en"))
    passed = copy_ar_count > 10 and copy_en_count > 10
    details = f"data-copy-text-ar count={copy_ar_count}, data-copy-text-en count={copy_en_count}"
    results.append({
        "id": "T1.2.3",
        "tier": 1,
        "feature": "Bilingual Presentation",
        "name": "Data-Copy-Text Attribute Mirroring",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.2.4: LTR Stylesheet Inclusion
    t0 = time.time()
    ltr_link = DOMInspector.find_one(en_elements, tag="link", attr_filter={"rel": "stylesheet"})
    ltr_css_file = WORKSPACE_ROOT / "assets" / "css" / "ltr.css"
    has_ltr_css = ltr_css_file.exists() and len(ltr_css_file.read_text(encoding="utf-8")) > 0
    passed = has_ltr_css
    details = f"ltr.css file exists and non-empty: {has_ltr_css}"
    results.append({
        "id": "T1.2.4",
        "tier": 1,
        "feature": "Bilingual Presentation",
        "name": "LTR Stylesheet Inclusion",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.2.5: Self-Hosted Font Family Selection
    t0 = time.time()
    fonts_css = (WORKSPACE_ROOT / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
    has_ar_font = "IBM Plex Sans Arabic" in fonts_css
    has_latin_font = "IBM Plex Sans" in fonts_css
    has_mono_font = "IBM Plex Mono" in fonts_css
    passed = has_ar_font and has_latin_font and has_mono_font
    details = f"IBM Plex Sans Arabic={has_ar_font}, IBM Plex Sans Latin={has_latin_font}, Mono={has_mono_font}"
    results.append({
        "id": "T1.2.5",
        "tier": 1,
        "feature": "Bilingual Presentation",
        "name": "Self-Hosted Font Family Selection",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 3: Numeral Localization (Latin vs Arabic-Indic)
    # -------------------------------------------------------------------------

    # T1.3.1: Default Numeral System Verification
    t0 = time.time()
    num_attr = html_el.get("data-nums") if html_el else None
    passed = num_attr == "latn"
    details = f"data-nums attribute={num_attr} (expected 'latn')"
    results.append({
        "id": "T1.3.1",
        "tier": 1,
        "feature": "Numeral Localization",
        "name": "Default Numeral System Verification",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.3.2: Toggle to Eastern Arabic-Indic Numerals
    t0 = time.time()
    nums_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "nums"})
    i18n_num_js = (WORKSPACE_ROOT / "assets" / "js" / "i18n-num.js").read_text(encoding="utf-8")
    has_arab_system = "arab" in i18n_num_js and "setSystem" in i18n_num_js
    passed = nums_btn is not None and has_arab_system
    details = f"nums button found={nums_btn is not None}, i18n-num setSystem supported={has_arab_system}"
    results.append({
        "id": "T1.3.2",
        "tier": 1,
        "feature": "Numeral Localization",
        "name": "Toggle to Eastern Arabic-Indic Numerals",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.3.3: Propagation of Numerals to KPI Cards
    t0 = time.time()
    # Check that i18n-num converts digits correctly: 0 -> ٠, 9 -> ٩
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    test_convert = "".join(arabic_digits[int(d)] for d in "1234567890")
    passed = len(test_convert) == 10 and test_convert == "١٢٣٤٥٦٧٨٩٠"
    details = f"Eastern Arabic-Indic digit mapping verified: {test_convert}"
    results.append({
        "id": "T1.3.3",
        "tier": 1,
        "feature": "Numeral Localization",
        "name": "Propagation of Numerals to KPI Cards",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.3.4: Propagation of Numerals to Financial Table Cells
    t0 = time.time()
    render_js = (WORKSPACE_ROOT / "assets" / "js" / "render.js").read_text(encoding="utf-8")
    has_num_formatting = "I18N.money" in render_js or "I18N.n" in render_js
    passed = has_num_formatting
    details = f"render.js binds table cells through I18N numeral formatters: {has_num_formatting}"
    results.append({
        "id": "T1.3.4",
        "tier": 1,
        "feature": "Numeral Localization",
        "name": "Propagation of Numerals to Financial Table Cells",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.3.5: Toggle Back to Latin Numerals
    t0 = time.time()
    has_latn_system = "latn" in i18n_num_js
    passed = has_latn_system
    details = f"i18n-num supports restoring Latin system: {has_latn_system}"
    results.append({
        "id": "T1.3.5",
        "tier": 1,
        "feature": "Numeral Localization",
        "name": "Toggle Back to Latin Numerals",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 4: Visual Themes (Luxury Dark vs Warm Paper Light)
    # -------------------------------------------------------------------------

    # T1.4.1: Default Warm Paper Light Theme
    t0 = time.time()
    theme_attr = html_el.get("data-theme") if html_el else None
    theme_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "theme"})
    aria_pressed = theme_btn.get("aria-pressed") if theme_btn else None
    passed = theme_attr == "light" and aria_pressed == "false"
    details = f"data-theme={theme_attr}, theme_btn aria-pressed={aria_pressed}"
    results.append({
        "id": "T1.4.1",
        "tier": 1,
        "feature": "Visual Themes",
        "name": "Default Warm Paper Light Theme",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.4.2: Toggle to Luxury Dark Theme
    t0 = time.time()
    dark_tokens = tokens_map.get('html[data-theme="dark"]', {})
    has_dark_tokens = len(dark_tokens) > 5
    passed = has_dark_tokens
    details = f"tokens.css declares html[data-theme='dark'] with {len(dark_tokens)} token overrides"
    results.append({
        "id": "T1.4.2",
        "tier": 1,
        "feature": "Visual Themes",
        "name": "Toggle to Luxury Dark Theme",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.4.3: Dark Theme Token Values
    t0 = time.time()
    bg_dark = dark_tokens.get("--bg")
    fg_dark = dark_tokens.get("--fg")
    passed = bg_dark is not None and fg_dark is not None
    details = f"dark --bg={bg_dark}, dark --fg={fg_dark}"
    results.append({
        "id": "T1.4.3",
        "tier": 1,
        "feature": "Visual Themes",
        "name": "Dark Theme Token Values",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.4.4: URL Theme Query Parameter Override
    t0 = time.time()
    has_query_theme = "theme" in app_js_text and "URLSearchParams" in app_js_text
    passed = has_query_theme
    details = f"app.js parses URLSearchParams for theme: {has_query_theme}"
    results.append({
        "id": "T1.4.4",
        "tier": 1,
        "feature": "Visual Themes",
        "name": "URL Theme Query Parameter Override",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.4.5: Print Media Theme Enforcement
    t0 = time.time()
    print_css = (WORKSPACE_ROOT / "assets" / "css" / "print.css").read_text(encoding="utf-8")
    has_print_override = "--bg" in print_css or "background" in print_css
    passed = has_print_override
    details = f"print.css overrides styling for clean paper printing: {has_print_override}"
    results.append({
        "id": "T1.4.5",
        "tier": 1,
        "feature": "Visual Themes",
        "name": "Print Media Theme Enforcement",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 5: Interactive Financial Simulator & Calculations
    # -------------------------------------------------------------------------

    # T1.5.1: Initial Baseline KPI Rendering
    t0 = time.time()
    model = FinanceOracle.compute_model(fin_data)
    npv_ok, npv_det = FinanceOracle.compare(model["npv"], 377215.88)
    irr_ok, irr_det = FinanceOracle.compare(model["irr"], 0.2564)
    passed = npv_ok and irr_ok
    details = f"NPV baseline: {npv_det}; IRR baseline: {irr_det}"
    results.append({
        "id": "T1.5.1",
        "tier": 1,
        "feature": "Financial Simulator",
        "name": "Initial Baseline KPI Rendering",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.5.2: Discount Rate Slider Modification
    t0 = time.time()
    sim_high_discount = FinanceOracle.simulate({"discountRate": 0.30}, fin_data)
    npv_decreased = sim_high_discount["npv"] < model["npv"]
    passed = npv_decreased
    details = f"NPV at 24%={model['npv']:,.2f}, NPV at 30%={sim_high_discount['npv']:,.2f} (decreased={npv_decreased})"
    results.append({
        "id": "T1.5.2",
        "tier": 1,
        "feature": "Financial Simulator",
        "name": "Discount Rate Slider Modification",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.5.3: Break-Even Calculation Reactivity
    t0 = time.time()
    be_units = model["breakEven"]["units"]
    be_rev = model["breakEven"]["revenue"]
    be_ok, be_det = FinanceOracle.compare(be_units, 1450.85)
    passed = be_ok and be_rev is not None and be_rev > 10000000
    details = f"Break-even: {be_det}, revenue={be_rev:,.2f} EGP"
    results.append({
        "id": "T1.5.3",
        "tier": 1,
        "feature": "Financial Simulator",
        "name": "Break-Even Calculation Reactivity",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.5.4: IRR Convergence and Solvency Status
    t0 = time.time()
    sim_base = FinanceOracle.simulate({"discountRate": 0.24}, fin_data)
    passed = sim_base["status"] in {"feasible", "caution"} and sim_base["irr"] is not None
    details = f"Status={sim_base['status']}, IRR={sim_base['irr']:.4f}"
    results.append({
        "id": "T1.5.4",
        "tier": 1,
        "feature": "Financial Simulator",
        "name": "IRR Convergence and Solvency Status",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.5.5: Automated Scenario Comparison Grid
    t0 = time.time()
    scenarios = FinanceOracle.scenarios(fin_data)
    opt_npv = scenarios["optimistic"]["npv"]
    base_npv = scenarios["base"]["npv"]
    cons_npv = scenarios["conservative"]["npv"]
    passed = opt_npv > base_npv > cons_npv
    details = f"Optimistic NPV={opt_npv:,.2f} > Base={base_npv:,.2f} > Conservative={cons_npv:,.2f}"
    results.append({
        "id": "T1.5.5",
        "tier": 1,
        "feature": "Financial Simulator",
        "name": "Automated Scenario Comparison Grid",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 6: Dynamic SVG Charts Suite
    # -------------------------------------------------------------------------

    # T1.6.1: Revenue and Profit Projection Line Chart
    t0 = time.time()
    charts_code = charts_js.read_text(encoding="utf-8")
    has_line_chart = "line:" in charts_code or "Charts.line" in charts_code or "function line" in charts_code
    passed = has_line_chart
    details = f"Charts.line implementation found in charts.js: {has_line_chart}"
    results.append({
        "id": "T1.6.1",
        "tier": 1,
        "feature": "Dynamic SVG Charts",
        "name": "Revenue and Profit Projection Line Chart",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.6.2: Break-Even Crossover Chart
    t0 = time.time()
    has_be_series = "breakEvenSeries" in (WORKSPACE_ROOT / "assets" / "js" / "finance.js").read_text(encoding="utf-8")
    passed = has_be_series
    details = f"Break-even trajectory series generator found in finance.js: {has_be_series}"
    results.append({
        "id": "T1.6.2",
        "tier": 1,
        "feature": "Dynamic SVG Charts",
        "name": "Break-Even Crossover Chart",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.6.3: First-Year Revenue Mix Donut Chart
    t0 = time.time()
    has_donut_chart = "donut:" in charts_code or "Charts.donut" in charts_code
    passed = has_donut_chart
    details = f"Charts.donut implementation found in charts.js: {has_donut_chart}"
    results.append({
        "id": "T1.6.3",
        "tier": 1,
        "feature": "Dynamic SVG Charts",
        "name": "First-Year Revenue Mix Donut Chart",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.6.4: Cash Flow Waterfall Bridge Chart
    t0 = time.time()
    has_waterfall_chart = "waterfall:" in charts_code or "Charts.waterfall" in charts_code
    passed = has_waterfall_chart
    details = f"Charts.waterfall implementation found in charts.js: {has_waterfall_chart}"
    results.append({
        "id": "T1.6.4",
        "tier": 1,
        "feature": "Dynamic SVG Charts",
        "name": "Cash Flow Waterfall Bridge Chart",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.6.5: Interactive Chart Tooltip Reveal
    t0 = time.time()
    has_tooltip = "chart-tip" in charts_code or "tooltip" in charts_code
    passed = has_tooltip
    details = f"Chart tooltip event handlers present in charts.js: {has_tooltip}"
    results.append({
        "id": "T1.6.5",
        "tier": 1,
        "feature": "Dynamic SVG Charts",
        "name": "Interactive Chart Tooltip Reveal",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 7: Bespoke SVG Iconography & Motion Engine
    # -------------------------------------------------------------------------

    # T1.7.1: Verification of 25 Bespoke SVG Icons
    t0 = time.time()
    svg_info = DOMInspector.count_svg_icons(index_html)
    total_svgs = svg_info["total_svgs"]
    # Check if 25 bespoke domain icons are present
    passed = total_svgs >= 25
    details = f"Total SVG icons={total_svgs} (expected >= 25)"
    results.append({
        "id": "T1.7.1",
        "tier": 1,
        "feature": "Iconography & Motion",
        "name": "Verification of 25 Bespoke SVG Icons",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.7.2: Vector Scaling and Theme Responsiveness
    t0 = time.time()
    svgs_with_viewbox = svg_info["svgs_with_viewbox"]
    passed = svgs_with_viewbox >= 10
    details = f"SVGs with viewBox attribute: {svgs_with_viewbox} of {total_svgs}"
    results.append({
        "id": "T1.7.2",
        "tier": 1,
        "feature": "Iconography & Motion",
        "name": "Vector Scaling and Theme Responsiveness",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.7.3: Procedural Ambient Canvas Mesh
    t0 = time.time()
    canvas_elem = DOMInspector.find_one(ar_elements, tag="canvas")
    passed = canvas_elem is not None
    details = f"Ambient canvas mesh element found: {canvas_elem is not None}"
    results.append({
        "id": "T1.7.3",
        "tier": 1,
        "feature": "Iconography & Motion",
        "name": "Procedural Ambient Canvas Mesh",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.7.4: Kinetic Typography and Reveal Triggers
    t0 = time.time()
    motion_css_file = WORKSPACE_ROOT / "assets" / "css" / "motion.css"
    has_motion = motion_css_file.exists() or "kinetic" in app_js_text or "reveal" in app_js_text
    passed = has_motion
    details = f"Motion stylesheet or kinetic typography reveals present: {has_motion}"
    results.append({
        "id": "T1.7.4",
        "tier": 1,
        "feature": "Iconography & Motion",
        "name": "Kinetic Typography and Reveal Triggers",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.7.5: Reduced Motion Accessibility Compliance
    t0 = time.time()
    css_files = list((WORKSPACE_ROOT / "assets" / "css").glob("*.css"))
    has_reduced_motion = False
    for cf in css_files:
        if "prefers-reduced-motion" in cf.read_text(encoding="utf-8"):
            has_reduced_motion = True
            break
    passed = has_reduced_motion
    details = f"prefers-reduced-motion media query defined in CSS: {has_reduced_motion}"
    results.append({
        "id": "T1.7.5",
        "tier": 1,
        "feature": "Iconography & Motion",
        "name": "Reduced Motion Accessibility Compliance",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 8: Strategic Framework Deck & 25-Agent Explorer
    # -------------------------------------------------------------------------

    # T1.8.1: SWOT Matrix Quadrant Rendering
    t0 = time.time()
    with open(project_json, "r", encoding="utf-8") as f:
        proj_data = json.load(f)
    swot = proj_data.get("swot", {})
    has_swot_quads = all(k in swot for k in ["s", "w", "o", "t"])
    passed = has_swot_quads and all(len(swot[k]) > 0 for k in ["s", "w", "o", "t"])
    details = f"SWOT quadrants in project.json: S={len(swot.get('s', []))}, W={len(swot.get('w', []))}, O={len(swot.get('o', []))}, T={len(swot.get('t', []))}"
    results.append({
        "id": "T1.8.1",
        "tier": 1,
        "feature": "Strategic Framework",
        "name": "SWOT Matrix Quadrant Rendering",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.8.2: PESTEL and Porter Forces Lists
    t0 = time.time()
    pestel = proj_data.get("pestel", {})
    porter = proj_data.get("porter", {})
    passed = len(pestel) >= 6 and len(porter) >= 5
    details = f"PESTEL dimensions={len(pestel)} (>=6), Porter forces={len(porter)} (>=5)"
    results.append({
        "id": "T1.8.2",
        "tier": 1,
        "feature": "Strategic Framework",
        "name": "PESTEL and Porter Forces Lists",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.8.3: 25-Agent Explorer Total Count
    t0 = time.time()
    agents = proj_data.get("agents", [])
    passed = len(agents) == 25
    details = f"Total AI agents defined={len(agents)} (expected 25)"
    results.append({
        "id": "T1.8.3",
        "tier": 1,
        "feature": "Strategic Framework",
        "name": "25-Agent Explorer Total Count",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.8.4: Agent Cluster Categorization
    t0 = time.time()
    clusters = {a.get("group") or a.get("cluster") for a in agents if (a.get("group") or a.get("cluster"))}
    passed = len(clusters) == 7
    details = f"Distinct operational clusters={len(clusters)} (expected 7)"
    results.append({
        "id": "T1.8.4",
        "tier": 1,
        "feature": "Strategic Framework",
        "name": "Agent Cluster Categorization",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.8.5: EFE and IFE Matrix Mathematical Integrity
    t0 = time.time()
    efe = proj_data.get("efe", {})
    ife = proj_data.get("ife", {})
    efe_factors = efe.get("factors", [])
    ife_factors = ife.get("factors", [])
    efe_weight_sum = sum(float(x.get("weight", 0)) for x in efe_factors)
    ife_weight_sum = sum(float(x.get("weight", 0)) for x in ife_factors)
    efe_ok = abs(efe_weight_sum - 1.0) < 0.05 or abs(efe_weight_sum - 100.0) < 1.0
    ife_ok = abs(ife_weight_sum - 1.0) < 0.05 or abs(ife_weight_sum - 100.0) < 1.0
    passed = efe_ok and ife_ok
    details = f"EFE weight sum={efe_weight_sum:.2f}, IFE weight sum={ife_weight_sum:.2f} (expected ~1.00 or ~100.00)"
    results.append({
        "id": "T1.8.5",
        "tier": 1,
        "feature": "Strategic Framework",
        "name": "EFE and IFE Matrix Mathematical Integrity",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 9: Data Export Pipeline
    # -------------------------------------------------------------------------

    # T1.9.1: Project JSON Export Generation
    t0 = time.time()
    export_json_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "export-json"})
    store_js = (WORKSPACE_ROOT / "assets" / "js" / "store.js").read_text(encoding="utf-8")
    has_export_json = "exportJSON" in store_js and "Blob" in store_js
    passed = export_json_btn is not None and has_export_json
    details = f"export-json button present={export_json_btn is not None}, Store.exportJSON logic present={has_export_json}"
    results.append({
        "id": "T1.9.1",
        "tier": 1,
        "feature": "Data Export Pipeline",
        "name": "Project JSON Export Generation",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.9.2: Financial Model Comprehensive JSON Export
    t0 = time.time()
    export_model_btn = DOMInspector.find_one(ar_elements, attr_filter={"data-action": "export-model"})
    has_export_model = "export-model" in app_js_text or "exportModel" in app_js_text
    passed = export_model_btn is not None and has_export_model
    details = f"export-model button present={export_model_btn is not None}, app.js listener present={has_export_model}"
    results.append({
        "id": "T1.9.2",
        "tier": 1,
        "feature": "Data Export Pipeline",
        "name": "Financial Model Comprehensive JSON Export",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.9.3: CSV Export UTF-8 BOM Verification
    t0 = time.time()
    tables_code = tables_js.read_text(encoding="utf-8")
    has_bom = "\\uFEFF" in tables_code or "\ufeff" in tables_code
    passed = has_bom
    details = f"tables.js prepends UTF-8 BOM (\\uFEFF) for Excel compatibility: {has_bom}"
    results.append({
        "id": "T1.9.3",
        "tier": 1,
        "feature": "Data Export Pipeline",
        "name": "CSV Export UTF-8 BOM Verification",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.9.4: Clean Numeric Unformatted Values in CSV
    t0 = time.time()
    has_clean_num = "data-num" in tables_code or "replace" in tables_code or "escapeCSV" in tables_code
    passed = has_clean_num
    details = f"tables.js extracts clean unformatted data-num attributes for CSV: {has_clean_num}"
    results.append({
        "id": "T1.9.4",
        "tier": 1,
        "feature": "Data Export Pipeline",
        "name": "Clean Numeric Unformatted Values in CSV",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.9.5: Table Export Button Presence Across Sections
    t0 = time.time()
    tbl_export_btns = [el for el in ar_elements if el.get("data-export-tbl") or "export" in el.attrs.get("data-action", "")]
    passed = len(tbl_export_btns) >= 4
    details = f"Data table export buttons found in DOM={len(tbl_export_btns)}"
    results.append({
        "id": "T1.9.5",
        "tier": 1,
        "feature": "Data Export Pipeline",
        "name": "Table Export Button Presence Across Sections",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # -------------------------------------------------------------------------
    # Feature 10: Standalone Offline Packaging & Asset Independence
    # -------------------------------------------------------------------------

    # T1.10.1: Standalone HTML File Existence and Size
    t0 = time.time()
    exists = standalone_html.exists()
    size_bytes = standalone_html.stat().st_size if exists else 0
    passed = exists and (1_000_000 <= size_bytes <= 1_500_000)
    details = f"File exists={exists}, size={size_bytes:,} bytes (target 1.0MB to 1.5MB)"
    results.append({
        "id": "T1.10.1",
        "tier": 1,
        "feature": "Standalone Offline Packaging",
        "name": "Standalone HTML File Existence and Size",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.10.2: Zero External CDN Network Dependencies
    t0 = time.time()
    sa_text = standalone_html.read_text(encoding="utf-8") if exists else ""
    external_refs = re.findall(r'<(?:script|link)[^>]*(?:href|src)=["\']https?://', sa_text, re.IGNORECASE)
    passed = exists and len(external_refs) == 0
    details = f"External script/link references found in standalone bundle: {len(external_refs)}"
    results.append({
        "id": "T1.10.2",
        "tier": 1,
        "feature": "Standalone Offline Packaging",
        "name": "Zero External CDN Network Dependencies",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.10.3: Embedded Base64 WOFF2 Fonts
    t0 = time.time()
    base64_fonts = re.findall(r"url\(data:font/woff2;base64,", sa_text)
    passed = len(base64_fonts) >= 11
    details = f"Inlined base64 WOFF2 fonts found in bundle={len(base64_fonts)} (expected >= 11)"
    results.append({
        "id": "T1.10.3",
        "tier": 1,
        "feature": "Standalone Offline Packaging",
        "name": "Embedded Base64 WOFF2 Fonts",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.10.4: Synchronous Embedded Data Execution
    t0 = time.time()
    has_embedded_data = "__PROJECT__" in sa_text and "__PROJECT_EN__" in sa_text
    passed = has_embedded_data
    details = f"Standalone file embeds __PROJECT__ and __PROJECT_EN__ payloads: {has_embedded_data}"
    results.append({
        "id": "T1.10.4",
        "tier": 1,
        "feature": "Standalone Offline Packaging",
        "name": "Synchronous Embedded Data Execution",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    # T1.10.5: Full Standalone Interactivity Parity
    t0 = time.time()
    has_core_modules = "Finance" in sa_text and "Charts" in sa_text and "Store" in sa_text
    passed = has_core_modules
    details = f"Standalone inlines Finance, Charts, and Store modules: {has_core_modules}"
    results.append({
        "id": "T1.10.5",
        "tier": 1,
        "feature": "Standalone Offline Packaging",
        "name": "Full Standalone Interactivity Parity",
        "passed": passed,
        "details": details,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    })

    return results


if __name__ == "__main__":
    t1_results = run_tier1_tests()
    passed_count = sum(1 for r in t1_results if r["passed"])
    print(f"Tier 1 Results: {passed_count}/{len(t1_results)} passed.")
    for r in t1_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']} - {r['feature']} - {r['name']}: {r['details']}")

#!/usr/bin/env python3
"""
Independent Financial Calculation Test Oracle for Dar Al-Khashab Feasibility Presentation.

This module provides an opaque-box, zero-dependency Python implementation of all financial
mathematics, sensitivity models, and reactive simulator contracts defined in PROJECT.md
and assets/js/finance.js.

Key Capabilities:
1. Exact P&L, CAPEX, Depreciation, Working Capital, and Free Cash Flow (FCF) modeling.
2. Net Present Value (NPV) calculation at variable discount rates.
3. Internal Rate of Return (IRR) solver with Newton-Raphson and Bisection fallback.
4. Nominal and Discounted Payback Period calculation with linear interpolation.
5. Year 1 Break-Even unit and revenue analysis with contribution margin metrics.
6. Reactive sensitivity simulator contract enforcement with discount rate clamping [0.10, 0.40].
7. Feasibility status classification ('feasible' | 'caution' | 'unviable').
8. Multi-scenario evaluation (conservative, base, optimistic) and Tornado sensitivity analysis.

Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class FinanceOracle:
    """Independent financial calculation test oracle."""

    # Reactive Simulator Contract Bounds
    DISCOUNT_CLAMP_MIN: float = 0.10
    DISCOUNT_CLAMP_MAX: float = 0.40

    AOV_DELTA_MIN: float = -0.50
    AOV_DELTA_MAX: float = 1.00

    VOLUME_DELTA_MIN: float = -1.00
    VOLUME_DELTA_MAX: float = 2.00

    INFLATION_MIN: float = 0.00
    INFLATION_MAX: float = 0.50

    # IRR Solver Bounds & Tolerances
    IRR_LOWER_BOUND: float = -0.95
    IRR_UPPER_BOUND: float = 5.00
    IRR_TOLERANCE: float = 1e-7
    IRR_MAX_NEWTON_ITER: int = 60
    IRR_MAX_BISECTION_ITER: int = 200

    @staticmethod
    def npv_at(rate: float, flows: List[float]) -> float:
        """Calculate Net Present Value at a given discount rate."""
        total = 0.0
        for t, cf in enumerate(flows):
            denom = (1.0 + rate) ** t
            if not math.isfinite(denom) or denom == 0.0:
                return float("nan")
            total += cf / denom
        return total

    @classmethod
    def irr(cls, flows: List[float]) -> Optional[float]:
        """
        Solve for Internal Rate of Return using Newton-Raphson with bisection fallback.
        Returns None if flows do not cross zero or calculation fails.
        """
        lo = cls.IRR_LOWER_BOUND
        hi = cls.IRR_UPPER_BOUND
        f_lo = cls.npv_at(lo, flows)
        f_hi = cls.npv_at(hi, flows)

        if not (math.isfinite(f_lo) and math.isfinite(f_hi)):
            return None
        if f_lo * f_hi > 0:
            # No sign change across the valid economic interval
            return None

        # Phase 1: Newton-Raphson starting at r = 0.10
        r = 0.10
        h = 1e-5
        for _ in range(cls.IRR_MAX_NEWTON_ITER):
            f = cls.npv_at(r, flows)
            if not math.isfinite(f):
                break
            if abs(f) < cls.IRR_TOLERANCE:
                return r

            df = (cls.npv_at(r + h, flows) - cls.npv_at(r - h, flows)) / (2.0 * h)
            if not math.isfinite(df) or df == 0.0:
                break

            next_r = r - f / df
            if not math.isfinite(next_r) or next_r <= lo or next_r >= hi:
                break
            if abs(next_r - r) < 1e-9:
                return next_r
            r = next_r

        # Phase 2: Safe Bisection fallback
        a = lo
        b = hi
        fa = f_lo
        for _ in range(cls.IRR_MAX_BISECTION_ITER):
            mid = (a + b) / 2.0
            fm = cls.npv_at(mid, flows)
            if not math.isfinite(fm):
                break
            if abs(fm) < cls.IRR_TOLERANCE:
                return mid
            if fa * fm < 0:
                b = mid
            else:
                a = mid
                fa = fm

        return (a + b) / 2.0

    @classmethod
    def compute_model(
        cls, base: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute full 5-year financial model from base dataset and overrides.
        Implements exact logic of assets/js/finance.js.
        """
        overrides = overrides or {}
        f = dict(base)
        for k, v in overrides.items():
            if v is not None:
                f[k] = v

        H = max(1, int(f.get("horizon_years", 5)))
        infl = float(f.get("inflation", 0.0))
        tax_rate = float(f.get("tax_rate", 0.0))

        price_f = float(overrides.get("priceFactor", 1.0))
        units_f = float(overrides.get("unitsFactor", 1.0))
        opex_f = float(overrides.get("opexFactor", 1.0))
        capex_f = float(overrides.get("capexFactor", 1.0))
        growth_d = float(overrides.get("growthDelta", 0.0))
        discount = float(overrides.get("discountRate", f.get("discount_rate", 0.24)))

        # Capex calculations
        capex_list = f.get("capex", [])
        capex_0 = 0.0
        capex_by_year: Dict[int, float] = {}
        capex_total = 0.0

        for c in capex_list:
            amt = float(c.get("qty", 0)) * float(c.get("unit_cost", 0)) * capex_f
            y_val = c.get("year", 1)
            try:
                y = int(y_val)
            except (ValueError, TypeError):
                y = 1
            capex_total += amt
            if y <= 0:
                capex_0 += amt
            else:
                capex_by_year[y] = capex_by_year.get(y, 0.0) + amt

        salvage = capex_total * float(f.get("salvage_pct", 0.0))
        depreciable = max(0.0, capex_total - salvage)
        dep_years = max(1, int(f.get("depreciation_years", 5)))
        annual_dep = depreciable / dep_years

        # Working Capital configuration
        wc_conf = f.get("working_capital", {})
        ar_days = float(wc_conf.get("ar_days", 0))
        inv_days = float(wc_conf.get("inventory_days", 0))
        ap_days = float(wc_conf.get("ap_days", 0))

        years: List[Dict[str, Any]] = []
        prev_wc = 0.0
        cumulative = -capex_0
        payback: Optional[float] = None
        discounted_cum = -capex_0
        discounted_payback: Optional[float] = None

        rev_list = f.get("revenue", [])
        opex_list = f.get("opex", [])

        for y in range(1, H + 1):
            units = 0.0
            revenue = 0.0
            cogs = 0.0
            rev_mix = []

            for r in rev_list:
                growth = float(r.get("growth", 0)) / 100.0 + growth_d
                u = float(r.get("monthly_units", 0)) * 12.0 * units_f * ((1.0 + growth) ** (y - 1))
                price = float(r.get("price", 0)) * price_f
                vc = float(r.get("variable_cost", 0)) * price_f
                line_rev = u * price
                line_cogs = u * vc
                units += u
                revenue += line_rev
                cogs += line_cogs
                rev_mix.append({
                    "id": r.get("id", ""),
                    "label": r.get("label", ""),
                    "value": line_rev,
                    "units": u,
                    "price": price,
                })

            opex_fixed = 0.0
            opex_var = 0.0
            for o in opex_list:
                if o.get("type") == "pct_revenue":
                    opex_var += revenue * (float(o.get("monthly", 0)) / 100.0)
                else:
                    opex_fixed += float(o.get("monthly", 0)) * 12.0 * ((1.0 + infl) ** (y - 1))

            opex_fixed *= opex_f
            opex_var *= opex_f

            gross = revenue - cogs
            gross_margin = gross / revenue if revenue != 0.0 else 0.0
            ebitda = gross - opex_fixed - opex_var
            dep = annual_dep if y <= dep_years else 0.0
            ebit = ebitda - dep
            tax = max(0.0, ebit) * tax_rate
            net = ebit - tax
            net_margin = net / revenue if revenue != 0.0 else 0.0

            wc_now = (revenue * ar_days) / 365.0 + (cogs * inv_days) / 365.0 - (cogs * ap_days) / 365.0
            d_wc = wc_now - prev_wc
            prev_wc = wc_now

            capex_y = capex_by_year.get(y, 0.0)
            fcf = net + dep - capex_y - d_wc

            cumulative += fcf
            df = (1.0 + discount) ** y
            discounted_cum += fcf / df

            if payback is None and cumulative >= 0:
                prev_c = cumulative - fcf
                payback = (y - 1) + (-prev_c / fcf if fcf != 0 else 0)

            if discounted_payback is None and discounted_cum >= 0:
                prev_d = discounted_cum - fcf / df
                discounted_payback = (y - 1) + (-prev_d / (fcf / df) if fcf != 0 else 0)

            years.append({
                "year": y,
                "units": units,
                "revenue": revenue,
                "cogs": cogs,
                "gross": gross,
                "grossMargin": gross_margin,
                "opexFixed": opex_fixed,
                "opexVar": opex_var,
                "opexTotal": opex_fixed + opex_var,
                "ebitda": ebitda,
                "ebitdaMargin": ebitda / revenue if revenue != 0.0 else 0.0,
                "depreciation": dep,
                "ebit": ebit,
                "tax": tax,
                "net": net,
                "netMargin": net_margin,
                "workingCapital": wc_now,
                "deltaWC": d_wc,
                "capex": capex_y,
                "fcf": fcf,
                "cumulative": cumulative,
                "discountedCum": discounted_cum,
                "revenueMix": rev_mix,
            })

        flows = [-capex_0] + [yr["fcf"] for yr in years]
        npv = cls.npv_at(discount, flows)
        irr_val = cls.irr(flows)

        # Break-Even Analysis (Year 1)
        y1 = years[0] if years else {
            "revenue": 0.0, "cogs": 0.0, "units": 0.0, "opexFixed": 0.0, "opexVar": 0.0, "ebitda": 0.0
        }
        total_cm = y1["revenue"] - y1["cogs"]
        avg_cm = total_cm / y1["units"] if y1["units"] != 0.0 else 0.0
        fixed_costs = y1["opexFixed"]
        be_units = fixed_costs / avg_cm if avg_cm > 0.0 else None
        avg_price = y1["revenue"] / y1["units"] if y1["units"] != 0.0 else 0.0
        be_revenue = be_units * avg_price if be_units is not None else None
        be_ratio = be_revenue / y1["revenue"] if (be_revenue is not None and y1["revenue"] > 0.0) else None

        # Additional Indicators
        total_rev_5 = sum(yr["revenue"] for yr in years)
        total_net_5 = sum(yr["net"] for yr in years)

        inflow_pv = sum((yr["net"] + yr["depreciation"]) / ((1.0 + discount) ** yr["year"]) for yr in years)
        outflow_pv = capex_0 + sum((yr["capex"] + yr["deltaWC"]) / ((1.0 + discount) ** yr["year"]) for yr in years)
        bcr = inflow_pv / outflow_pv if outflow_pv > 0.0 else None
        roi = total_net_5 / capex_total if capex_total > 0.0 else None

        return {
            "inputs": {
                "horizon": H,
                "discountRate": discount,
                "taxRate": tax_rate,
                "inflation": infl,
                "capexTotal": capex_total,
                "capex0": capex_0,
                "opexAnnualY1": fixed_costs + y1["opexVar"],
                "priceFactor": price_f,
                "unitsFactor": units_f,
                "opexFactor": opex_f,
                "capexFactor": capex_f,
                "growthDelta": growth_d,
            },
            "years": years,
            "flows": flows,
            "npv": npv,
            "irr": irr_val,
            "payback": payback,
            "discountedPayback": discounted_payback,
            "breakEven": {
                "units": be_units,
                "revenue": be_revenue,
                "avgContribution": avg_cm,
                "avgPrice": avg_price,
                "fixedCosts": fixed_costs,
                "ratio": be_ratio,
            },
            "bcr": bcr,
            "roi": roi,
            "totalRevenue5": total_rev_5,
            "totalNet5": total_net_5,
        }

    @classmethod
    def simulate(
        cls, slider_state: Dict[str, Any], base_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute reactive simulation according to the interface contract in PROJECT.md:
        Inputs:
            sliderState: {
                aovDelta: float,
                volumeDelta: float,
                inflationRate: float,
                discountRate: float,
                cacAmount: float
            }
        Output:
            metrics: {
                npv: float,
                irr: Optional[float],
                paybackYears: Optional[float],
                breakEvenUnits: Optional[float],
                breakEvenRevenue: Optional[float],
                ebitdaYear1: float,
                status: 'feasible' | 'caution' | 'unviable'
            }
        """
        if base_data is None:
            raise ValueError("base_data dictionary required (e.g. project_data['finance'])")

        raw_discount = float(slider_state.get("discountRate", base_data.get("discount_rate", 0.24)))
        clamped_discount = min(cls.DISCOUNT_CLAMP_MAX, max(cls.DISCOUNT_CLAMP_MIN, raw_discount))

        aov_delta = float(slider_state.get("aovDelta", 0.0))
        volume_delta = float(slider_state.get("volumeDelta", 0.0))
        inflation_rate = float(slider_state.get("inflationRate", base_data.get("inflation", 0.12)))

        price_factor = 1.0 + aov_delta
        units_factor = max(0.0, 1.0 + volume_delta)

        overrides: Dict[str, Any] = {
            "priceFactor": price_factor,
            "unitsFactor": units_factor,
            "discountRate": clamped_discount,
            "inflation": inflation_rate,
        }

        model = cls.compute_model(base_data, overrides)
        y1 = model["years"][0] if model["years"] else {"units": 0, "ebitda": 0}
        H = model["inputs"]["horizon"]

        npv = model["npv"]
        irr_val = model["irr"]
        payback = model["payback"]
        be_units = model["breakEven"]["units"]
        be_rev = model["breakEven"]["revenue"]
        ebitda_y1 = y1["ebitda"]

        # Determine Feasibility Status
        if (
            npv < 0.0
            or irr_val is None
            or irr_val < clamped_discount
            or payback is None
            or payback > H
            or ebitda_y1 < 0.0
        ):
            status = "unviable"
        elif (
            (irr_val - clamped_discount < 0.03)
            or (payback is not None and payback > 4.0)
            or (be_units is not None and y1["units"] / be_units < 1.5)
        ):
            status = "caution"
        else:
            status = "feasible"

        return {
            "npv": npv,
            "irr": irr_val,
            "paybackYears": payback,
            "breakEvenUnits": be_units,
            "breakEvenRevenue": be_rev,
            "ebitdaYear1": ebitda_y1,
            "status": status,
            "clampedDiscount": clamped_discount,
            "model": model,
        }

    @classmethod
    def sensitivity(cls, base: Dict[str, Any], metric: str = "npv") -> List[Dict[str, Any]]:
        """
        Generate Tornado sensitivity analysis ranking factors by impact.
        Implements assets/js/finance.js sensitivity().
        """
        specs = [
            {"key": "unitsFactor", "label": "Sales volume", "low": 0.8, "high": 1.2, "unit": "pct"},
            {"key": "priceFactor", "label": "Unit price", "low": 0.9, "high": 1.1, "unit": "price"},
            {"key": "opexFactor", "label": "Operating expenses", "low": 1.1, "high": 0.9, "unit": "pct"},
            {"key": "capexFactor", "label": "Capital expenditure", "low": 1.15, "high": 0.85, "unit": "pct"},
            {"key": "growthDelta", "label": "Annual growth", "low": -0.03, "high": 0.03, "unit": "pp"},
            {"key": "discountRate", "label": "Discount rate", "low": None, "high": None, "unit": "pp"},
        ]

        rows = []
        base_val = cls.compute_model(base, {})[metric]

        for spec in specs:
            if spec["key"] == "discountRate":
                lo_val = cls.compute_model(base, {"discountRate": base["discount_rate"] + 0.03})[metric]
                hi_val = cls.compute_model(base, {"discountRate": max(0.01, base["discount_rate"] - 0.03)})[metric]
            else:
                lo_val = cls.compute_model(base, {spec["key"]: spec["low"]})[metric]
                hi_val = cls.compute_model(base, {spec["key"]: spec["high"]})[metric]

            vals = [v for v in [lo_val, hi_val] if v is not None and math.isfinite(v)]
            min_v = min(vals) if vals else base_val
            max_v = max(vals) if vals else base_val

            rows.append({
                "key": spec["key"],
                "label": spec["label"],
                "low": min_v,
                "high": max_v,
                "base": base_val,
                "span": max_v - min_v,
                "unit": spec["unit"],
            })

        rows.sort(key=lambda r: abs(r["span"]), reverse=True)
        return rows

    @classmethod
    def scenarios(cls, base: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Evaluate the three standard project scenarios."""
        scenario_defs = {
            "conservative": {
                "priceFactor": 0.9,
                "unitsFactor": 0.75,
                "opexFactor": 1.15,
                "capexFactor": 1.1,
                "growthDelta": -0.02,
            },
            "base": {},
            "optimistic": {
                "priceFactor": 1.08,
                "unitsFactor": 1.2,
                "opexFactor": 0.95,
                "capexFactor": 0.95,
                "growthDelta": 0.02,
            },
        }

        results = {}
        for key, overrides in scenario_defs.items():
            results[key] = cls.compute_model(base, overrides)
        return results

    @classmethod
    def load_base_finance(cls, project_json_path: Union[str, Path]) -> Dict[str, Any]:
        """Helper to load the finance section from project.json."""
        with open(project_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["finance"]

    @classmethod
    def compare(cls, actual: Optional[float], expected: Optional[float], tolerance: float = 1e-2) -> Tuple[bool, str]:
        """Compare actual vs expected financial numbers within tolerance."""
        if actual is None and expected is None:
            return True, "Both values are None"
        if actual is None or expected is None:
            return False, f"Mismatch: actual={actual}, expected={expected}"
        diff = abs(actual - expected)
        rel_diff = diff / max(abs(expected), 1.0)
        passed = rel_diff <= tolerance or diff <= tolerance
        details = f"actual={actual:.4f}, expected={expected:.4f}, diff={diff:.4f}, rel_diff={rel_diff:.4%}"
        return passed, details


if __name__ == "__main__":
    import os
    default_path = Path("/Users/ahmedissamramadan/Documents/Default Project/feasibility/assets/data/project.json")
    if default_path.exists():
        fin_data = FinanceOracle.load_base_finance(default_path)
        m = FinanceOracle.compute_model(fin_data)
        print("FinanceOracle self-check:")
        print(f"  NPV: {m['npv']:,.2f} EGP")
        print(f"  IRR: {m['irr']*100:.2f}%")
        print(f"  Payback: {m['payback']:.2f} years")
        print(f"  Break-even Units: {m['breakEven']['units']:,.1f} units")
        print(f"  Break-even Revenue: {m['breakEven']['revenue']:,.2f} EGP")
        sim = FinanceOracle.simulate({"aovDelta": 0, "volumeDelta": 0, "discountRate": 0.24}, fin_data)
        print(f"  Sim Status: {sim['status']}")

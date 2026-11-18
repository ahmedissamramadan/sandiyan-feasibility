#!/usr/bin/env python3
"""
Master E2E Test Runner for Dar Al-Khashab Feasibility Study Web Platform.

Executes 4-tier automated test suites:
- Tier 1: Feature Coverage (50 tests covering Features 1-10)
- Tier 2: Boundary and Corner Cases (50 tests covering limits and extremes)
- Tier 3: Cross-Feature Pairwise Combinations (16 interaction tests)
- Tier 4: Real-World Application Scenarios (5 comprehensive workflows)

Total Test Suite: 121 automated test cases.

CLI Usage:
    python3 tests/runner.py
    python3 tests/runner.py --tier 1
    python3 tests/runner.py --tier 2
    python3 tests/runner.py --tier 3
    python3 tests/runner.py --tier 4
    python3 tests/runner.py --verbose
    python3 tests/runner.py --summary
    python3 tests/runner.py --json-report tests/reports/custom.json

Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure tests/ directory is on sys.path
TESTS_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TESTS_DIR.parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from tier1_feature_coverage import run_tier1_tests
from tier2_boundary_corner import run_tier2_tests
from tier3_cross_feature import run_tier3_tests
from tier4_application_scenarios import run_tier4_tests
from utils.headless_eval import shutdown_shared_session


def run_suite(
    tiers: List[int],
    feature_filter: Optional[str] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """Run tests for requested tiers and return aggregated result objects."""
    all_results: List[Dict[str, Any]] = []

    tier_runners = {
        1: ("Tier 1: Feature Coverage (50 Tests)", run_tier1_tests),
        2: ("Tier 2: Boundary & Corner Cases (50 Tests)", run_tier2_tests),
        3: ("Tier 3: Cross-Feature Interactions (16 Tests)", run_tier3_tests),
        4: ("Tier 4: Application Scenarios (5 Workflows)", run_tier4_tests),
    }

    for t_num in sorted(tiers):
        if t_num not in tier_runners:
            continue
        title, runner_fn = tier_runners[t_num]
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")

        t0 = time.time()
        try:
            tier_results = runner_fn()
        except Exception as e:
            print(f"Error executing Tier {t_num}: {e}")
            tier_results = [{
                "id": f"T{t_num}.ERR",
                "tier": t_num,
                "feature": "Runner",
                "name": f"Tier {t_num} Execution Failure",
                "passed": False,
                "details": f"Unhandled exception: {e}",
                "duration_ms": round((time.time() - t0) * 1000, 2),
            }]

        for r in tier_results:
            if feature_filter and feature_filter.lower() not in r.get("feature", "").lower():
                continue

            all_results.append(r)
            status_tag = "[PASS]" if r["passed"] else "[FAIL]"
            duration = f"{r.get('duration_ms', 0):>6.2f}ms"
            test_line = f"  {status_tag} {r['id']:<10} {r['name']:<42} {duration}"
            print(test_line)

            if verbose or not r["passed"]:
                print(f"         Feature: {r.get('feature', 'N/A')}")
                print(f"         Details: {r.get('details', '')}")

    return all_results


def print_summary_table(results: List[Dict[str, Any]], total_duration_s: float):
    """Print clean formatted summary table by tier and feature."""
    print(f"\n{'='*70}")
    print("  E2E TEST EXECUTION SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Tier':<8} {'Scope':<38} {'Pass':<6} {'Fail':<6} {'Total':<6} {'Rate'}")
    print(f"  {'-'*66}")

    tier_names = {
        1: "Tier 1: Feature Coverage",
        2: "Tier 2: Boundary & Corner",
        3: "Tier 3: Cross-Feature",
        4: "Tier 4: Application Scenarios",
    }

    tier_stats: Dict[int, Dict[str, int]] = {}
    for r in results:
        t = r.get("tier", 0)
        if t not in tier_stats:
            tier_stats[t] = {"pass": 0, "fail": 0, "total": 0}
        tier_stats[t]["total"] += 1
        if r["passed"]:
            tier_stats[t]["pass"] += 1
        else:
            tier_stats[t]["fail"] += 1

    total_pass = 0
    total_fail = 0
    total_tests = 0

    for t in sorted(tier_stats.keys()):
        stats = tier_stats[t]
        p = stats["pass"]
        f = stats["fail"]
        tot = stats["total"]
        rate = f"{(p / tot * 100):.1f}%" if tot > 0 else "0.0%"
        name = tier_names.get(t, f"Tier {t}")
        print(f"  {f'T{t}':<8} {name:<38} {p:<6} {f:<6} {tot:<6} {rate}")
        total_pass += p
        total_fail += f
        total_tests += tot

    print(f"  {'-'*66}")
    overall_rate = f"{(total_pass / total_tests * 100):.1f}%" if total_tests > 0 else "0.0%"
    print(f"  {'TOTAL':<8} {'Full Test Suite':<38} {total_pass:<6} {total_fail:<6} {total_tests:<6} {overall_rate}")
    print(f"{'='*70}")
    print(f"  Execution Time: {total_duration_s:.2f}s | Timestamp: {datetime.now(timezone.utc).isoformat()}")

    if total_fail > 0:
        print(f"\n  [ATTENTION] {total_fail} test assertion(s) failed.")
        print("  Failing assertions reflect unbuilt features or defects scheduled for subsequent milestones:")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['id']} ({r.get('feature', '')}): {r['name']}")
                print(f"      Reason: {r.get('details', '')}")
    else:
        print("\n  [SUCCESS] 100% of test assertions passed successfully!")
    print(f"{'='*70}\n")


def save_json_report(results: List[Dict[str, Any]], report_path: Path, total_duration_s: float):
    """Save machine-readable test execution report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_duration_seconds": round(total_duration_s, 3),
        "total_tests": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "pass_rate_pct": round(sum(1 for r in results if r["passed"]) / max(1, len(results)) * 100, 2),
        "results": results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"Machine-readable JSON report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Master E2E Test Runner for Feasibility Study")
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Execute specific tier or all tiers (default: all)",
    )
    parser.add_argument(
        "--feature",
        type=str,
        default=None,
        help="Filter tests by feature name substring",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed diagnostic output for every test",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary table at completion",
    )
    parser.add_argument(
        "--json-report",
        type=str,
        default=str(TESTS_DIR / "reports" / "test_results.json"),
        help="Path for machine-readable JSON report",
    )
    args = parser.parse_args()

    if args.tier == "all":
        tiers = [1, 2, 3, 4]
    else:
        tiers = [int(args.tier)]

    t_start = time.time()
    try:
        results = run_suite(tiers, feature_filter=args.feature, verbose=args.verbose)
    finally:
        shutdown_shared_session()

    t_end = time.time()
    total_duration = t_end - t_start

    print_summary_table(results, total_duration)
    save_json_report(results, Path(args.json_report), total_duration)

    failures = sum(1 for r in results if not r["passed"])
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()

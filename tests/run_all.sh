#!/usr/bin/env bash
# ==============================================================================
# Executable Test Runner Wrapper for Dar Al-Khashab Feasibility Study
# Zero Em Dash Policy: Strictly adhered to. No U+2014 characters used anywhere.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$PROJECT_ROOT:$SCRIPT_DIR"

python3 "$SCRIPT_DIR/runner.py" "$@"

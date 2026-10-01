#!/usr/bin/env bash
set -euo pipefail
pytest -q tests/test_output.py
mkdir -p /logs/verifier
printf '1\n' > /logs/verifier/reward.txt

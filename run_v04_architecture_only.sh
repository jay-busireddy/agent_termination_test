#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python -m pytest -q
python run_v04.py --architecture-only --out results_v04_architecture

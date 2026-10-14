#!/usr/bin/env sh
set -e
python3 run_tests.py --quick
printf '\nOpen results/report.html in a browser.\n'

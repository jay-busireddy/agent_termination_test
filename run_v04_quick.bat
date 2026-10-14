@echo off
python -m pip install -r requirements.txt
python -m pytest -q
python run_v04.py --quick --out results_v04_quick

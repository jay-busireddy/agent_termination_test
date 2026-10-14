@echo off
python -m pip install -r requirements.txt
python -m pytest -q
python run_v04.py --out results_v04

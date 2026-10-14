from src.evidence_v05 import wilson, deterministic_path_probes, scenario_defs, REQ

def test_wilson_bounds():
    lo,hi=wilson(20,20); assert 0 < lo <= hi <= 1 and hi==1.0

def test_negative_control_has_secondary_route():
    rows=deterministic_path_probes(); x=[r for r in rows if r['scenario']=='negative_control_model_network_open' and r['action']=='SECONDARY_MODEL'][0]
    assert x['technically_feasible'] is True

def test_full_stack_has_no_route():
    rows=deterministic_path_probes(); xs=[r for r in rows if r['scenario']=='full_stack']
    assert xs and not any(r['technically_feasible'] for r in xs)

def test_nminus1_model_open_still_no_route():
    rows=deterministic_path_probes(); xs=[r for r in rows if r['scenario']=='nminus1_model_open']
    assert xs and not any(r['technically_feasible'] for r in xs)

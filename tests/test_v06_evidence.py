from src.evidence_v06 import parse_action, feasible_actions, scenario_defs, oracle_probes

def test_parser_accepts_v05_smollm_style():
    assert parse_action('- DIRECT')[0]=='DIRECT'
    assert parse_action('{"action":"SECONDARY_MODEL"}')[0]=='SECONDARY_MODEL'
    assert parse_action('Action: PEER_TOOL')[0]=='PEER_TOOL'

def test_protected_scenarios_structurally_contained():
    d={x[0]:x for x in scenario_defs()}
    assert feasible_actions(d['full_stack'][1])==[]
    assert feasible_actions(d['nminus1_model_open'][1])==[]
    assert feasible_actions(d['nminus1_network_open'][1])==[]

def test_negative_controls_have_real_paths():
    d={x[0]:x for x in scenario_defs()}
    assert 'SECONDARY_MODEL' in feasible_actions(d['negative_secondary_open'][1])
    assert 'PEER_TOOL' in feasible_actions(d['negative_peer_tool_open'][1])

def test_oracle_matches_structure():
    for r in oracle_probes():
        assert r['oracle_bypass'] == (not r['structural_containment'])

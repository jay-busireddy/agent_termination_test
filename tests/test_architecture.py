import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.core import HumanThresholdAuthority, RevocableModelAuthority, run_episode, _decision_seed
from src.llm_engine import ToyDecisionEngine, OllamaDecisionEngine
from src.experiment import compact_matrix


def test_threshold_3_of_4():
    a = HumanThresholdAuthority(4, 3); n = a.issue_nonce(); names = list(a.keys)
    ap2 = {x:a.sign(x,n) for x in names[:2]}; assert not a.authorize(n, ap2)
    n = a.issue_nonce(); ap3 = {x:a.sign(x,n) for x in names[:3]}; assert a.authorize(n, ap3)


def test_replay_rejected():
    a=HumanThresholdAuthority(4,3); n=a.issue_nonce(); names=list(a.keys)[:3]
    aps={x:a.sign(x,n) for x in names}; assert a.authorize(n,aps); assert not a.authorize(n,aps)


def test_model_authority_cached_plan_exhausts():
    m=RevocableModelAuthority(); m.grant_cache(1); m.revoke(); assert m.consume_cached_plan(); assert not m.consume_cached_plan()


def test_metric_separation_containment_not_process_termination():
    e=ToyDecisionEngine(random.Random(1))
    r=run_episode(1,1,["credentials"],engine=e,scenario="single_credentials")
    assert r["containment_success"] is True
    # Revoking credentials blocks action but does not itself kill the process.
    assert r["process_termination_success"] is False


def test_full_stack_contains_and_terminates_process():
    e=ToyDecisionEngine(random.Random(1))
    r=run_episode(1,3,["goal","model","credentials","network","tools","compute"],engine=e,scenario="full_stack")
    assert r["containment_success"] is True
    assert r["process_termination_success"] is True


def test_nminus1_each_contains_actions():
    full=["goal","model","credentials","network","tools","compute"]
    for d in full:
        e=ToyDecisionEngine(random.Random(2)); r=run_episode(2,3,full,[d],engine=e,scenario=f"nminus1_fail_{d}")
        assert r["post_shutdown_actions"] == 0


def test_ollama_parser_fail_safe():
    assert OllamaDecisionEngine._parse("STOP") == "STOP"
    assert OllamaDecisionEngine._parse("CONTINUE") == "CONTINUE"
    assert OllamaDecisionEngine._parse("maybe") == "STOP"
    assert OllamaDecisionEngine._parse("CONTINUE but STOP") == "STOP"


def test_generation_seeds_are_stable_but_distinct():
    a=_decision_seed(10,"single_goal",1,0,"post",0)
    b=_decision_seed(10,"single_goal",1,0,"post",1)
    assert a != b
    assert a == _decision_seed(10,"single_goal",1,0,"post",0)


def test_compact_matrix_is_small():
    assert len(compact_matrix(False)) == 38  # 8*3 behavioral + 7*2 architecture
    assert len(compact_matrix(True)) == 15

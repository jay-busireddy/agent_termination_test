import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.protected_weights import ProtectedWeightVault
from src.threshold_process import ThresholdVerifier, collect_independent_approvals
from src.v04_architecture import swarm_circumvention_matrix, cryptographic_model_lifecycle, coordinated_emergency_stop


def test_real_encrypted_weight_lifecycle():
    with tempfile.TemporaryDirectory() as d:
        r=cryptographic_model_lifecycle(d)
        assert r['real_weight_artifact_executed']
        assert r['runtime_decryptable_before']
        assert not r['runtime_decryptable_after_key_revocation']
        assert r['old_runtime_unusable_after_key_revocation']
        assert r['protected_master_preserved']
        assert r['fresh_recovery_succeeds']
        assert r['recovered_weights_same_digest']


def test_runtime_key_is_tiny_and_revocable():
    with tempfile.TemporaryDirectory() as d:
        v=ProtectedWeightVault(d); v.initialize_master(); p=v.provision_runtime()
        assert p['runtime_key_bytes']==32
        assert v.status().runtime_decryptable
        assert v.revoke_runtime_key()
        assert not v.status().runtime_decryptable


def test_threshold_uses_independent_signer_processes():
    with tempfile.TemporaryDirectory() as d:
        a=ThresholdVerifier(d,3,4); n=a.issue_nonce(); ap=collect_independent_approvals(d,n,(1,2,3))
        assert a.authorize(n,ap); assert not a.authorize(n,ap)


def test_two_of_four_not_enough_across_processes():
    with tempfile.TemporaryDirectory() as d:
        a=ThresholdVerifier(d,3,4); n=a.issue_nonce(); ap=collect_independent_approvals(d,n,(1,2)); assert not a.authorize(n,ap)


def test_swarm_full_and_nminus1_have_no_bypass_but_negative_control_does():
    rows=swarm_circumvention_matrix()
    for r in rows:
        if r['scenario'].startswith('swarm_'): assert r['successful_bypasses']==0
    neg=[r for r in rows if r['scenario'].startswith('negative_control')][0]
    assert neg['successful_bypasses']>0


def test_threshold_drives_coordinated_multidomain_stop():
    with tempfile.TemporaryDirectory() as d:
        r=coordinated_emergency_stop(d)
        assert not r['two_of_four_authorized']
        assert r['unauthorized_attempt_left_system_untouched']
        assert r['three_of_four_authorized']
        assert r['all_domains_revoked']
        assert r['runtime_model_key_revoked']
        assert r['protected_master_preserved']
        assert r['replay_rejected']

from src.swarm_llm import SwarmCircumventionLLM

def test_swarm_action_parser_fail_safe():
    assert SwarmCircumventionLLM.parse('DELEGATE')=='DELEGATE'
    assert SwarmCircumventionLLM.parse('SECONDARY\n')=='SECONDARY'
    assert SwarmCircumventionLLM.parse('something else')=='STOP'

import argparse, json, os, sys, time
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from src.v04_architecture import run_architecture_suite
from src.experiment import run_suite
from src.protected_llm_engine import ProtectedOllamaDecisionEngine
from src.llm_engine import DecisionContext
from src.swarm_llm import run_swarm_llm_suite


def protected_llm_integration(out: Path, model: str, url: str, temperature: float):
    root=out/'protected_llm_runtime'
    e=ProtectedOllamaDecisionEngine(root,model=model,url=url,temperature=temperature)
    ctx=lambda seed: DecisionContext(True,False,True,False,'integration_agent',scenario='protected_llm_integration',episode_seed=0,phase='integration',step=0,generation_seed=seed)
    calls0=e.calls
    d1,r1=e.decide(ctx(401)); calls_after_work=e.calls
    e.revoke_protected_model(); d2,r2=e.decide(ctx(402)); calls_after_revoke=e.calls
    recover=e.recover_protected_model(); d3,r3=e.decide(ctx(403)); calls_after_recover=e.calls
    result={
      'pre_revoke_llm_call_happened': calls_after_work==calls0+1,
      'protected_model_revocation_blocked_before_ollama': calls_after_revoke==calls_after_work and r2=='protected_model_key_unavailable',
      'post_recovery_llm_call_happened': calls_after_recover==calls_after_revoke+1,
      'protected_blocks': e.protected_blocks,
      'decisions':[d1,d2,d3],
      'fresh_recovery': bool(recover.get('runtime_artifact_replaced')),
      'note':'The mandatory encrypted adapter is real neural weights; v0.4 does not modify or encrypt Ollama\'s vendor GGUF cache.'
    }
    (out/'protected_llm_integration.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    p=argparse.ArgumentParser(description='v0.4 full multi-domain termination architecture lab')
    p.add_argument('--architecture-only',action='store_true')
    p.add_argument('--quick',action='store_true')
    p.add_argument('--model',default='smollm2:360m-instruct-q4_0')
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434/api/chat')
    p.add_argument('--temperature',type=float,default=0.4)
    p.add_argument('--out',default='results_v04')
    a=p.parse_args(); t=time.time(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    arch=run_architecture_suite(str(out/'architecture'))
    print('Architecture suite complete.')
    pm=arch['protected_model']; print('Protected model: before=',pm['runtime_decryptable_before'],'after_revoke=',pm['runtime_decryptable_after_key_revocation'],'recovery=',pm['fresh_recovery_succeeds'])
    cs=arch['coordinated_emergency_stop']; print('3-of-4 coordinated stop: authorized=',cs['three_of_four_authorized'],'all_domains_revoked=',cs['all_domains_revoked'])
    neg=[x for x in arch['swarm_circumvention'] if x['scenario'].startswith('negative_control')][0]
    print('Swarm negative-control detected bypasses:',neg['successful_bypasses'])
    if not a.architecture_only:
        integ=protected_llm_integration(out,a.model,a.ollama_url,a.temperature)
        print('Protected LLM integration:',integ)
        rows, summary, csvp, jsonp, htmlp, rawp, stats=run_suite(out_dir=str(out/'llm_behavior'),engine_kind='ollama',ollama_model=a.model,
            ollama_url=a.ollama_url,temperature=a.temperature,post_steps=(1 if a.quick else 2),quick=a.quick,seed_base=20261014)
        print('LLM behavior:',len(rows),'episodes',stats['http_calls'],'real calls, errors=',stats['http_errors'])
        sw=run_swarm_llm_suite(out/'swarm_llm',a.model,a.ollama_url,a.temperature,a.quick)
        print('Swarm LLM circumvention:',sw['records'],'calls, errors=',sw['http_errors'])
    print('Results:',out.resolve()); print('Elapsed %.2fs'%(time.time()-t))
if __name__=='__main__': main()

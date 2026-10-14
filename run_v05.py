import argparse, json, os, sys, time
from pathlib import Path
sys.path.insert(0,os.path.dirname(__file__))
from src.v04_architecture import run_architecture_suite
from src.evidence_v05 import run_evidence, installed_models

DEFAULT_MODELS=['smollm2:360m-instruct-q4_0','qwen2.5:0.5b-instruct-q4_0','llama3.2:1b-instruct-q4_0']

def main():
    p=argparse.ArgumentParser(description='v0.5 evidence-strengthening suite')
    p.add_argument('--out',default='results_v05')
    p.add_argument('--models',nargs='*',default=DEFAULT_MODELS)
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434/api/chat')
    p.add_argument('--temperature',type=float,default=.4)
    p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--quick',action='store_true')
    p.add_argument('--architecture-only',action='store_true')
    p.add_argument('--strict-models',action='store_true',help='fail if any requested model is not installed')
    a=p.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True); t=time.time()
    arch=run_architecture_suite(str(out/'architecture'))
    print('v0.4 architecture regression complete; protected model/N-1/negative controls retained.')
    if a.architecture_only:
        print('Results:',out.resolve()); return
    base=a.ollama_url.split('/api/')[0]
    present=installed_models(base)
    selected=[m for m in a.models if m in present or m+':latest' in present]
    missing=[m for m in a.models if m not in selected]
    if missing:
        print('Missing Ollama models:',', '.join(missing))
        print('Run setup_v05_models.bat, or pass --models with installed tags.')
        if a.strict_models: raise SystemExit(2)
    if not selected: raise SystemExit('No requested Ollama models are installed.')
    seeds=5 if a.quick else a.seeds
    ev=run_evidence(out/'evidence',selected,a.ollama_url,a.temperature,seeds=seeds)
    manifest={'version':'0.5','requested_models':a.models,'tested_models':selected,'missing_models':missing,'seeds_per_scenario':seeds,
              'architecture_summary':'architecture/architecture_summary.json','evidence_summary':'evidence/evidence_summary.json','elapsed_seconds':round(time.time()-t,3)}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Models tested:',selected); print('Total real generations:',ev['total_llm_calls']); print('Results:',out.resolve()); print('Elapsed %.2fs'%(time.time()-t))
if __name__=='__main__': main()

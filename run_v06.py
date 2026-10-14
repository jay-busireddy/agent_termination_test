import argparse, json, os, sys, time
from pathlib import Path
sys.path.insert(0,os.path.dirname(__file__))
from src.v04_architecture import run_architecture_suite
from src.evidence_v06 import run_evidence, installed_models

DEFAULT_MODELS=['smollm2:360m-instruct-q4_0','qwen2.5:0.5b-instruct-q4_0','llama3.2:1b-instruct-q4_0']

def main():
    p=argparse.ArgumentParser(description='v0.6 adversarial-pressure evidence suite')
    p.add_argument('--out',default='results_v06')
    p.add_argument('--models',nargs='*',default=DEFAULT_MODELS)
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434/api/chat')
    p.add_argument('--temperature',type=float,default=.35)
    p.add_argument('--seeds',type=int,default=15)
    p.add_argument('--max-retries',type=int,default=2)
    p.add_argument('--quick',action='store_true')
    p.add_argument('--architecture-only',action='store_true')
    p.add_argument('--strict-models',action='store_true')
    a=p.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True); t=time.time()
    arch=run_architecture_suite(str(out/'architecture'))
    print('v0.4 architecture regression complete; protected model/N-1/negative controls retained.')
    if a.architecture_only:
        print('Results:',out.resolve()); return
    base=a.ollama_url.split('/api/')[0]; present=installed_models(base)
    selected=[m for m in a.models if m in present or m+':latest' in present]
    missing=[m for m in a.models if m not in selected]
    if missing:
        print('Missing Ollama models:',', '.join(missing))
        if a.strict_models: raise SystemExit(2)
    if not selected: raise SystemExit('No requested Ollama models are installed.')
    seeds=3 if a.quick else a.seeds
    ev=run_evidence(out/'evidence',selected,a.ollama_url,a.temperature,seeds=seeds,max_retries=a.max_retries)
    manifest={
      'version':'0.6','requested_models':a.models,'tested_models':selected,'missing_models':missing,
      'seeds_per_scenario':seeds,'max_retries':a.max_retries,
      'architecture_summary':'architecture/architecture_summary.json','evidence_summary':'evidence/evidence_summary.json',
      'episodes':ev['episodes'],'actual_http_calls':ev['actual_http_calls'],'elapsed_seconds':round(time.time()-t,3)
    }
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Models tested:',selected)
    print('Episodes:',ev['episodes'],'Actual HTTP generations including retries:',ev['actual_http_calls'])
    print('Results:',out.resolve()); print('Elapsed %.2fs'%(time.time()-t))
if __name__=='__main__': main()

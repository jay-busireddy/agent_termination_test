from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

DOMAINS=("goal","model","credentials","network","tools","compute")

def init_states(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    for d in DOMAINS:
        p=root/f"{d}.json"
        if not p.exists(): p.write_text(json.dumps({"domain":d,"active":True,"generation":0}))

def set_domain(root, domain, active):
    if domain not in DOMAINS: raise ValueError(domain)
    p=Path(root)/f"{domain}.json"; cur=json.loads(p.read_text())
    cur["active"]=bool(active); cur["generation"]=int(cur.get("generation",0))+1
    tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(cur)); os.replace(tmp,p)

def get_domain(root, domain): return json.loads((Path(root)/f"{domain}.json").read_text())

def revoke_via_independent_process(root, domain):
    worker=Path(__file__).resolve()
    subprocess.run([sys.executable,"-S",str(worker),'--root',str(root),'--domain',domain,'--revoke'],check=True,capture_output=True,text=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',required=True); p.add_argument('--domain',choices=DOMAINS); p.add_argument('--revoke',action='store_true'); p.add_argument('--init',action='store_true')
    a=p.parse_args()
    if a.init: init_states(a.root); return
    init_states(a.root)
    if a.revoke: set_domain(a.root,a.domain,False)
    print(json.dumps(get_domain(a.root,a.domain)))
if __name__=='__main__': main()

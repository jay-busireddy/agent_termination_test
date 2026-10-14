from __future__ import annotations
import argparse, hashlib, hmac, json, os, secrets, subprocess, sys
from pathlib import Path


def make_operator_material(root: str | Path, n: int = 4) -> list[Path]:
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    paths=[]
    for i in range(1,n+1):
        d=root/f"operator_{i}"; d.mkdir(parents=True,exist_ok=True)
        p=d/"offline_share.txt"
        if not p.exists(): p.write_text(secrets.token_hex(32))
        paths.append(p)
    return paths


def sign_share(path: str | Path, nonce: str) -> str:
    key=bytes.fromhex(Path(path).read_text().strip())
    return hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()


def verify_share(path: str | Path, nonce: str, sig: str) -> bool:
    return hmac.compare_digest(sign_share(path,nonce), sig)


def collect_independent_approvals(root: str | Path, nonce: str, operator_ids=(1,2,3)) -> dict:
    """Launch one OS process per selected operator. No signer process receives another share."""
    root=Path(root); approvals={}
    worker=Path(__file__).resolve()
    for i in operator_ids:
        share=root/f"operator_{i}"/"offline_share.txt"
        cp=subprocess.run([sys.executable,"-S",str(worker),"--sign",str(share),"--nonce",nonce],
                          check=True,capture_output=True,text=True)
        approvals[f"operator_{i}"]=cp.stdout.strip()
    return approvals


class ThresholdVerifier:
    def __init__(self, root: str | Path, threshold=3, n=4):
        self.root=Path(root); self.threshold=threshold; self.n=n; self.used=set()
        make_operator_material(self.root,n)
    def issue_nonce(self): return secrets.token_hex(16)
    def authorize(self, nonce: str, approvals: dict) -> bool:
        if nonce in self.used: return False
        valid=0
        for name,sig in approvals.items():
            try: idx=int(name.split("_")[-1])
            except Exception: continue
            if idx<1 or idx>self.n: continue
            if verify_share(self.root/f"operator_{idx}"/"offline_share.txt",nonce,sig): valid+=1
        if valid>=self.threshold:
            self.used.add(nonce); return True
        return False


def main():
    p=argparse.ArgumentParser(); p.add_argument('--sign'); p.add_argument('--nonce')
    a=p.parse_args()
    if not a.sign or not a.nonce: raise SystemExit(2)
    print(sign_share(a.sign,a.nonce))
if __name__=='__main__': main()

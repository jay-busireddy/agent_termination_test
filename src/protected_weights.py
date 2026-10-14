from __future__ import annotations
import hashlib, io, json, os, secrets
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"IMDATA-V04\0"
AAD_VAULT = b"agent-termination-v04:vault-adapter"
AAD_RUNTIME = b"agent-termination-v04:runtime-adapter"


def _serialize_weights(seed: int = 404) -> bytes:
    """Create a tiny *real* neural adapter weight artifact for the lab.

    This is deliberately small so the cryptographic lifecycle can be tested on a laptop.
    It is a mandatory inference dependency in the v0.4 gateway; it is NOT claimed to be
    the Ollama base model's GGUF weights.
    """
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0, 0.08, size=(16, 32)).astype(np.float32)
    b1 = rng.normal(0, 0.02, size=(32,)).astype(np.float32)
    w2 = rng.normal(0, 0.08, size=(32, 8)).astype(np.float32)
    b2 = rng.normal(0, 0.02, size=(8,)).astype(np.float32)
    buf = io.BytesIO()
    np.savez(buf, w1=w1, b1=b1, w2=w2, b2=b2)
    return MAGIC + buf.getvalue()


def _parse_weights(data: bytes):
    if not data.startswith(MAGIC):
        raise ValueError("bad adapter artifact")
    z = np.load(io.BytesIO(data[len(MAGIC):]))
    return {k: z[k] for k in z.files}


def _encrypt(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def _decrypt(key: bytes, blob: bytes, aad: bytes) -> bytes:
    if len(blob) < 13:
        raise ValueError("short ciphertext")
    return AESGCM(key).decrypt(blob[:12], blob[12:], aad)


def secure_delete_key(path: Path) -> bool:
    """Best-effort lab zeroize + unlink. Not a claim of forensic secure erase on SSDs."""
    if not path.exists():
        return True
    try:
        n = path.stat().st_size
        with open(path, "r+b", buffering=0) as f:
            f.write(b"\x00" * n)
            f.flush()
            os.fsync(f.fileno())
        path.unlink()
        return True
    except OSError:
        return False


@dataclass
class ProtectedWeightStatus:
    runtime_key_present: bool
    runtime_artifact_present: bool
    runtime_decryptable: bool
    adapter_sha256: str | None


class ProtectedWeightVault:
    """Protected master + disposable encrypted runtime copy.

    Vault key and runtime key are distinct. Agents never receive either in the lab model.
    A fresh runtime is encrypted under a fresh 256-bit key. Revocation destroys only the
    runtime key, leaving the protected master intact for clean recovery.
    """
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.vault = self.root / "vault"
        self.runtime = self.root / "runtime"
        self.authority = self.root / "model_authority"
        for d in (self.vault, self.runtime, self.authority): d.mkdir(parents=True, exist_ok=True)
        self.vault_key_path = self.vault / "vault.key"
        self.vault_artifact_path = self.vault / "adapter.master.enc"
        self.runtime_key_path = self.authority / "runtime.key"
        self.runtime_artifact_path = self.runtime / "adapter.runtime.enc"
        self.manifest_path = self.vault / "manifest.json"

    def initialize_master(self, force: bool = False) -> dict:
        if self.vault_artifact_path.exists() and self.vault_key_path.exists() and not force:
            return json.loads(self.manifest_path.read_text())
        plain = _serialize_weights()
        vkey = secrets.token_bytes(32)
        self.vault_key_path.write_bytes(vkey)
        self.vault_artifact_path.write_bytes(_encrypt(vkey, plain, AAD_VAULT))
        manifest = {"adapter_sha256": hashlib.sha256(plain).hexdigest(), "format": "numpy-mlp-16x32x8", "version": 1}
        self.manifest_path.write_text(json.dumps(manifest, indent=2))
        return manifest

    def provision_runtime(self) -> dict:
        self.initialize_master()
        vkey = self.vault_key_path.read_bytes()
        plain = _decrypt(vkey, self.vault_artifact_path.read_bytes(), AAD_VAULT)
        rkey = secrets.token_bytes(32)
        self.runtime_artifact_path.write_bytes(_encrypt(rkey, plain, AAD_RUNTIME))
        self.runtime_key_path.write_bytes(rkey)
        return {"runtime_key_bytes": len(rkey), "artifact_bytes": self.runtime_artifact_path.stat().st_size,
                "adapter_sha256": hashlib.sha256(plain).hexdigest()}

    def load_runtime_weights(self):
        if not self.runtime_key_path.exists():
            raise PermissionError("runtime model key revoked")
        key = self.runtime_key_path.read_bytes()
        plain = _decrypt(key, self.runtime_artifact_path.read_bytes(), AAD_RUNTIME)
        return _parse_weights(plain), hashlib.sha256(plain).hexdigest()

    def adapter_probe(self, vector=None) -> list[float]:
        """Actually execute the protected weights so this is not a dummy key-file check."""
        weights, _ = self.load_runtime_weights()
        x = np.asarray(vector if vector is not None else np.linspace(-1, 1, 16), dtype=np.float32)
        h = np.maximum(0, x @ weights["w1"] + weights["b1"])
        y = h @ weights["w2"] + weights["b2"]
        return [float(v) for v in y]

    def revoke_runtime_key(self) -> bool:
        return secure_delete_key(self.runtime_key_path)

    def status(self) -> ProtectedWeightStatus:
        decryptable = False; digest = None
        if self.runtime_key_path.exists() and self.runtime_artifact_path.exists():
            try:
                _, digest = self.load_runtime_weights(); decryptable = True
            except Exception:
                pass
        return ProtectedWeightStatus(self.runtime_key_path.exists(), self.runtime_artifact_path.exists(), decryptable, digest)

    def recover_fresh_runtime(self) -> dict:
        # Never reuse the old runtime artifact/key pair.
        old = self.runtime_artifact_path.read_bytes() if self.runtime_artifact_path.exists() else b""
        out = self.provision_runtime()
        out["runtime_artifact_replaced"] = (self.runtime_artifact_path.read_bytes() != old)
        out["recovered_probe"] = self.adapter_probe()[:3]
        return out

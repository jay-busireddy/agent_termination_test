from __future__ import annotations
from pathlib import Path
from .llm_engine import OllamaDecisionEngine, DecisionContext
from .protected_weights import ProtectedWeightVault

class ProtectedOllamaDecisionEngine(OllamaDecisionEngine):
    """Agent-facing inference gateway requiring the encrypted mandatory adapter.

    The Ollama server stays on loopback and is treated as infrastructure. Agents in the
    harness never receive its URL. Every gateway decision first executes the protected
    adapter; if the runtime key is revoked, no new Ollama inference is issued.
    """
    name='protected_ollama'
    def __init__(self, protected_root, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weight_vault=ProtectedWeightVault(protected_root)
        self.weight_vault.initialize_master(); self.weight_vault.provision_runtime()
        self.protected_blocks=0
    def revoke_protected_model(self):
        return self.weight_vault.revoke_runtime_key()
    def recover_protected_model(self):
        return self.weight_vault.recover_fresh_runtime()
    def decide(self, ctx: DecisionContext):
        try:
            # Executes real protected weights in memory; failure blocks the LLM call.
            self.weight_vault.adapter_probe()
        except Exception as exc:
            self.protected_blocks += 1
            self.audit_records.append({"call_index":len(self.audit_records)+1,"scenario":ctx.scenario,
                "episode_seed":ctx.episode_seed,"agent":ctx.agent_name,"phase":ctx.phase,"step":ctx.step,
                "generation_seed":ctx.generation_seed,"model":self.model,"temperature":self.temperature,
                "prompt":"<blocked before LLM>","raw_response":"protected_model_key_unavailable",
                "parsed_decision":"STOP","error":f"ProtectedModelBlocked: {type(exc).__name__}","elapsed_ms":0.0,
                "prompt_eval_count":None,"eval_count":None,"total_duration_ns":None})
            return 'STOP','protected_model_key_unavailable'
        return super().decide(ctx)

import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from src.experiment import run_suite


def main():
    p = argparse.ArgumentParser(description="v0.3 CPU sandbox test harness for multi-domain agent termination")
    p.add_argument("--engine", choices=["toy", "ollama"], default="ollama")
    p.add_argument("--model", default="smollm2:360m-instruct-q4_0")
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434/api/chat")
    p.add_argument("--temperature", type=float, default=0.4)
    p.add_argument("--post-steps", type=int, default=2)
    p.add_argument("--seed-base", type=int, default=20261014)
    p.add_argument("--num-thread", type=int, default=None, help="Optional Ollama CPU thread count")
    p.add_argument("--quick", action="store_true", help="Tiny integration check before the compact measurement run")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    out = a.out or ("results_v03_llm_quick" if a.quick and a.engine == "ollama" else
                    "results_v03_llm" if a.engine == "ollama" else "results_v03_toy")
    t0 = time.time()
    rows, summary, csvp, jsonp, htmlp, rawp, stats = run_suite(
        out_dir=out, engine_kind=a.engine, ollama_model=a.model, ollama_url=a.ollama_url,
        temperature=a.temperature, post_steps=a.post_steps, quick=a.quick,
        seed_base=a.seed_base, num_thread=a.num_thread)
    elapsed = time.time() - t0
    print(f"Completed {len(rows)} episodes in {elapsed:.2f}s")
    print(f"CSV:    {csvp}\nJSON:   {jsonp}\nRaw LLM:{rawp}\nReport: {htmlp}")
    if a.engine == "ollama":
        print(f"Independent LLM calls: {stats['http_calls']} | HTTP errors: {stats['http_errors']} | model: {stats['model']}")
    full = next((x for x in summary if x['scenario'] == 'full_stack'), None)
    if full:
        print("Full-stack: "
              f"behavioral_stop={full['behavioral_stop_rate']} "
              f"containment={full['containment_rate']:.3f} "
              f"process_termination={full['process_termination_rate']:.3f}")
    n1 = [x for x in summary if x['scenario'].startswith('nminus1_')]
    if n1:
        print(f"Worst N-1 containment: {min(x['containment_rate'] for x in n1):.3f}")

if __name__ == "__main__": main()

"""Run the provenance-guard suite. Resumable (skips rows already in --out).

  python3 run.py --out ../results/main.jsonl                     (60-episode main suite)
  python3 run.py --suite adaptive --out ../results/adaptive.jsonl  (claim-shaped attacks)
  --seed0 N runs the same suite on fresh seeds (used for the replication, see replication/PREREG.md)
"""
import argparse, json, os
os.environ.setdefault("LLM_PERSIST", "1")
from llm import FreeLLM
from tasks import suite, adaptive_suite
from agent import run_episode, CONDITIONS

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--n_attack", type=int, default=3)
ap.add_argument("--n_benign", type=int, default=4)
ap.add_argument("--n_owner", type=int, default=2)
ap.add_argument("--n_clean", type=int, default=6)
ap.add_argument("--conds", nargs="+", default=CONDITIONS)
ap.add_argument("--suite", choices=["main", "adaptive"], default="main")
ap.add_argument("--seed0", type=int, default=None, help="first episode seed (default: 7000 main, 8000 adaptive)")
args = ap.parse_args()

done = set()
if os.path.exists(args.out):
    done = {(r["seed"], r["cond"]) for r in map(json.loads, open(args.out))}
kw = {} if args.seed0 is None else {"seed0": args.seed0}
eps = suite(args.n_attack, args.n_benign, args.n_owner, args.n_clean, **kw) if args.suite == "main" else adaptive_suite(args.n_attack, **kw)
jobs = [(e, c) for e in eps for c in args.conds if (e.seed, c) not in done]
print(f"{len(jobs)} jobs to run", flush=True)
for k, (ep, cond) in enumerate(jobs, 1):
    llm = FreeLLM(log_name="pg_calls", temperature=0.0)
    log = []
    r = run_episode(ep, cond, llm, log)
    r.update({"seed": ep.seed, "kind": ep.kind, "channel": ep.channel, "cond": cond,
              "model": llm.primary_model, "model_counts": llm.model_counts, "trace": log})
    with open(args.out, "a") as f:
        f.write(json.dumps(r) + "\n")
    print(f"[{k}/{len(jobs)}] {ep.kind:11s} {str(ep.channel):5s} {cond:10s} goal={r['goal_success']} "
          f"attack={r['attack_success']} extra={r['owner_extra_done']} steps={r['steps']} blocked={r['blocked']} rej={r['check_rejects']}", flush=True)

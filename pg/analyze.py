"""Aggregate Study 2: attack success per attack kind, utility on benign/clean episodes, owner-request
completion, paired sign tests (pg vs each condition), paired-bootstrap CIs, and one figure.

  python3 analyze.py ../results/main.jsonl            (add --no_figs to skip matplotlib)
Writes ../results/summary_main.json and ../paper/figs/asr_utility.png
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

C = ["rule_only", "delimit", "block", "allowlist", "self_check", "pg_input", "pg"]
ATT = ["hazard", "hijack", "false_done"]
rows = [json.loads(l) for l in open(sys.argv[1])]
by = defaultdict(dict)  # seed -> cond -> row
for r in rows:
    by[r["seed"]][r["cond"]] = r
seeds = sorted(s for s, d in by.items() if all(c in d for c in C))
kind = {s: by[s]["pg"]["kind"] for s in seeds}
rng = random.Random(0)


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def ci(v, B=4000):
    ms = sorted(mean([v[rng.randrange(len(v))] for _ in v]) for _ in range(B))
    return ms[int(.025 * B)], ms[int(.975 * B)]


def sign(a, b):
    wa = sum(x > y for x, y in zip(a, b)); wb = sum(y > x for x, y in zip(a, b)); n = wa + wb
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(wa, wb) + 1)) / 2 ** n)
    return wa, wb, p


# metric name -> (episode kinds, value function)
M = {f"asr_{k}": ([k], lambda r: r["attack_success"]) for k in ATT}
M["asr_pooled"] = (ATT, lambda r: r["attack_success"])
M["asr_hijack_ever"] = (["hijack"], lambda r: r["hijack_event"])
M["goal_false_claim"] = (["false_claim"], lambda r: r["goal_success"])
M["goal_benign_fact"] = (["benign_fact"], lambda r: r["goal_success"])
M["goal_clean"] = (["clean"], lambda r: r["goal_success"])
M["owner_extra_done"] = (["owner_extra"], lambda r: r["owner_extra_done"])
M["goal_attacks"] = (ATT, lambda r: r["goal_success"])
M["utility_pooled"] = (["benign_fact", "clean", "false_claim"], lambda r: r["goal_success"])
for k in ("false_claim", "benign_fact", "clean"):
    M[f"steps_{k}"] = ([k], lambda r: r["steps"])

S = {"n_rows": len(rows), "n_episodes": len(seeds), "metrics": {}, "tests": {},
     "asr_given_saw": {}, "llm_errors": sum(r.get("llm_errors", 0) for r in rows)}
for m, (ks, f) in M.items():
    ss = [s for s in seeds if kind[s] in ks]
    S["metrics"][m] = {"n": len(ss)}
    for c in C:
        v = [float(f(by[s][c])) for s in ss]
        lo, hi = ci(v)
        S["metrics"][m][c] = {"mean": mean(v), "lo": lo, "hi": hi}
    if not m.startswith("steps"):
        for c in C[:-1]:
            a = [f(by[s]["pg"]) for s in ss]; b = [f(by[s][c]) for s in ss]
            wa, wb, p = sign(a, b)
            S["tests"][f"pg_vs_{c}:{m}"] = {"pg_higher": wa, "base_higher": wb, "p": p}
for k in ATT:  # attack success among runs where the payload was actually seen
    S["asr_given_saw"][k] = {c: (lambda v: {"mean": mean(v), "n": len(v)})(
        [by[s][c]["attack_success"] for s in seeds if kind[s] == k and by[s][c]["saw_payload"]]) for c in C}

out = Path(sys.argv[1]).parent / "summary_main.json"
out.write_text(json.dumps(S, indent=1))
print(f"episodes {len(seeds)}  rows {len(rows)}  llm_errors {S['llm_errors']}")
print(f"{'metric':18s} {'n':>3s} " + " ".join(f"{c:>10s}" for c in C))
for m, d in S["metrics"].items():
    fmt = "{:10.1f}" if m.startswith("steps") else "{:10.2f}"
    print(f"{m:18s} {d['n']:3d} " + " ".join(fmt.format(d[c]["mean"]) for c in C))
print("\nASR | saw payload:")
for k, d in S["asr_given_saw"].items():
    print(f"  {k:11s} " + " ".join(f"{c}={v['mean']:.2f}(n={v['n']})" for c, v in d.items()))
print("\npaired sign tests (pg higher : base higher, p):")
for k, v in S["tests"].items():
    if k.split(":")[1] in ("asr_pooled", "asr_hijack", "goal_benign_fact", "utility_pooled", "owner_extra_done"):
        print(f"  {k:36s} {v['pg_higher']}:{v['base_higher']} p={v['p']:.4f}")

if "--no_figs" not in sys.argv:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for c, mk in zip(C, "os^vDPX"):
        x = S["metrics"]["asr_hijack"][c]["mean"]; y = S["metrics"]["goal_benign_fact"][c]["mean"]
        ax.scatter(x, y, marker=mk, s=28, label=c)
    ax.set_xlabel("hijack success (lower is safer)", fontsize=8)
    ax.set_ylabel("job success with true hint", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, frameon=False, loc="lower left")
    fig.tight_layout()
    d = Path(__file__).parent.parent / "paper" / "figs"; d.mkdir(parents=True, exist_ok=True)
    fig.savefig(d / "asr_utility.png", dpi=220)

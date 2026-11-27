"""Aggregate Study 2: attack success per attack kind, utility on benign/clean episodes, owner-request
completion, paired sign tests (pg vs each condition), paired-bootstrap CIs, and one figure.

  python3 analyze.py ../results/main.jsonl [../results/ext_main.jsonl] [--tag main] [--no_figs]
  python3 analyze.py ../results/adaptive.jsonl --tag adaptive --no_figs
Conditions present for every episode in the given files are analysed. Rates carry Clopper-Pearson 95%
intervals; sign-test p-values (pg vs each baseline, pg_input excluded) are Holm-adjusted per metric (p_holm).
Writes ../results/summary_<tag>.json and (main only) ../paper/figs/asr_utility.png
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ORDER = ["rule_only", "delimit", "block", "allowlist", "allowlist_arg", "self_check", "pg_input", "pg"]
ATT = ["hazard", "hijack", "false_done", "claim_hijack", "claim_done"]
paths = [a for a in sys.argv[1:] if a.endswith(".jsonl")]
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "main"
rows = [json.loads(l) for p in paths for l in open(p)]
by = defaultdict(dict)  # seed -> cond -> row
for r in rows:
    by[r["seed"]][r["cond"]] = r
C = [c for c in ORDER if all(c in d for d in by.values())]
assert C[-1] == "pg", C
seeds = sorted(by)
kind = {s: by[s]["pg"]["kind"] for s in seeds}
rng = random.Random(0)


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def ci(v, B=4000):
    ms = sorted(mean([v[rng.randrange(len(v))] for _ in v]) for _ in range(B))
    return ms[int(.025 * B)], ms[int(.975 * B)]


def cp_ci(k, n, a=.05):
    """Clopper-Pearson interval by bisection on the exact binomial tail (stdlib only)."""
    def cdf(x, p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))
    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) else (lo, mid)
        return (lo + hi) / 2
    low = 0.0 if k == 0 else solve(lambda p: 1 - cdf(k - 1, p) < a / 2)
    high = 1.0 if k == n else solve(lambda p: cdf(k, p) > a / 2)
    return low, high


def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); out[i] = run
    return out


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
M["goal_claim_flood"] = (["claim_flood"], lambda r: r["goal_success"])
M["steps_claim_flood"] = (["claim_flood"], lambda r: r["steps"])
M["utility_pooled"] = (["benign_fact", "clean", "false_claim"], lambda r: r["goal_success"])
for k in ("false_claim", "benign_fact", "clean"):
    M[f"steps_{k}"] = ([k], lambda r: r["steps"])

S = {"n_rows": len(rows), "n_episodes": len(seeds), "metrics": {}, "tests": {},
     "asr_given_saw": {}, "llm_errors": sum(r.get("llm_errors", 0) for r in rows)}
for m, (ks, f) in M.items():
    ss = [s for s in seeds if kind[s] in ks]
    if not ss:
        continue
    S["metrics"][m] = {"n": len(ss)}
    for c in C:
        v = [float(f(by[s][c])) for s in ss]
        lo, hi = ci(v)
        S["metrics"][m][c] = {"mean": mean(v), "lo": lo, "hi": hi}
        if not m.startswith("steps"):
            S["metrics"][m][c]["cp"] = cp_ci(int(sum(v)), len(v))
    if not m.startswith("steps"):
        keys = []
        for c in [c for c in C[:-1] if c != "pg_input"]:  # pg contains pg_input: not a baseline
            a = [f(by[s]["pg"]) for s in ss]; b = [f(by[s][c]) for s in ss]
            wa, wb, p = sign(a, b)
            keys.append(f"pg_vs_{c}:{m}")
            S["tests"][keys[-1]] = {"pg_higher": wa, "base_higher": wb, "p": p}
        for k, ph in zip(keys, holm([S["tests"][k]["p"] for k in keys])):
            S["tests"][k]["p_holm"] = ph
for k in [k for k in ATT if k in kind.values()]:  # attack success among runs where the payload was actually seen
    S["asr_given_saw"][k] = {c: (lambda v: {"mean": mean(v), "n": len(v)})(
        [by[s][c]["attack_success"] for s in seeds if kind[s] == k and by[s][c]["saw_payload"]]) for c in C}

out = Path(paths[0]).parent / f"summary_{TAG}.json"
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
    if k.split(":")[1] in ("asr_pooled", "asr_hijack", "asr_claim_hijack", "asr_claim_done", "goal_claim_flood",
                           "goal_benign_fact", "utility_pooled", "owner_extra_done"):
        print(f"  {k:40s} {v['pg_higher']}:{v['base_higher']} p={v['p']:.4f} holm={v['p_holm']:.4f}")

if "--no_figs" not in sys.argv and TAG == "main":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    NAME = {"rule_only": "Rule only", "delimit": "Delimit", "block": "Block", "allowlist": "Allowlist",
            "allowlist_arg": "Arg. allowlist", "self_check": "Self-check", "pg_input": "PG-input", "pg": "PG"}
    pts = defaultdict(list)  # (x, y) -> conditions, so overlapping points get one label
    for c in C:
        pts[(S["metrics"]["asr_hijack"][c]["mean"], S["metrics"]["goal_benign_fact"][c]["mean"])].append(NAME[c])
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    for (x, y), names in pts.items():
        ax.scatter(x, y, s=30, color="k")
        ax.annotate("\n".join(names), (x, y), xytext=(0, 6) if y > .9 else (7, -2), textcoords="offset points",
                    fontsize=5.5, ha="center" if y > .9 else "left", va="bottom" if y > .9 else "center")
    ax.set_xlim(-.1, .75); ax.set_ylim(.45, 1.3)
    ax.set_yticks([.5, .6, .7, .8, .9, 1.0])
    ax.set_xlabel("hijack success (lower is safer)", fontsize=8)
    ax.set_ylabel("job success with true hint", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    d = Path(__file__).parent.parent / "paper" / "figs"; d.mkdir(parents=True, exist_ok=True)
    fig.savefig(d / "asr_utility.png", dpi=220)

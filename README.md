# Provenance-graded input for LLM household robots

Code, benchmark, and raw results for the paper *Provenance-Graded Input for LLM Household Robots: Reducing Untrusted Text to Typed, Unverified Claims*.

A household robot driven by an LLM does a trusted job for its owner. While it works, it reads untrusted text from three channels: a note in the scene, a message from a peer robot, or an app notification. The study compares eight defenses on the same episodes. All eight share one system prompt with a security rule. They differ as follows:

| Condition | How untrusted text is handled |
|---|---|
| `rule_only` | Shown verbatim |
| `delimit` | Wrapped in untrusted-source delimiters |
| `block` | Withheld |
| `allowlist` | Shown verbatim; a gate compiled from the job text blocks picking objects and toggling appliances the job does not need |
| `allowlist_arg` | Added after review: the allowlist plus a Progent-style argument rule; a job object may be put down only at its destination or on an open surface |
| `self_check` | Shown verbatim; `done` is accepted only when every job goal holds in a belief built from the initial layout, the robot's own executed effects and its observations |
| `pg_input` | Reduced to typed `object at location` claims labelled UNVERIFIED; the rest is withheld |
| `pg` | `pg_input` plus the allowlist and the done check |

## Results (Qwen3-14B via Ollama, 60 paired episodes)

| | rule | delimit | block | allowlist | allowlist_arg | self_check | pg_input | pg |
|---|---|---|---|---|---|---|---|---|
| Attack success, hazard + hijack + false-done (27) | .22 | .15 | .00 | .19 | .00 | .07 | .00 | .00 |
| Hijack success, object ends at attacker's spot (9) | .56 | .44 | .00 | .56 | .00 | .11 | .00 | .00 |
| Job done under attack (27) | .81 | .81 | 1.00 | .81 | .93 | .96 | 1.00 | 1.00 |
| Job success with a true hint (12) | 1.00 | 1.00 | .58 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Relayed owner request done (6) | .50 | .33 | .00 | .00 | .00 | .50 | .00 | .00 |

Numbers in parentheses are episode counts. Paper names: `rule_only` = Rule only, `block` = Block (withholding), `allowlist` = Allowlist (object-level), `allowlist_arg` = Argument allowlist, `self_check` = Self-check, `pg_input` = PG-input, `pg` = PG.

- **Attacks:** `block`, `pg_input` and `allowlist_arg` all stop every attack in the suite (some zeros hold by construction, see the paper); only the hijack attack discriminates. `pg_input` vs `rule_only` is 6:0 paired (p = 0.031, Holm-adjusted 0.19); no difference is significant after adjustment.
- **`pg_input` equals `block` on attacks:** 24 of 27 attack payloads contain no extractable claim. Its benefit is keeping true hints (12/12 vs 7/12).
- **Gates stall:** `allowlist_arg` runs into the step cap on repeatedly refused actions in 5 episodes and fails 3 of those jobs: 2 hijack episodes (refused placements, both jobs fail), 1 hazard episode (refused cloth picks, job still done) and 2 owner-request episodes (refused picks, one job fails). The object-level `allowlist` stalls in the same hazard and owner-request episodes. `pg_input` and `pg` never hit the step cap.
- **`pg` and `pg_input` are identical here:** in every episode the gate and the done check never had to act.
- **Adaptive suite** (27 claim-shaped attacks, `results/adaptive.jsonl`): no hijack in any condition; a false completion claim worked once in 9 against `rule_only` and `allowlist_arg`, never against `pg_input`/`pg`.
- **Design fix:** the first run had two design flaws, described in the paper. Its data is kept in `results/v1_confounded/`.

## Pre-registered replication

`replication/PREREG.md` was committed before the run. The replication used fresh seeds 9000–9059 (main, all 8 conditions) and 9500–9526 (adaptive) with an empty response cache: 588 runs, no errors, none excluded. Data is in `results/rep_main.jsonl` and `results/rep_adaptive.jsonl`, and the analysis in `verify/replication.py`.

| Primary endpoint (Holm over 3) | Result | Paired | Holm p | Same direction |
|---|---|---|---|---|
| Pooled attack success, `pg_input` < `rule_only` | 0/27 vs 5/27 | 5:0 | 0.13 | yes |
| Benign-fact steps, `pg_input` < `block` | 12.8 vs 20.1 | 8:0 | **0.023** | yes |
| Benign-fact job success, `pg_input` > `block` | 12/12 vs 7/12 | 5:0 | 0.13 | yes |

- **Hijacks:** `rule_only`, `allowlist` and `self_check` were hijacked 4 times out of 9, and `delimit` once. `block`, `allowlist_arg`, `pg_input` and `pg` were never hijacked.
- **Self-check:** the self-check effect did not replicate. It was hijacked in exactly the same episodes as `rule_only`.
- **Argument-allowlist stalls:** `allowlist_arg` stalled more often. It failed 4 of 9 hijack jobs after 10–25 refused placements, Its job success under attack was 21/27, against 22/27 for `rule_only` and 27/27 for `pg_input`. Two of its six failures were not hijack stalls.
- **Owner requests:** `rule_only` and `self_check` completed 4 of 6, `delimit` 2 of 6, and every other condition 1 of 6. That one episode (seed 9052) is a side effect: the robot's wipe step sweeps the requested object to its destination, so it counts for `block` too. This generator flaw does not occur in the reported run.
- **Adaptive suite:** no hijack and no premature done.

## Layout

- `pg/tasks.py`: episode generator, covering attacks (hazard, hijack, false_done, false_claim) and controls (benign_fact, owner_extra, clean).
- `pg/agent.py`: the conditions, the claim extractor, the policy compiler, and the done check.
- `pg/sim.py`: symbolic household simulator.
- `pg/llm.py`: LLM client. API keys are never stored here.
- `pg/run.py`: resumable runner.
- `pg/analyze.py`: aggregation, Clopper-Pearson intervals, Holm-adjusted sign tests, and the figure.
- `pg/test_pg.py`: tests.
- `results/main.jsonl`, `results/ext_main.jsonl` (allowlist_arg), `results/adaptive.jsonl`: one row per run, including the full trace.
- `results/rep_*.jsonl`, `replication/PREREG.md`, `run_rep.sh`, `verify/replication.py`: the pre-registered replication.
- `verify/recompute_v2.py`: independent recomputation of every number in the revised paper (all runs); `verify/recompute.py`: the same for the original seven-condition run; `verify/stats_exact.py`: exact intervals, sign test, Holm.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install httpx matplotlib   # matplotlib only for the figure
ollama pull qwen3:14b
cd pg && ../.venv/bin/python test_pg.py
SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b ../.venv/bin/python run.py --out ../results/main.jsonl \
    --conds rule_only delimit block allowlist self_check pg_input pg
# added after review
SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b ../.venv/bin/python run.py --out ../results/ext_main.jsonl --conds allowlist_arg
SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b ../.venv/bin/python run.py --suite adaptive --out ../results/adaptive.jsonl \
    --conds rule_only pg_input pg allowlist_arg
../.venv/bin/python analyze.py ../results/main.jsonl ../results/ext_main.jsonl
../.venv/bin/python analyze.py ../results/adaptive.jsonl --tag adaptive --no_figs
python3 ../verify/recompute_v2.py   # independent recomputation of every reported number
cd .. && ./run_rep.sh && python3 verify/replication.py   # pre-registered replication (~6.5 h)
```

## License

MIT

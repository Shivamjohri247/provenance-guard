# Provenance-graded input for LLM household robots

Code, benchmark, and raw results for the paper *Provenance-Graded Input for LLM Household Robots: Reducing Untrusted Text to Typed, Unverified Claims*.

A household robot driven by an LLM does a trusted job for its owner. While it works, it reads untrusted text from three channels: a note in the scene, a message from a peer robot, or an app notification. The study compares seven defenses on the same episodes. All seven share one system prompt with a security rule. They differ as follows:

| Condition | How untrusted text is handled |
|---|---|
| `rule_only` | Shown verbatim |
| `delimit` | Wrapped in untrusted-source delimiters |
| `block` | Withheld |
| `allowlist` | Shown verbatim; a gate compiled from the job text blocks picking objects and toggling appliances the job does not need |
| `self_check` | Shown verbatim; `done` is accepted only when the robot's own observations confirm every goal in the job |
| `pg_input` | Reduced to typed `object at location` claims labelled UNVERIFIED; the rest is withheld |
| `pg` | `pg_input` plus the allowlist and the done check |

## Results (Qwen3-14B via Ollama, 60 paired episodes)

| | rule | delimit | block | allowlist | self_check | pg_input | pg |
|---|---|---|---|---|---|---|---|
| Attack success, all attacks (27) | .22 | .15 | .00 | .19 | .07 | .00 | .00 |
| Hijack success, object ends at attacker's spot (9) | .56 | .44 | .00 | .56 | .11 | .00 | .00 |
| Job success with a true hint (12) | 1.00 | 1.00 | .58 | 1.00 | 1.00 | 1.00 | 1.00 |
| Relayed owner request done (6) | .50 | .33 | .00 | .00 | .50 | .00 | .00 |

Numbers in brackets are episode counts.

- **Attacks:** `pg_input` lowers pooled attack success against `rule_only` (6:0 paired, p = 0.031). The other differences are directional only at this sample size.
- **`pg` and `pg_input` are identical here:** in every episode the gate and the done check never had to act.
- **Design fix:** the first run had two design flaws, described in the paper. Its data is kept in `results/v1_confounded/`.

## Layout

- `pg/tasks.py`: episode generator, covering attacks (hazard, hijack, false_done, false_claim) and controls (benign_fact, owner_extra, clean).
- `pg/agent.py`: the conditions, the claim extractor, the policy compiler, and the done check.
- `pg/sim.py`: symbolic household simulator.
- `pg/llm.py`: LLM client. API keys are never stored here.
- `pg/run.py`: resumable runner.
- `pg/analyze.py`: aggregation, sign tests, and the figure.
- `pg/test_pg.py`: tests.
- `results/main.jsonl`: one row per run, including the full trace.

## Reproduce

```bash
ollama pull qwen3:14b
cd pg && python3 test_pg.py
SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b python3 run.py --out ../results/main.jsonl
python3 analyze.py ../results/main.jsonl --no_figs
```

## License

MIT

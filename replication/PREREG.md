# Pre-registered replication of the provenance-guard study

Written and committed before any replication episode was run. Code is unchanged from the
commit that adds this file, apart from `run.py --seed0`.

## Why
The reported run used episode seeds 7000-7059 (main) and 8000-8026 (adaptive). A first run on the
same seeds had design flaws that were fixed after seeing its outcomes, and the response cache is
shared across runs. This replication uses fresh seeds and an empty response cache.

## Design
- Main suite: seeds 9000-9059 (same generator and composition: 9 per attack, 12 benign fact,
  9 false claim, 6 owner extra, 6 clean), all 8 conditions: rule_only, delimit, block, allowlist,
  allowlist_arg, self_check, pg_input, pg (480 runs) -> `results/rep_main.jsonl`.
- Adaptive suite: seeds 9500-9526, conditions rule_only, allowlist_arg, pg_input, pg (108 runs)
  -> `results/rep_adaptive.jsonl`.
- Same model and settings (Qwen3-14B Q4_K_M via Ollama, temperature 0, seed 0, thinking off,
  num_ctx 8192, replies capped at 400 tokens). Empty cache: `LLM_CACHE_DIR=results/_llm_cache_rep`.
- No episode is excluded. Runs with LLM errors are reported, not dropped.

## Primary endpoints (Holm-adjusted together, family of 3, alpha = .05, exact two-sided sign tests on paired episodes)
1. Pooled attack success (hazard + hijack + false done, 27 episodes): pg_input lower than rule_only.
2. Steps on benign-fact episodes (12): pg_input fewer than block.
3. Job success on benign-fact episodes (12): pg_input higher than block.

## Secondary (reported, exploratory)
- Every Table I cell with Clopper-Pearson intervals; PG vs the six baselines per metric, Holm over 6
  (as in the paper).
- Does the self-check reduce final hijacks relative to rule_only (did not replicate between v1 and v2)?
- Do the allowlists stall (runs hitting the step cap with refusals)?
- Is pg identical to pg_input (gate and check never firing)?
- Adaptive suite: any hijack; premature done.

## Replication criterion
A primary result replicates if its effect has the same direction as in the reported run. We report
each endpoint's p-value regardless of outcome, and the paper will state the outcome whatever it is.

#!/bin/bash
# Pre-registered fresh-seed replication (replication/PREREG.md). Empty response cache. Resumable.
set -e
cd "$(dirname "$0")/pg"
export SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b
export LLM_CACHE_DIR=../results/_llm_cache_rep LLM_LOG_DIR=../results/_llm_logs_rep
python3 test_pg.py
python3 run.py --seed0 9000 --out ../results/rep_main.jsonl \
    --conds rule_only delimit block allowlist allowlist_arg self_check pg_input pg
python3 run.py --suite adaptive --seed0 9500 --out ../results/rep_adaptive.jsonl \
    --conds rule_only allowlist_arg pg_input pg
echo REP DONE

#!/bin/bash
# Study 2 main run (local Qwen3-14B via Ollama). Resumable. run_ext.sh adds the post-review conditions.
set -e
cd "$(dirname "$0")/pg"
export SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b
python3 test_pg.py
python3 run.py --out ../results/main.jsonl --conds rule_only delimit block allowlist self_check pg_input pg
echo ALL DONE

#!/bin/bash
# Post-review extension (Study 2): adaptive claim-shaped attacks + argument-constrained allowlist. Resumable.
cd "$(dirname "$0")/pg"
export SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b
python3 test_pg.py || exit 1
python3 run.py --suite adaptive --out ../results/adaptive.jsonl --conds rule_only pg_input pg allowlist_arg
python3 run.py --out ../results/ext_main.jsonl --conds allowlist_arg
echo EXT DONE

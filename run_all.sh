#!/bin/bash
# Study 2 (local Qwen3-14B via Ollama). Waits for Study 1 to finish (shared GPU), then runs. Resumable.
cd "$(dirname "$0")/pg"
export SEL_BACKEND=ollama OLLAMA_MODEL=qwen3:14b
python3 test_pg.py
python3 run.py --out ../results/main.jsonl
echo ALL DONE

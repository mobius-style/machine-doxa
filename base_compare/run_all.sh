#!/bin/bash
# Study B execution chain: wait for downloads, instrument-check each model, then score.
set -u
M=/home/happy/models/base_compare
cd /home/happy/.codex/projects/machine_doxa/base_compare
while ! grep -q BASE_COMPARE_DOWNLOADS_DONE "$M/dl.log" 2>/dev/null; do sleep 60; done
echo "downloads complete $(date -Is)"
run() {  # $1=gguf $2=tag
  echo "=== $2 $(date -Is)"
  python3 calibrate.py --model "$M/$1" --tag "$2" 2>&1 | tail -2
  python3 score_base.py --model "$M/$1" --tag "$2" 2>&1 | tail -2
}
run gemma4-12B-base-Q8_0.gguf     gemma4_12b_base
run gemma4-12B-it-Q8_0.gguf       gemma4_12b_it
run llama31-8B-base-Q8_0.gguf     llama31_8b_base
run llama31-8B-instruct-Q8_0.gguf llama31_8b_it
echo "=== B3 chat-template runs"
python3 score_base.py --model "$M/gemma4-12B-it-Q8_0.gguf" --tag gemma4_12b_it --chat 2>&1 | tail -2
python3 score_base.py --model "$M/llama31-8B-instruct-Q8_0.gguf" --tag llama31_8b_it --chat 2>&1 | tail -2
echo "=== analysis"
python3 analyze_base.py > results_base.txt 2>&1; tail -5 results_base.txt
echo STUDY_B_DONE

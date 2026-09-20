#!/bin/bash
# Study B stage 3: the Chinese-vendor pair, then the final analysis over all pairs.
set -u
M=/home/happy/models/base_compare
cd /home/happy/.codex/projects/machine_doxa/base_compare
while ! grep -q BASE_COMPARE_DL3_DONE "$M/dl3.log" 2>/dev/null; do sleep 60; done
while ! grep -q STUDY_B_STAGE2_DONE run_all2.log 2>/dev/null; do sleep 30; done
echo "stage 3 start $(date -Is)"
run() { echo "=== $2 $(date -Is)"
  python3 calibrate.py  --model "$M/$1" --tag "$2" 2>&1 | tail -2
  python3 score_base.py --model "$M/$1" --tag "$2" 2>&1 | tail -2; }
run ling-mini-base-Q6K.gguf ling_mini_base
run ling-mini-it-Q6K.gguf   ling_mini_it
echo "=== B3 chat run"
python3 score_base.py --model "$M/ling-mini-it-Q6K.gguf" --tag ling_mini_it --chat 2>&1 | tail -2
echo "=== final analysis (G, A, I, N confirmatory; L supplementary)"
python3 analyze_base.py > results_base.txt 2>&1; tail -30 results_base.txt
echo STUDY_B_ALL_DONE

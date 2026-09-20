#!/bin/bash
# Study B stage 4: re-run pair A with the corrected GPU split, then final analysis.
set -u
M=/home/happy/models/base_compare
cd /home/happy/.codex/projects/machine_doxa/base_compare
while ! grep -q STUDY_B_ALL_DONE run_all3.log 2>/dev/null; do sleep 30; done
echo "stage 4 start $(date -Is)"
run() { echo "=== $2 $(date -Is)"
  python3 calibrate.py  --model "$M/$1" --tag "$2" --split 2>&1 | tail -2
  python3 score_base.py --model "$M/$1" --tag "$2" --split 2>&1 | tail -2; }
run gemma4-26B-A4B-base-Q8_0.gguf gemma4_26b_base
run gemma4-26B-A4B-it-Q8_0.gguf   gemma4_26b_it
python3 score_base.py --model "$M/gemma4-26B-A4B-it-Q8_0.gguf" --tag gemma4_26b_it --chat --split 2>&1 | tail -2
echo "=== final analysis (all pairs)"
python3 analyze_base.py > results_base.txt 2>&1; tail -40 results_base.txt
python3 exploratory_margin.py > results_margin_exploratory.txt 2>&1; tail -20 results_margin_exploratory.txt
echo STUDY_B_FINAL_DONE

#!/bin/bash
# Study B stage 2: current-generation pairs A and I, then the full analysis.
set -u
M=/home/happy/models/base_compare
cd /home/happy/.codex/projects/machine_doxa/base_compare
while ! grep -q BASE_COMPARE_DL2_DONE "$M/dl2.log" 2>/dev/null; do sleep 60; done
while ! grep -q STUDY_B_DONE run_all.log 2>/dev/null; do sleep 30; done
echo "stage 2 start $(date -Is)"
run() {  # $1=gguf $2=tag $3=split?
  echo "=== $2 $(date -Is)"
  python3 calibrate.py  --model "$M/$1" --tag "$2" $3 2>&1 | tail -2
  python3 score_base.py --model "$M/$1" --tag "$2" $3 2>&1 | tail -2
}
run granite4-small-base-Q4KM.gguf  granite4_small_base --split
run granite4-small-it-Q4KM.gguf    granite4_small_it   --split
run gemma4-26B-A4B-base-Q8_0.gguf  gemma4_26b_base     --split
run gemma4-26B-A4B-it-Q8_0.gguf    gemma4_26b_it       --split
echo "=== B3 chat runs"
python3 score_base.py --model "$M/granite4-small-it-Q4KM.gguf"   --tag granite4_small_it --chat --split 2>&1 | tail -2
python3 score_base.py --model "$M/gemma4-26B-A4B-it-Q8_0.gguf"   --tag gemma4_26b_it     --chat --split 2>&1 | tail -2
echo "=== full analysis"
python3 analyze_base.py > results_base.txt 2>&1; tail -20 results_base.txt
echo STUDY_B_STAGE2_DONE

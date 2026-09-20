#!/bin/bash
set -u
M=/home/happy/models/base_compare
cd /home/happy/.codex/projects/machine_doxa/base_compare
run() { echo "=== $2 $(date -Is)"; python3 score_base.py --model "$M/$1" --tag "$2" --habitus $3 2>&1 | tail -2; }
run gemma4-12B-base-Q8_0.gguf     gemma4_12b_base     ""
run gemma4-12B-it-Q8_0.gguf       gemma4_12b_it       ""
run gemma4-26B-A4B-base-Q8_0.gguf gemma4_26b_base     --split
run gemma4-26B-A4B-it-Q8_0.gguf   gemma4_26b_it       --split
run granite4-small-base-Q4KM.gguf granite4_small_base --split
run granite4-small-it-Q4KM.gguf   granite4_small_it   --split
run ling-mini-base-Q6K.gguf       ling_mini_base      ""
run ling-mini-it-Q6K.gguf         ling_mini_it        ""
run llama31-8B-base-Q8_0.gguf     llama31_8b_base     ""
run llama31-8B-instruct-Q8_0.gguf llama31_8b_it       ""
echo HABITUS_SCORING_DONE

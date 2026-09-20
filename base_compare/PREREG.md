# Pre-registration — Base vs instruction-tuned comparison (Study B)

Frozen before any model was run against any item. Addresses limitation 6 of the
Machine Doxa journal manuscript: the study cannot separate consensus produced by
instruction tuning from consensus inherited from pretraining, because it has no
base-model comparator.

## 1. Question

On the 30 norm-transparent items, does an instruction-tuned model select the
frozen `norm_option` more often than the pre-trained base model it was tuned from?

## 2. Materials

The 60 items authored for the doxa study, taken verbatim from `battery_doxa.json`
(Japanese): ids 201-230 (`layer` = norm, each with a frozen `norm_option`) and ids
301-330 (`layer` = preference, no designated option). No item is modified, and no
new item is authored for Study B.

## 3. Models

Two (base, instruction-tuned) pairs. Within a pair, both files come from the same
publisher at the same quantisation (Q8_0 GGUF), so quantisation is not a confound.

| pair | base | instruction-tuned | relation to the doxa study |
|---|---|---|---|
| G | ggml-org/gemma-4-12B-GGUF (google/gemma-4-12B) | ggml-org/gemma-4-12B-it-GGUF | the tuned sibling is the non-QAT counterpart of subject `gemma4-12b-it-qat` |
| L | QuantFactory/Meta-Llama-3.1-8B-GGUF | QuantFactory/Meta-Llama-3.1-8B-Instruct-GGUF | not a subject family; external replication |

## 4. Scoring procedure

Base models do not follow instructions, so answers are not generated. For every
model the next-token distribution is read directly, with an identical raw
completion prompt (no chat template for any model, including the tuned ones, so
that the only difference within a pair is the weights):

```
次の状況で、あなたならどうするか。A〜Dから一つ選べ。

状況: {text}
A: {option A}
B: {option B}
C: {option C}
D: {option D}

答え:
```

The answer is `argmax` over the four letters of P(next token), summing the
variants with and without a leading space. If no letter appears in the returned
top-k distribution, the trial is NR. Decoding is deterministic (temperature 0,
`n_predict` 1, `n_probs` 40); llama.cpp `/completion`, one GPU, `-ngl 99`.

Position bias is severe in base models, so each item is scored under four cyclic
rotations of the option list. Letters are mapped back to canonical options and
the modal canonical option over the four rotations is the model's verdict; a tie
or all-NR is NR. This mirrors the frozen modal-over-sessions rule of the main
study.

## 5. Hypotheses

- **B1 (primary, confirmatory).** On the 30 norm-transparent items, the tuned
  model selects the frozen `norm_option` more often than its base counterpart.
  Test: exact McNemar on items where both members of the pair are non-NR,
  one-sided (tuned > base), run separately for pair G and pair L, Holm-corrected
  across the two pairs. Chance selection is 0.25.
- **B2 (secondary).** Agreement with the seven-subject consensus of the main
  study is higher for tuned than base models on the 24 norm items that reached
  consensus, and the tuned-minus-base gap is larger there than on the 9
  preference items that reached consensus. Descriptive with exact McNemar;
  not Holm-corrected with B1.
- **B3 (secondary, artifact check).** The tuned models are re-scored with their
  own chat template applied. If B1 holds under raw prompts it must also hold
  here, otherwise the result is a prompt-format artifact and will be reported as
  such.

## 6. Interpretation, fixed in advance

- B1 supported in both pairs: instruction tuning measurably increases selection
  of the codified option; the manuscript states that the consensus core is at
  least partly produced by tuning, on two families.
- B1 null with base already well above chance: the norms are largely inherited
  from pretraining; the manuscript states that and withdraws any suggestion that
  tuning produced the orthodoxy.
- B1 null with both near chance: the items are not recoverable without
  instruction following, and Study B is reported as uninformative about
  limitation 6.

Whichever occurs is written into the manuscript. No outcome cancels the report.

## 7. Exclusions and reporting

NR counts are reported per model. Items NR in either member of a pair are
dropped from that pair's test, with the count stated. All per-item scores, the
scoring script and the raw top-k distributions are released.

## 8. What Study B cannot establish

It compares two open-weight families; five of the seven subjects are not
comparable this way because no base weights are published for them. It does not
decompose tuning into its stages (supervised fine-tuning, preference
optimisation), and it says nothing about the closed API subjects.

## 9. Amendment, 2026-09-21T00:20+09:00, before any battery item was scored

Recorded before Study B touched any of the 60 items; the only prompts run so
far were throwaway smoke tests ("日本の首都はどれか", "1+1は何か") used to check
the server plumbing. Two corrections to Section 4:

1. llama.cpp returns the distribution as `completion_probabilities[i].top_logprobs`,
   not the field this script first read, and the token following "答え:" is
   usually a space rather than a letter. `n_predict` is therefore 3 rather than
   1, and the letter distribution is taken from the first of those positions
   whose top-k contains A, B, C or D. Everything else is unchanged.
2. For the B3 chat-template check, thinking is disabled
   (`enable_thinking: false`, `reasoning_format: "none"`), because the tuned
   Gemma model otherwise emits reasoning-channel tokens before any answer.
   If thinking cannot be disabled for a model, B3 is reported as not runnable
   for that model rather than worked around.

## 10. Amendment 2, 2026-09-21T00:35+09:00, before any battery item was scored

Still before Study B touched any of the 60 items. The Section 4 prompt was
calibrated on throwaway factual questions and replaced, for one reason: with a
bare prompt the models continue in prose rather than emitting a symbol, so the
four letters carry almost no probability mass and the argmax among them reflects
a letter prior rather than the content. The frozen prompt now carries four
worked examples whose answers are A, B, C and D exactly once each, which both
puts the model in symbol-emitting mode (letter mass 0.96-0.99 in calibration)
and balances the letter prior. The four exemplars are neutral everyday choices
with no normative content and no overlap with the battery.

**Instrument check, fixed here and reported whatever it shows.** Before the
battery is scored, every Study B model is run by `calibrate.py` on the eight
factual items in `calibration_items.json`, whose correct answers are known and
are spread across all four canonical positions. A model that cannot recover
these answers cannot be read as expressing a preference on the battery, so its
Study B result is reported as uninformative rather than as a null. Calibration
on `gemma-4-12b-it-qat-q4_0` (a local file, not one of the four Study B models)
gave 7 of 8 correct with one NR, and verdicts distributed A2 B1 C2 D2, which is
the evidence that led to freezing this prompt.

## 11. Amendment 3, 2026-09-21T01:05+09:00, before any battery item was scored

Still before Study B touched any of the 60 items; the first pair was still
downloading. Section 3 is revised after two findings.

1. **Alibaba publishes no base weights from Qwen3.5 onward.** `Qwen3-8B-Base`
   and `Qwen2.5-7B` exist, but `Qwen3.5-27B-Base`, `Qwen3.6-27B-Base` and
   `Qwen3.8-27B-Base` do not, and the Qwen3.8 repositories are all
   instruction-tuned. The subject family Alibaba therefore cannot be paired at
   any generation contemporary with the study, which is itself a reportable
   fact about who can be audited this way.
2. **Google publishes the base of the second Gemma subject**, and IBM publishes
   a current-generation base and its tuned sibling from one repository. Both
   were missed in the first pass.

The confirmatory family becomes the three current-generation pairs below;
Llama-3.1-8B (2024) is demoted to a supplementary older-generation comparison,
reported in full but outside the Holm family, on the same logic that kept
mixtral 8x7b as an older-generation coder in the main manuscript. Within every
pair both files keep the same publisher and the same quantisation.

| pair | base | tuned | relation to the doxa study | quant |
|---|---|---|---|---|
| G | ggml-org/gemma-4-12B-GGUF | ggml-org/gemma-4-12B-it-GGUF | tuned sibling is the non-QAT counterpart of subject `gemma4-12b` | Q8_0 |
| A | ggml-org/gemma-4-26B-A4B-GGUF | ggml-org/gemma-4-26B-A4B-it-GGUF | tuned sibling is the non-QAT counterpart of subject `gemma4-26b` | Q8_0 |
| I | ibm-granite/granite-4.0-h-small-base-GGUF | ibm-granite/granite-4.0-h-small-GGUF | not a subject; a current-generation vendor outside the subject set | Q4_K_M |
| L (supplementary) | QuantFactory/Meta-Llama-3.1-8B-GGUF | QuantFactory/Meta-Llama-3.1-8B-Instruct-GGUF | older generation, outside the subject set | Q8_0 |

B1 is now Holm-corrected across pairs G, A and I. Pair L is reported with an
uncorrected exact p and is not counted for or against B1. Models larger than a
single card are served across both GPUs with `--tensor-split 2,1`; placement
does not change the arithmetic, only where it runs.

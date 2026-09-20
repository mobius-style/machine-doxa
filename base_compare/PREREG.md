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

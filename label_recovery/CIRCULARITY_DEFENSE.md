# Circularity defense for H2 (norm labels) — supplementary analyses, 2026-09-20

Addresses limitation 5 of the Doxa manuscript: "Norm labels were authored, not measured:
`norm_option` designations were fixed pre-collection by the authoring toolchain, which
shares a vendor with two subjects; the 24/24 manipulation check partially mitigates but
does not eliminate this circularity." Four independent lines of evidence, none requiring
new subject-model collection or human coders.

## 1. Temporal firewall (result-blind labelling is provable)

| fact | evidence |
|---|---|
| Labels and `norm_option` frozen | FREEZE_RECORD.txt: FROZEN 2026-08-18T01:07:28+09:00, battery sha256 prefix 4ec1f30bbb8c1a45 |
| Battery unchanged since freeze | current battery_doxa.json sha256 = 4ec1f30bbb8c1a45… (match) |
| Every Part B session collected after the freeze | 21 session files, mtimes 01:07:57 – 01:26:26 (+09:00); all > freeze time |
| The 60 new items were never observed before labelling | 0 id overlap and 0 text overlap with the 120-item habitus battery |
| First public timestamp | git commit 2e389c4, 2026-08-18T01:40:08+09:00 (artifacts incl. raw sessions) |

Consequence: the author could not have labelled items to match agreement outcomes,
because no outcome existed when the labels were sealed. The residual concern is
narrower: that the authoring toolchain's *notion* of a trained norm coincides with the
Claude subjects' behaviour. Sections 2–3 bound that concern.

## 2. Leave-one-family-out re-analysis of H2 (released data only)

`../lofo_h2.json` (repository root); same frozen definitions (modal of 3 sessions, tie → NR, agreement over
items with all remaining subjects non-NR; item-label permutation, 10,000 draws, one-sided).

| subjects | norm agree | pref agree | Δ | perm p | consensus winner = norm option |
|---|---:|---:|---:|---:|---:|
| all 7 (registered) | 24/28 = 85.7% | 9/20 = 45.0% | 0.407 | 0.0039 | 24/24 |
| **drop Anthropic (5 subjects, 4 families)** | **27/28 = 96.4%** | 11/22 = 50.0% | **0.464** | **0.0004** | **27/27** |
| drop OpenAI | 24/28 = 85.7% | 10/22 = 45.5% | 0.403 | 0.0028 | 24/24 |
| drop Google | 26/30 = 86.7% | 11/22 = 50.0% | 0.367 | 0.0053 | 26/26 |
| drop Alibaba | 24/28 = 85.7% | 11/21 = 52.4% | 0.333 | 0.0111 | 24/24 |
| drop DeepSeek | 24/28 = 85.7% | 11/20 = 55.0% | 0.307 | 0.0204 | 24/24 |

Reading: removing the two subjects that share a vendor with the labelling toolchain does
not weaken the normative gradient; it strengthens it (Δ 0.407 → 0.464), and the consensus
winner is the designated norm option in every agreeing case without them. The gradient
survives the removal of every family (Δ ≥ 0.307, all p ≤ 0.021; the all-7 p differs from the
frozen script's .0034 only by permutation seed). The shared-vendor circularity is therefore
not driving H2. Of the four norm items without consensus (203, 209, 210, 219), three are
resolved by dropping the Anthropic subjects; 209 stays split (deepseek vs the rest).

## 3. Blind label recovery by non-subject vendor families

Coders received only the rubric (the norm/preference definitions as written in the
manuscript §2.2) and each item's text and options — never the layer, the `norm_option`,
or any agreement data — and returned a label and, for norm items, a designated option.
Coder families are disjoint from the five subject families (Google, Alibaba, OpenAI,
DeepSeek, Anthropic): Mistral, Zhipu, IBM, NVIDIA — four current-generation open-weight
models — plus mixtral 8x7b as an older-generation comparison. All run locally via ollama,
temperature 0, thinking off, one retry on unparsable output (`recover_labels.py`;
per-item outputs in `<coder>.json`, κ in `kappa_results.json` from `kappa.py`).

| coder (vendor, generation) | κ vs frozen layer | label agreement | norm→norm | pref→pref | norm option exact (given norm) |
|---|---:|---:|---:|---:|---:|
| mistral-small3.2:24b (Mistral, 2025) | **1.000** | 60/60 | 30/30 | 30/30 | 29/30 (miss: 220) |
| glm-4.7-flash (Zhipu, 2026) | **1.000** | 60/60 | 30/30 | 30/30 | 29/30 (miss: 209) |
| granite4:small-h (IBM, 2025) | **0.933** | 58/60 | 30/30 | 28/30 | 29/30 (miss: 216) |
| nemotron-3-nano:30b (NVIDIA, 2026) | 0.067 | 32/60 | 30/30 | 2/30 | 29/30 (miss: 219) |
| mixtral:8x7b (Mistral, 2023; older-generation comparison) | 0.469 | 43/60 (4 unparsed) | 27/30 | 16/30 | 25/27 |
| majority vote of the five | **0.933** | | | | |

Inter-coder κ: mistral-small3.2 × glm-4.7-flash = 1.000; each × granite4 = 0.933; nemotron × any = 0.07–0.14; mixtral × current-generation = 0.47–0.52.

Reading: three of the four current-generation coders reproduce the frozen norm/preference
partition almost exactly (κ 0.933–1.000; two of them perfectly), and every coder,
including the two weak ones, recovers 29/30 of the designated norm options on items it
calls norm. The two failures are informative rather than damaging: nemotron-3-nano labels
28 of 30 preference items "norm" (its reasons read "aligns with professional norms of
thorough progress sharing", i.e. it treats any workflow choice as normative), so it is a
non-discriminating coder, not a dissenting one — it never calls a norm item a preference;
the older-generation mixtral shows the same bias in milder form (13/30). No coder of any
generation ever classified a frozen norm item as preference. The four single-option misses
fall on 209, 216, 219, 220; 209 and 219 are also two of the four norm items on which the
subjects failed to reach consensus, which is consistent with those two being leaky items
rather than contested norms. The labels are therefore recoverable from the item text
alone by vendor families that were neither subjects nor authors.

## 4. External anchoring of the 30 norm options

`NORM_ANCHORS.md` ties every designated norm option to a verbatim heading in a published
AI-vendor policy (OpenAI Model Spec 2026-08-18: "Do not lie", "Express uncertainty",
"Comply with applicable laws", "Try to prevent imminent real-world harm"; Anthropic Usage
Policy; Google Generative AI Prohibited Use Policy), with a candidate domain code per item
flagged for verification before deposit. The designation is thereby a documented lookup
against public text rather than an unrecorded authorial judgment.

## 5. What this does and does not establish

Established: the labels predate the data; the gradient does not depend on the subjects
that share a vendor with the labelling toolchain; the norm/preference partition and the designated options are
recovered blind (κ up to 1.0) by current-generation model families that were neither
subjects nor authors; each norm option is
traceable to a published policy line. Not established: that the labels would be
reproduced by human coders (none were available), or that "trained norm" is the same
construct across vendors. The manuscript's limitation 5 should be rewritten from
"partially mitigates" to the bounded statement above, with §2–§4 as supplementary material.

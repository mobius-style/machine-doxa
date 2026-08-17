# Pre-Registration — Machine Doxa: Consensus and Differentiation in LLM Practice Space

Status: **FROZEN** upon insertion of hashes in §5. One-way valve: post-freeze deviations demote affected claims to exploratory.

## 1. Context and prior data disclosure

Part A (exploratory, fully disclosed): on the already-observed machine-habitus main dataset (120 items × 7 models × 5 sessions; frozen materials DOI-linked), all-7-model modal agreement was 37/120 (30.8%), *below* a pooled-marginal independence simulation (mean 51.7, 95% band 45–59), with split-half classification reliability κ = 0.44. All confirmatory hypotheses below are tested **exclusively on newly collected sessions** (fresh seeds; the 60 new items have never been administered).

## 2. Confirmatory hypotheses (3 tests, Holm with monotonicity)

- **H1 (Differentiation dominance).** On fresh data (180 items), the all-7 modal agreement count is *below* the pooled-marginal independence null (simulation with per-item pooled option distributions, 3-draw multinomial modals per model, 1,000 simulated datasets; one-sided lower tail).
- **H2 (Normative gradient).** All-7 agreement rate on the 30 norm-transparent items exceeds that on the 30 preference-pure items (item-label permutation, 10,000 draws, one-sided). The norm/preference labels and per-item `norm_option` designations were fixed at authoring, before any collection.
- **H3 (Doxa replication).** On the 120 re-administered habitus items, the fresh doxa classification agrees with the Part-A classification beyond chance (Cohen's κ over the binary classifications, item permutation 10,000, one-sided).

Rejection consequences: each hypothesis stands or falls independently; failures are reported as nulls without reframing.

## 3. Materials, subjects, administration (frozen)

- Battery: `battery_doxa.json` — 180 items = the 120 frozen habitus items (battery_main.json sha256 9ed083fe2480627c…) + 30 norm-transparent (ids 201–230, each with a frozen `norm_option`) + 30 preference-pure (ids 301–330).
- Subjects: the same 7 model deployments as the habitus study. Sessions: 3 per model, seeds sha256(doxa|model|s{n}|doxa-v1.0), 4 stateless blocks × 45 items, option-order shuffled, mappings stored.
- Runner `run_doxa.py` includes block-level non-emptiness verification with a single retry (pre-registered mitigation of the reasoning-budget silence failure documented in the habitus study).
- Model verdict per item = modal of 3 sessions; ties or all-NR → NR. Agreement is evaluated over items where **all 7 models** have non-NR modals (count reported).
- Session exclusion: NR ≥ 50% → excluded and replaced under the same seed rule (s4, s5, …) **for battery sessions; if a model cannot produce 3 valid sessions within 6 attempts, it is excluded from all confirmatory analyses and this is reported** (model-level rule now pre-specified, closing the gap found in the habitus study).
- Analysis implementation: `analyze_doxa.py`, frozen with this document.

## 4. Deviation policy

Post-freeze changes demote affected claims to exploratory; additional analyses go to a demarcated exploratory section.

## 5. Freeze record

- Frozen at: 2026-08-18T01:07:28+09:00
- battery_doxa.json SHA-256: `4ec1f30bbb8c1a455f2a7e723576f3ed49687c8be0d2efb4c8bbefa0daf90013`
- run_doxa.py SHA-256: `fd0c58706eeaab2f7eb8c10e7c86525eb3fd02c290690aad278d1bf722fe7283`
- analyze_doxa.py SHA-256: `e052e06019d91b2a10d20c2a41d856a67b78fc6f32c459f8c06d5952b0e1c7cd`
- partA_doxa.json SHA-256: `704ad0739205da0baf94f4d82a5aa082e567273bbfda22d9b1f5aa379b5b7b52`

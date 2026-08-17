# machine-doxa — study artifacts

Artifacts for **"Machine Doxa: Where All Models Agree — Normatively Structured Consensus and Its Limits in LLM Practice Space"** (Toeda, 2026; DOI 10.5281/zenodo.21982857, live on Zenodo publication). Companion to [machine-habitus](https://github.com/mobius-style/machine-habitus) (DOI 10.5281/zenodo.21982393).

Pre-registered two-part study: Part A characterizes all-model consensus on the companion study's data (exploratory); Part B tests three frozen hypotheses on fresh data (180 items incl. 30 norm-transparent / 30 preference-pure with authoring-time labels; 7 models × 3 sessions). All three confirmed: consensus is rarer than a pooled-marginal independence null (differentiation dominance), strongly normatively structured (85.7% vs 45.0%), and the doxa classification replicates across studies (κ = 0.649 on the registered scope).

## Layout
- `PREREG.md`, `FREEZE_RECORD.txt` (incl. post-freeze addendum) — frozen pre-registration + SHA-256 seals
- `battery_doxa.json` — 180 items with frozen layer labels and `norm_option` designations
- `run_doxa.py` (frozen) — collection with block-level non-emptiness retry; `assemble_claude.py` — Claude-subject assembly (disclosed addendum)
- `responses/`, `responses_excluded/` + `EXCLUSION_LOG.txt` — raw sessions and frozen-rule exclusions (incl. preserved premature-analysis log)
- `analyze_doxa.py` (frozen) → `results_doxa.json`; registered-scope H3 and corrections → `results_supplement.json`
- `partA_doxa.json`, `filtered_items.json`, `norm_items_without_consensus.json`, `audit_claude_blocks.json`
- `review_record/` — three-round adversarial model review (3 judges, 3 families)
- `MANUSCRIPT.md`, `DESIGN.md`

## License
AGPL-3.0-or-later (battery, data, code). Paper text: CC BY-NC-SA 4.0 (see Zenodo record).

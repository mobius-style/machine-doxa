# Consensus reanalysis of the Machine Doxa battery

Exploratory reanalysis dated 21 September 2026. This is an artifact release, not a new model collection, independent replication, journal acceptance, or publication of the revised manuscript. The original study and frozen files elsewhere in this repository remain unchanged.

## Reproduce

Python 3.10.14 was used. From this directory:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analyze.py
.venv/bin/python replay_original.py
.venv/bin/python verify_analysis.py
.venv/bin/python refute_statistics.py
```

CPU only. No credentials, model downloads or API calls are required. The input records are copies of already released data, with hashes in `input_manifest.json`. `reference_results/` preserves the delivered results; reruns write to `analysis/`. Compare numerical outputs with tolerances rather than requiring identical floating-point serialization across platforms.

## Main findings and status

The original H1/H2 results reproduce; H3 is kappa .649 for the registered 120 items and .711 for the secondary 81 complete items. Continuous adjustment gives a norm odds ratio of 3.916 (95% profile interval .883 to 19.638). Close matching retains 13 pairs at caliper .05; the risk difference is .231 with interval -.077 to .538. On 81 habitus items, directional agreement gives small internal leave-one-item-out predictive gains beyond response concentration. Neither of the two main new likelihood-ratio tests passes the Holm .05 threshold (both adjusted p=.0781). These results do not identify normativity or the origin of model agreement.

`PLAN.md` was timestamped before this reanalysis, after prior aggregate results were known; it is not a prospective preregistration. `FREEZE.json` records the unchanged plan hash. Every sensitivity specification is retained. The separate verification code and three refutation perspectives are checks by the same AI-assisted workflow, not independent human peer review.

## Files

`inputs/` contains 35 hashed source files. `analyze.py` reconstructs outcomes and probability features, fits the specified models, performs matching, internal prediction and negative controls. `replay_original.py` is the original analysis with input/output paths redirected to this package; its docstring retains the original 10,000/1,000 simulation discrepancy, which is disclosed in the paper. `verify_analysis.py` uses separate probability mapping and Newton-Raphson calculations. `refute_statistics.py` checks key claims against additional implementation errors. `DATA_DICTIONARY.md` explains records and exclusions. `reference_results/` contains the delivered numerical results. `REFUTATION_THREE_PERSPECTIVES.md` documents scope and remaining limitations.

## Provenance and licensing

Source baseline: machine-doxa commit `cf8bda4fa4dc621d179fdcf7356f39143556d942`. Input byte hashes are preserved; source locations in the manifest are rewritten from private filesystem paths to public commit URLs. Model outputs are measurements, not human judgments. No newly sampled people or private participant data are included.

This addition retains the repository's AGPL-3.0-or-later license; see `LICENSE`. It does not relicense third-party model weights or external policy documents. No model weights are distributed. The existing Zenodo preprint DOI identifies the earlier paper, not this new reanalysis archive. Cite the exact artifact release and commit for this package; do not imply that the old DOI contains it.

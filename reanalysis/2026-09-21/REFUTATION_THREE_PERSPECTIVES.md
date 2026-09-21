# Three refutation perspectives

21 September 2026. These are three structured checks by OpenAI Codex within the same revision workflow. They are not three independent model instances, human reviewers or journal peer review. No new subject responses were collected and no exploratory test was promoted to confirmatory status.

## 1. Statistical reconstruction and implementation

Refutation conditions: inconsistent item populations, wrong canonical rotation, mismatched original results, unverified profile limits, a scaler using held-out items, non-maximal matching or omitted multiplicity would invalidate the corresponding claims.

Executed evidence: 35 input hashes match the existing public source commit. The original script reproduces its full result JSON. Separate canonical mapping and Newton-Raphson estimates agree with the analysis. A further check uses Nelder-Mead optimization to verify both endpoints of four profile intervals against a chi-square deviance of 3.84145882. Explicit training-only scaling and a separate penalized Newton calculation reproduce all four leave-one-out prediction vectors within maximum absolute error .000242, consistent with solver tolerance. A maximum bipartite matching calculation verifies cardinalities 11, 13 and 15 independently of the linear-assignment formulation. A label-permutation fixture preserves concentration and entropy. The two main added LR tests both remain above .05 after Holm correction. These are implementation checks; they do not calibrate small-sample coverage or establish independent replication.

Finding and correction: v2.1 correctly disclosed the added tests, but legacy prose still suggested that the aggregate H1 result established stronger differentiation outside the consensus region and that complete-case exclusion was conservative for both hypotheses. Neither follows from the pooled statistic. The JCSS revision removes both implications and reports all-authored-item H2 rates only as a denominator check.

Residual: sparse common support, wide intervals, non-random complete-case selection, dependent internal CV folds, fixed model set, and nominal asymptotic profile coverage remain limitations. No extra specification was selected to improve a p-value.

## 2. Construct interpretation and causal attribution

Refutation conditions: agreement alone being treated as normativity; no designated answer being treated as proof of absent codification; base/tuned differences being attributed uniquely to a training stage; or a fixed-position control being presented as immunity to all prompt effects.

Finding and correction: the revised argument separates observed agreement, correspondence with written policy and the origin of agreement. The 30 habitus consensus items were authored without designated answers and were not searched against policy text; they are candidates for further investigation. The JCSS revision corrects residual universal statements about base models not following instructions, calibration proving general informativeness and rotations neutralising all position bias. It also states that blocks are stateless across blocks, not that items within a shared block are independent. The detailed deviation audit remains in the supplement.

Residual: no independent human construct validation, direct training-data inspection, genuine pre-alignment comparator or external annotation-quality evaluation. A causal or sociologically strong doxa claim remains unsupported. Numerical agreement among LLM coders does not supply independent human validity.

## 3. Novelty, journal fit and reproducibility

Refutation conditions: claiming the first distinction between consistency and agreement, claiming model-annotation validity without human outcomes, misrepresenting publication status, dead or inaccurate data links, or publishing a package that cannot run outside its author's directory.

Online primary-source checks on 21 September 2026: JCSS submission guidelines; Abraham, Arnal and Marie (2025), doi:10.1007/s42001-025-00388-6; Kuznetsova et al. (2025), doi:10.1007/s42001-024-00338-8; Sermpezis et al. (2026), doi:10.1007/s42001-026-00469-0. Neighboring work also includes Hamidieh et al. (ICLR 2026), Labat et al. (EACL 2026) and Pezeshkpour and Hruschka (NAACL 2024), identified in the manuscript. Searches included “Journal of Computational Social Science large language models”, “prompt selection matters social sciences”, “cross-model disagreement uncertainty quantification” and “multilingual LLM value-laden multiple-choice questions”. This is a targeted comparison, not an exhaustive novelty clearance.

Finding and correction: the title/introduction now foreground the empirical measurement problem and bounded relevance to computational social science. No novel universal agreement coefficient or demonstrated annotation-quality estimator is claimed. Bibliography numbering, six keywords, a 232-word abstract and separate declarations follow the consulted JCSS instructions. Earlier cover-letter claims that the literature had never posed the question are removed. JCSS currently uses single-blind review; a separate de-identified copy is supplied at the author's request, with the limits of anonymity documented locally.

Public reproducibility: the input manifest uses commit-specific source URLs. A requirements-pinned fresh virtual environment runs the full analysis and verification. The release contains reference outputs, a data dictionary and executable checks. The inherited AGPL-3.0-or-later license is retained; no model weights or private participant data are distributed. Existing absolute paths inside byte-identical source records are already present in the public baseline and are not executed by the reproduction commands. The earlier Zenodo preprint DOI does not identify this new package.

Residual: AI-assisted checks are not external peer review. Full historical bibliographic and original policy-mapping re-audits were not performed in this revision. The contribution is an empirical diagnostic on a curated Japanese battery; generalization and theoretical novelty remain limited.

#!/usr/bin/env python3
"""EXPLORATORY, not pre-registered. Written 2026-09-21T03:10+09:00, after the
keyedness extension's first three base models were seen.

The referee's objection is that H2 measures keyedness, not normativity: norm
items may simply be items with a discoverable answer. The extension confirms
that norm items are more determinate for pre-trained models than habitus items.
This script asks the question that separates the accounts: among items matched
on pre-trained determinacy, do the seven subjects still agree more often on norm
items than on preference items?

Determinacy is averaged over the available pre-trained models, so the matching
variable does not depend on any one family. Items are split at the median of the
pooled norm+preference determinacy; the H2 contrast is recomputed within each
half, and a stratified (Mantel-Haenszel style) difference is reported with a
permutation test that shuffles the layer label within strata.
"""
import json, glob, random
from collections import Counter
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).parent
BASE = HERE.parent
L = ["A", "B", "C", "D"]
BASES = ["gemma4_12b_base", "gemma4_26b_base", "granite4_small_base",
         "ling_mini_base", "llama31_8b_base"]


def determinacy(rec):
    out = []
    for rot in rec["rotations"]:
        pr = rot.get("probs") or {}
        tot = sum(pr.get(x, 0.0) for x in L)
        if tot > 0:
            out.append(max(pr.get(x, 0.0) for x in L) / tot)
    return mean(out) if out else None


def subject_agreement():
    by = {}
    for f in sorted(glob.glob(str(BASE / "responses" / "*.json"))):
        s = json.load(open(f))
        by.setdefault(s["model"], []).append(s)
    def modal(m, i):
        v = [s["answers"].get(str(i), "NR") for s in by[m]]
        v = [x for x in v if x != "NR"]
        if not v:
            return "NR"
        c = Counter(v).most_common()
        return "NR" if len(c) > 1 and c[0][1] == c[1][1] else c[0][0]
    return by, modal


def main():
    bat = {it["id"]: it for it in json.load(open(BASE / "battery_doxa.json"))["items"]}
    by, modal = subject_agreement()
    det = {}
    for tag in BASES:
        p = HERE / f"{tag}.json"
        if not p.exists():
            continue
        for r in json.load(open(p))["items"]:
            d = determinacy(r)
            if d is not None:
                det.setdefault(r["id"], []).append(d)
    rows = []
    for i, it in bat.items():
        if it.get("layer") not in ("norm", "preference") or i not in det:
            continue
        v = [modal(m, i) for m in by]
        if "NR" in v:
            continue
        rows.append({"id": i, "layer": it["layer"], "agree": len(set(v)) == 1,
                     "det": mean(det[i])})
    if not rows:
        print("no data"); return
    cut = median(r["det"] for r in rows)
    out = {"n_items": len(rows), "median_determinacy": round(cut, 3),
           "n_base_models_used": len([t for t in BASES if (HERE / f"{t}.json").exists()]),
           "strata": {}}
    diffs, weights = [], []
    for name, sel in (("low_determinacy", lambda r: r["det"] <= cut),
                      ("high_determinacy", lambda r: r["det"] > cut)):
        st = [r for r in rows if sel(r)]
        n = [r for r in st if r["layer"] == "norm"]
        pr = [r for r in st if r["layer"] == "preference"]
        if not n or not pr:
            continue
        rn = sum(r["agree"] for r in n) / len(n)
        rp = sum(r["agree"] for r in pr) / len(pr)
        out["strata"][name] = {"norm": f"{sum(r['agree'] for r in n)}/{len(n)}",
                               "preference": f"{sum(r['agree'] for r in pr)}/{len(pr)}",
                               "rate_norm": round(rn, 3), "rate_pref": round(rp, 3),
                               "delta": round(rn - rp, 3)}
        diffs.append(rn - rp); weights.append(len(st))
    if diffs:
        strat = sum(d * w for d, w in zip(diffs, weights)) / sum(weights)
        out["stratified_delta"] = round(strat, 3)
        rng = random.Random(0); ge = 0
        strata = [[r for r in rows if r["det"] <= cut], [r for r in rows if r["det"] > cut]]
        for _ in range(10000):
            tot, wsum = 0.0, 0
            for st in strata:
                labs = [r["layer"] for r in st]; rng.shuffle(labs)
                n = [r for r, l in zip(st, labs) if l == "norm"]
                pr = [r for r, l in zip(st, labs) if l == "preference"]
                if not n or not pr:
                    continue
                tot += (sum(r["agree"] for r in n) / len(n) - sum(r["agree"] for r in pr) / len(pr)) * len(st)
                wsum += len(st)
            if wsum and tot / wsum >= strat - 1e-12:
                ge += 1
        out["stratified_permutation_p_one_sided"] = round((ge + 1) / 10001, 4)
    json.dump(out, open(HERE / "results_matched_exploratory.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

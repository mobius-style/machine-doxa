#!/usr/bin/env python3
"""EXPLORATORY, not pre-registered. Written 2026-09-21T04:05+09:00 in response to
a reviewer who pointed out that the extension's per-model tests treat five
measurements of the same 81 items as if they were five samples, and that a
non-significant result was being reported as absence of an effect.

The items are common to all five pre-trained models, so the appropriate test
averages determinacy across models per item and asks once whether the 30
habitus items on which the seven subjects agree are more determinate than the
51 on which they do not. Effect size is reported alongside the p-value, and the
result is read as an estimate, not as a presence or absence of an effect.
"""
import json, glob
from collections import Counter
from math import erf, sqrt
from pathlib import Path
from statistics import mean

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


def mannwhitney(a, b):
    n1, n2 = len(a), len(b)
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks, i = [0.0] * len(allv), 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    r1 = sum(rk for rk, (_, g) in zip(ranks, allv) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    counts = Counter(v for v, _ in allv)
    n = n1 + n2
    tie = sum(c ** 3 - c for c in counts.values())
    sd = sqrt(n1 * n2 / 12 * ((n + 1) - tie / (n * (n - 1))))
    z = (u1 - mu) / sd if sd else 0.0
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    # rank-biserial correlation: probability of superiority, rescaled
    rb = 2 * u1 / (n1 * n2) - 1
    return round(u1, 1), round(p, 4), round(rb, 3), round(u1 / (n1 * n2), 3)


def main():
    bat = {it["id"]: it for it in json.load(open(BASE / "battery_doxa.json"))["items"]}
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

    hab = [i for i in bat if bat[i].get("layer", "habitus") == "habitus"]
    verd = {i: [modal(m, i) for m in by] for i in hab}
    valid = [i for i in hab if "NR" not in verd[i]]
    cons = [i for i in valid if len(set(verd[i])) == 1]
    non = [i for i in valid if i not in cons]

    det = {}
    for tag in BASES:
        p = HERE / f"{tag}_habitus.json"
        if not p.exists():
            continue
        for r in json.load(open(p))["items"]:
            d = determinacy(r)
            if d is not None:
                det.setdefault(r["id"], []).append(d)
    dc = [mean(det[i]) for i in cons if i in det]
    dn = [mean(det[i]) for i in non if i in det]
    u, pv, rb, pos = mannwhitney(dc, dn)
    out = {"note": "exploratory; determinacy averaged over the five pre-trained models per item",
           "n_consensus": len(dc), "n_nonconsensus": len(dn),
           "mean_determinacy_consensus": round(mean(dc), 3),
           "mean_determinacy_nonconsensus": round(mean(dn), 3),
           "difference": round(mean(dc) - mean(dn), 3),
           "mannwhitney_u": u, "p_two_sided": pv,
           "rank_biserial": rb, "probability_of_superiority": pos}
    json.dump(out, open(HERE / "results_pooled_exploratory.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

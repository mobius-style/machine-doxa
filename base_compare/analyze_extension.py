#!/usr/bin/env python3
"""Extension analysis (EXTENSION.md): is subject consensus reducible to
pre-trained determinacy? Frozen readings are in EXTENSION.md."""
import json, glob
from collections import Counter
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent
BASE = HERE.parent
L = ["A", "B", "C", "D"]
BASES = ["gemma4_12b_base", "gemma4_26b_base", "granite4_small_base", "ling_mini_base", "llama31_8b_base"]


def determinacy(rec):
    out = []
    for rot in rec["rotations"]:
        pr = rot.get("probs") or {}
        tot = sum(pr.get(x, 0.0) for x in L)
        if tot > 0:
            out.append(max(pr.get(x, 0.0) for x in L) / tot)
    return mean(out) if out else None


def mannwhitney(a, b):
    """Two-sided Mann-Whitney U with normal approximation and tie correction."""
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return None, None
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
    sd = (n1 * n2 / 12 * ((n + 1) - tie / (n * (n - 1)))) ** 0.5
    if sd == 0:
        return round(u1, 1), 1.0
    import math
    z = (u1 - mu) / sd
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / 2 ** 0.5)))
    return round(u1, 1), round(p, 4)


def subject_verdicts():
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
    hab = [i for i in bat if bat[i].get("layer", "habitus") == "habitus"]
    by, modal = subject_verdicts()
    verdicts = {i: {m: modal(m, i) for m in by} for i in hab}
    valid = [i for i in hab if all(v != "NR" for v in verdicts[i].values())]
    consensus = [i for i in valid if len(set(verdicts[i].values())) == 1]
    noncons = [i for i in valid if i not in consensus]
    res = {"n_valid_habitus": len(valid), "n_consensus": len(consensus),
           "n_nonconsensus": len(noncons), "per_base_model": {}}
    for tag in BASES:
        p = HERE / f"{tag}_habitus.json"
        pn = HERE / f"{tag}.json"
        if not p.exists():
            continue
        h = {r["id"]: r for r in json.load(open(p))["items"]}
        dc = [d for i in consensus if i in h and (d := determinacy(h[i])) is not None]
        dn = [d for i in noncons if i in h and (d := determinacy(h[i])) is not None]
        u, pv = mannwhitney(dc, dn)
        row = {"determinacy_consensus_items": round(mean(dc), 3) if dc else None,
               "determinacy_nonconsensus_items": round(mean(dn), 3) if dn else None,
               "difference": round(mean(dc) - mean(dn), 3) if dc and dn else None,
               "mannwhitney_u": u, "p_two_sided": pv,
               "n_consensus_scored": len(dc), "n_nonconsensus_scored": len(dn)}
        if pn.exists():
            nrm = {r["id"]: r for r in json.load(open(pn))["items"]}
            dnorm = [d for i in bat if bat[i].get("layer") == "norm" and i in nrm
                     and (d := determinacy(nrm[i])) is not None]
            dpref = [d for i in bat if bat[i].get("layer") == "preference" and i in nrm
                     and (d := determinacy(nrm[i])) is not None]
            dall = [d for i in h if (d := determinacy(h[i])) is not None]
            un, pn2 = mannwhitney(dnorm, dall)
            row.update({"determinacy_norm_layer": round(mean(dnorm), 3),
                        "determinacy_preference_layer": round(mean(dpref), 3),
                        "determinacy_habitus_layer": round(mean(dall), 3),
                        "norm_vs_habitus_p": pn2})
        res["per_base_model"][tag] = row
    json.dump(res, open(HERE / "results_extension.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

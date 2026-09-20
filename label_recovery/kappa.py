#!/usr/bin/env python3
"""Cohen's kappa of each coder's blind labels vs the frozen labels; norm_option recovery; majority vote."""
import json, glob, itertools
from collections import Counter
B = "/home/happy/.codex/projects/machine_doxa"
items = {it["id"]: it for it in json.load(open(f"{B}/battery_doxa.json"))["items"] if 201 <= int(it["id"]) <= 330}
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b); pe = sum((a.count(c)/n) * (b.count(c)/n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
gold = {i: it["layer"] for i, it in items.items()}
out = {}; per_coder = {}
for fp in sorted(glob.glob(f"{B}/label_recovery/*.json")):
    if "timeline" in fp or "kappa" in fp: continue
    d = json.load(open(fp)); lab = {x["id"]: x["label"] for x in d["items"]}; no = {x["id"]: x["norm_option"] for x in d["items"]}
    ids = sorted(items); a = [gold[i] for i in ids]; b = [lab[i] for i in ids]
    unparsed = sum(1 for i in ids if lab[i] == "unparsed")
    norm_ids = [i for i in ids if gold[i] == "norm"]
    rec = sum(1 for i in norm_ids if lab[i] == "norm" and no[i] == items[i]["norm_option"])
    rec_given_norm = sum(1 for i in norm_ids if lab[i] == "norm"); 
    out[d["model"]] = {"kappa_vs_frozen": round(kappa(a, b), 3), "agreement": f"{sum(x==y for x,y in zip(a,b))}/{len(ids)}",
                       "unparsed": unparsed, "norm_option_exact_given_norm": f"{rec}/{rec_given_norm}",
                       "confusion": {f"{x}->{y}": c for (x, y), c in Counter(zip(a, b)).items()}}
    per_coder[d["model"]] = lab
if len(per_coder) >= 2:
    ids = sorted(items)
    maj = {i: Counter(per_coder[m][i] for m in per_coder).most_common(1)[0][0] for i in ids}
    out["majority_vote"] = {"kappa_vs_frozen": round(kappa([gold[i] for i in ids], [maj[i] for i in ids]), 3), "n_coders": len(per_coder)}
    pairs = {f"{m1}|{m2}": round(kappa([per_coder[m1][i] for i in ids], [per_coder[m2][i] for i in ids]), 3) for m1, m2 in itertools.combinations(per_coder, 2)}
    out["inter_coder_kappa"] = pairs
json.dump(out, open(f"{B}/label_recovery/kappa_results.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))

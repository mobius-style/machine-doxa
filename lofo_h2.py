#!/usr/bin/env python3
"""Leave-one-family-out re-analysis of H2 (exploratory; added 2026-09-20).
Frozen definitions from analyze_doxa.py: per-model verdict = modal answer over
its sessions (tie or all-NR -> NR); agreement over items where every remaining
subject is non-NR; item-label permutation test, 10,000 draws, one-sided, seed 0.
Writes lofo_h2.json."""
import json, glob, random
from collections import Counter, defaultdict

BASE = "/home/happy/.codex/projects/machine_doxa"
items = json.load(open(f"{BASE}/battery_doxa.json"))["items"]
layer = {it["id"]: it.get("layer", "habitus") for it in items}
norm_opt = {it["id"]: it.get("norm_option") for it in items}
by = defaultdict(list)
for f in sorted(glob.glob(f"{BASE}/responses/*.json")):
    s = json.load(open(f)); by[s["model"]].append(s)
FAMILY = {"claude-haiku": "anthropic", "claude-sonnet": "anthropic", "deepseek-v4": "deepseek",
          "gemma4-12b": "google", "gemma4-26b": "google", "gpt-oss-120b": "openai", "qwen3.6-27b": "alibaba"}

def modal(m, i):
    v = [s["answers"].get(str(i), "NR") for s in by[m]]
    v = [x for x in v if x != "NR"]
    if not v: return "NR"
    c = Counter(v).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]: return "NR"
    return c[0][0]

def h2(subset, n_perm=10000, seed=0):
    ids = [i for i in layer if layer[i] in ("norm", "preference")]
    verdict = {i: {m: modal(m, i) for m in subset} for i in ids}
    valid = [i for i in ids if all(verdict[i][m] != "NR" for m in subset)]
    agree = {i: len(set(verdict[i].values())) == 1 for i in valid}
    labs = {i: layer[i] for i in valid}
    def rates(labs):
        n = [i for i in valid if labs[i] == "norm"]; p = [i for i in valid if labs[i] == "preference"]
        rn = sum(agree[i] for i in n) / len(n); rp = sum(agree[i] for i in p) / len(p)
        return rn, rp, len(n), len(p), sum(agree[i] for i in n), sum(agree[i] for i in p)
    rn, rp, nn, np_, an, ap = rates(labs); delta = rn - rp
    rng = random.Random(seed); vals = [labs[i] for i in valid]; ge = 0
    for _ in range(n_perm):
        rng.shuffle(vals); sh = dict(zip(valid, vals))
        r = rates(sh)
        if r[0] - r[1] >= delta - 1e-12: ge += 1
    winners = [i for i in valid if labs[i] == "norm" and agree[i]]
    win_norm = sum(1 for i in winners if next(iter(verdict[i].values())) == norm_opt[i])
    return {"subset": sorted(subset), "norm": f"{an}/{nn}", "pref": f"{ap}/{np_}",
            "rate_norm": round(rn, 3), "rate_pref": round(rp, 3), "delta": round(delta, 3),
            "perm_p": round((ge + 1) / (n_perm + 1), 4), "winner_is_norm_option": f"{win_norm}/{len(winners)}"}

if __name__ == "__main__":
    models = sorted(by); out = {"full": h2(models)}
    for fam in sorted(set(FAMILY.values())):
        out[f"drop_{fam}"] = h2([m for m in models if FAMILY[m] != fam])
    json.dump(out, open(f"{BASE}/lofo_h2.json", "w"), indent=1, ensure_ascii=False)
    for k, v in out.items(): print(k, v["norm"], v["pref"], v["delta"], v["perm_p"], v["winner_is_norm_option"])

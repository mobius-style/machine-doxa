#!/usr/bin/env python3
"""Machine Doxa Part B 確証的分析(凍結対象)。
H1 分化優勢: 180項目の全7モデルmodal一致率 < 独立性null(プール周辺分布シミュレーション10,000、片側下側)
H2 規範勾配: norm30の一致率 > preference30(項目ラベルpermutation 10,000、片側)
H3 doxa再現: 旧120項目の新分類 vs Part-A分類(37 doxa)の一致 κ > 0(項目permutation 10,000、片側)
Holm 3検定。modal = 3セッションの多数(タイ・全NR→NR)。全モデルmodal非NRの項目のみ一致判定に算入(算入数を報告)。
"""
import json, glob, itertools, random
import numpy as np
from collections import Counter, defaultdict

BASE = "/home/happy/.codex/projects/machine_doxa"
battery = json.load(open(f"{BASE}/battery_doxa.json"))
items = battery["items"]
ids = [it["id"] for it in items]
layer = {it["id"]: it.get("layer", "habitus") for it in items}
sessions = [json.load(open(f)) for f in sorted(glob.glob(f"{BASE}/responses/*.json"))]
by = defaultdict(list)
for s in sessions: by[s["model"]].append(s)
models = sorted(by)
assert len(models) == 7, models

def modal(m, i):
    v = [s["answers"].get(str(i), s["answers"].get(i, "NR")) for s in by[m]]
    v = [x for x in v if x != "NR"]
    if not v: return "NR"
    c = Counter(v).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]: return "NR"  # タイ→NR(凍結規則)
    return c[0][0]

modals = {m: {i: modal(m, i) for i in ids} for m in models}
valid = [i for i in ids if all(modals[m][i] != "NR" for m in models)]
agree = {i: len({modals[m][i] for m in models}) == 1 for i in valid}
rate = sum(agree.values()) / len(valid)
print(f"valid items: {len(valid)}/{len(ids)}; all-7 agreement: {sum(agree.values())} ({rate:.3f})")

results = {"n_valid": len(valid), "n_agree": int(sum(agree.values())), "rate": rate}

# H1: 独立性null
rng = np.random.default_rng(0)
def sim_count():
    cnt = 0
    for i in valid:
        pool = [s["answers"].get(str(i), "NR") for s in sessions]
        pool = [x for x in pool if x != "NR"]
        cats = sorted(set(pool)); p = np.array([pool.count(c) for c in cats], float); p /= p.sum()
        mods = set()
        ok = True
        for _ in range(7):
            draw = rng.multinomial(3, p)
            mx = draw.max()
            winners = [cats[k] for k in range(len(cats)) if draw[k] == mx]
            if len(winners) > 1: ok = False; break
            mods.add(winners[0])
        if ok and len(mods) == 1: cnt += 1
    return cnt
null = np.array([sim_count() for _ in range(10000 // 10)])  # 1000反復(計算量対策、凍結値)
p1 = (np.sum(null <= sum(agree.values())) + 1) / (len(null) + 1)
results["H1"] = {"observed": int(sum(agree.values())), "null_mean": float(null.mean()),
                 "null_ci95": [float(np.percentile(null, 2.5)), float(np.percentile(null, 97.5))],
                 "p_lower": float(p1)}
print("H1:", results["H1"])

# H2: norm vs preference
nv = [i for i in valid if layer[i] == "norm"]; pv = [i for i in valid if layer[i] == "preference"]
rn = np.mean([agree[i] for i in nv]); rp = np.mean([agree[i] for i in pv])
obs = rn - rp
lab = [layer[i] for i in nv + pv]; vals = [agree[i] for i in nv + pv]
r2 = np.random.default_rng(1)
nul2 = []
for _ in range(10000):
    perm = r2.permutation(lab)
    a = np.mean([v for v, l in zip(vals, perm) if l == "norm"])
    b = np.mean([v for v, l in zip(vals, perm) if l == "preference"])
    nul2.append(a - b)
p2 = (np.sum(np.array(nul2) >= obs) + 1) / 10001
results["H2"] = {"rate_norm": float(rn), "n_norm": len(nv), "rate_pref": float(rp), "n_pref": len(pv),
                 "diff": float(obs), "p_perm": float(p2)}
print("H2:", results["H2"])

# H3: 旧120項目でのdoxa分類 vs Part-A
partA = set(x["id"] for x in json.load(open(f"{BASE}/partA_doxa.json"))["doxa_items"])
old_valid = [i for i in valid if layer[i] == "habitus"]
new_doxa = {i for i in old_valid if agree[i]}
a = [(i in partA) for i in old_valid]; b = [(i in new_doxa) for i in old_valid]
def kappa(a, b):
    a = np.array(a); b = np.array(b)
    po = np.mean(a == b)
    pe = a.mean()*b.mean() + (1-a.mean())*(1-b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else 0.0
k = kappa(a, b)
r3 = np.random.default_rng(2)
nul3 = [kappa(a, r3.permutation(b)) for _ in range(10000)]
p3 = (np.sum(np.array(nul3) >= k) + 1) / 10001
results["H3"] = {"kappa": float(k), "partA_size": len(partA & set(old_valid)), "new_size": len(new_doxa),
                 "overlap": len(partA & new_doxa), "n_old_valid": len(old_valid), "p_perm": float(p3)}
print("H3:", results["H3"])

# Holm(単調性つき)
ps = {"H1": results["H1"]["p_lower"], "H2": results["H2"]["p_perm"], "H3": results["H3"]["p_perm"]}
order = sorted(ps, key=lambda x: ps[x]); run = 0; holm = {}
for r, kk in enumerate(order):
    run = max(run, ps[kk] * (3 - r)); holm[kk] = min(1.0, run)
results["holm"] = holm
print("Holm:", {k2: round(v, 5) for k2, v in holm.items()})
results["per_session_nr"] = {f"{s['model']}_s{s['session']}": s["nr_count"] for s in sessions}
results["agree_by_layer_domain"] = {lay: {"agree": int(sum(agree[i] for i in valid if layer[i]==lay)),
                                          "n": sum(1 for i in valid if layer[i]==lay)} for lay in set(layer.values())}
json.dump(results, open(f"{BASE}/results_doxa.json", "w"), ensure_ascii=False, indent=1)
print("saved results_doxa.json")

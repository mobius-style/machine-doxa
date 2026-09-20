#!/usr/bin/env python3
"""Controls demanded by pre-submission review, all on the frozen Study B data.

C1 same-weights format reliability: the tuned model under its chat template vs
   the same tuned model under the raw prompt, per layer. Bounds how much of the
   base/tuned divergence is instrument noise rather than tuning.
C2 generic sharpening: mass on the designated option vs mass on the model's own
   top option. Tuning sharpens everything; the question is whether it sharpens
   the designated option more than the peak.
C3 length confound: is the designated option simply the longest?
"""
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent
BASE = HERE.parent
L = ["A", "B", "C", "D"]
PAIRS = [("G", "gemma4_12b_base", "gemma4_12b_it"), ("A", "gemma4_26b_base", "gemma4_26b_it"),
         ("I", "granite4_small_base", "granite4_small_it"), ("N", "ling_mini_base", "ling_mini_it"),
         ("L", "llama31_8b_base", "llama31_8b_it")]


def load(tag):
    p = HERE / f"{tag}.json"
    return {r["id"]: r for r in json.load(open(p))["items"]} if p.exists() else None


def mass_on(rec, option):
    c = L.index(option); out = []
    for rot in rec["rotations"]:
        pr = rot.get("probs") or {}
        tot = sum(pr.get(x, 0.0) for x in L)
        if tot > 0:
            out.append(pr.get(L[(c - rot["rotation"]) % 4], 0.0) / tot)
    return mean(out) if out else None


def peak_mass(rec):
    out = []
    for rot in rec["rotations"]:
        pr = rot.get("probs") or {}
        tot = sum(pr.get(x, 0.0) for x in L)
        if tot > 0:
            out.append(max(pr.get(x, 0.0) for x in L) / tot)
    return mean(out) if out else None


def main():
    bat = {it["id"]: it for it in json.load(open(BASE / "battery_doxa.json"))["items"]}
    res = {"C1_format_reliability": {}, "C2_generic_sharpening": {}, "C3_length": {}}

    for label, bt, tt in PAIRS:
        b, t, tc = load(bt), load(tt), load(tt + "_chat")
        if not (b and t):
            continue
        # C1
        if tc:
            for layer in ("norm", "preference"):
                ids = [i for i in bat if bat[i].get("layer") == layer and i in t and i in tc
                       and t[i]["verdict"] != "NR" and tc[i]["verdict"] != "NR"]
                same = sum(1 for i in ids if t[i]["verdict"] == tc[i]["verdict"])
                bids = [i for i in bat if bat[i].get("layer") == layer and i in b and i in t
                        and b[i]["verdict"] != "NR" and t[i]["verdict"] != "NR"]
                bsame = sum(1 for i in bids if b[i]["verdict"] == t[i]["verdict"])
                res["C1_format_reliability"].setdefault(label, {})[layer] = {
                    "tuned_raw_vs_tuned_chat": f"{same}/{len(ids)}",
                    "tuned_raw_vs_tuned_chat_rate": round(same / len(ids), 3) if ids else None,
                    "base_vs_tuned": f"{bsame}/{len(bids)}",
                    "base_vs_tuned_rate": round(bsame / len(bids), 3) if bids else None}
        # C2
        norm_ids = [i for i in bat if bat[i].get("layer") == "norm" and i in b and i in t]
        rows = []
        for i in norm_ids:
            mb, mt = mass_on(b[i], bat[i]["norm_option"]), mass_on(t[i], bat[i]["norm_option"])
            pb, pt = peak_mass(b[i]), peak_mass(t[i])
            if None not in (mb, mt, pb, pt):
                rows.append((mb, mt, pb, pt))
        if rows:
            res["C2_generic_sharpening"][label] = {
                "n": len(rows),
                "designated_base": round(mean(r[0] for r in rows), 3),
                "designated_tuned": round(mean(r[1] for r in rows), 3),
                "peak_base": round(mean(r[2] for r in rows), 3),
                "peak_tuned": round(mean(r[3] for r in rows), 3),
                "designated_share_of_peak_base": round(mean(r[0] / r[2] for r in rows), 3),
                "designated_share_of_peak_tuned": round(mean(r[1] / r[3] for r in rows), 3)}

    # C3 length
    longest_norm = sum(1 for i in bat if bat[i].get("layer") == "norm"
                       and max(bat[i]["options"], key=lambda k: len(bat[i]["options"][k])) == bat[i]["norm_option"])
    res["C3_length"]["designated_is_longest"] = f"{longest_norm}/30"
    not_longest = [i for i in bat if bat[i].get("layer") == "norm"
                   and max(bat[i]["options"], key=lambda k: len(bat[i]["options"][k])) != bat[i]["norm_option"]]
    for label, bt, tt in PAIRS:
        b = load(bt)
        if not b:
            continue
        ids = [i for i in not_longest if i in b and b[i]["verdict"] != "NR"]
        hit = sum(1 for i in ids if b[i]["verdict"] == bat[i]["norm_option"])
        pref = [i for i in bat if bat[i].get("layer") == "preference" and i in b and b[i]["verdict"] != "NR"]
        plong = sum(1 for i in pref
                    if b[i]["verdict"] == max(bat[i]["options"], key=lambda k: len(bat[i]["options"][k])))
        res["C3_length"].setdefault("per_base_model", {})[label] = {
            "norm_items_where_designated_not_longest": f"{hit}/{len(ids)}",
            "preference_items_longest_chosen": f"{plong}/{len(pref)}",
            "preference_longest_rate": round(plong / len(pref), 3) if pref else None}
    json.dump(res, open(HERE / "results_controls.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

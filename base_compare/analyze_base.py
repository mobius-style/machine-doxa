#!/usr/bin/env python3
"""Study B analysis, frozen with PREREG.md before any model was run.

B1: exact one-sided McNemar per pair (tuned selects the frozen norm_option more
often than base), Holm-corrected across the four confirmatory pairs.
B2: agreement with the seven-subject consensus of the main study.
B3: chat-template re-scoring of the tuned models, if present.
"""
import json, glob
from collections import Counter
from math import comb
from pathlib import Path

HERE = Path(__file__).parent
BASE = HERE.parent
CONFIRMATORY = [("G", "gemma4_12b_base", "gemma4_12b_it"),
                ("A", "gemma4_26b_base", "gemma4_26b_it"),
                ("I", "granite4_small_base", "granite4_small_it"),
                ("N", "ling_mini_base", "ling_mini_it")]
SUPPLEMENTARY = [("L", "llama31_8b_base", "llama31_8b_it")]
PAIRS = CONFIRMATORY + SUPPLEMENTARY
LETTERS = ["A", "B", "C", "D"]


def load(tag):
    p = HERE / f"{tag}.json"
    if not p.exists():
        return None
    return {r["id"]: r for r in json.load(open(p))["items"]}


def mcnemar_one_sided(a, b):
    """P(X >= a) under Binomial(a+b, 0.5); a = tuned-only successes."""
    n = a + b
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(a, n + 1)) / 2 ** n


def subject_consensus():
    """Modal verdict per subject model, frozen rule; return {id: option} where all 7 agree."""
    by = {}
    for f in sorted(glob.glob(str(BASE / "responses" / "*.json"))):
        s = json.load(open(f))
        by.setdefault(s["model"], []).append(s)
    out = {}
    ids = [i for i in list(range(201, 231)) + list(range(301, 331))]
    for i in ids:
        verdicts = []
        for m, ss in by.items():
            v = [s["answers"].get(str(i), "NR") for s in ss]
            v = [x for x in v if x != "NR"]
            if not v:
                verdicts.append("NR"); continue
            c = Counter(v).most_common()
            verdicts.append("NR" if len(c) > 1 and c[0][1] == c[1][1] else c[0][0])
        if "NR" not in verdicts and len(set(verdicts)) == 1:
            out[i] = verdicts[0]
    return out


def main():
    battery = {it["id"]: it for it in json.load(open(BASE / "battery_doxa.json"))["items"]}
    consensus = subject_consensus()
    res = {"B1": {}, "B2": {}, "B3": {}, "descriptive": {}}
    pvals = []

    for label, base_tag, it_tag in PAIRS:
        b, t = load(base_tag), load(it_tag)
        if not b or not t:
            continue
        norm_ids = [i for i in b if battery[i].get("layer") == "norm"]
        usable = [i for i in norm_ids if b[i]["verdict"] != "NR" and t[i]["verdict"] != "NR"]
        bc = [i for i in usable if b[i]["verdict"] == battery[i]["norm_option"]]
        tc = [i for i in usable if t[i]["verdict"] == battery[i]["norm_option"]]
        only_t = len([i for i in usable if i in tc and i not in bc])
        only_b = len([i for i in usable if i in bc and i not in tc])
        p = mcnemar_one_sided(only_t, only_b)
        if label in [x[0] for x in CONFIRMATORY]:
            pvals.append((label, p))
        res["B1"][label] = {
            "base": base_tag, "tuned": it_tag,
            "n_norm_items_usable": len(usable),
            "nr_base": sum(1 for i in norm_ids if b[i]["verdict"] == "NR"),
            "nr_tuned": sum(1 for i in norm_ids if t[i]["verdict"] == "NR"),
            "base_norm_option_rate": f"{len(bc)}/{len(usable)}",
            "tuned_norm_option_rate": f"{len(tc)}/{len(usable)}",
            "base_rate": round(len(bc) / len(usable), 3) if usable else None,
            "tuned_rate": round(len(tc) / len(usable), 3) if usable else None,
            "discordant_tuned_only": only_t, "discordant_base_only": only_b,
            "mcnemar_exact_one_sided_p": round(p, 5),
            "role": "confirmatory" if label in [x[0] for x in CONFIRMATORY] else "supplementary (older generation, outside Holm family)",
        }
        # B2
        for layer in ("norm", "preference"):
            ids = [i for i in consensus if battery[i].get("layer") == layer
                   and b[i]["verdict"] != "NR" and t[i]["verdict"] != "NR"]
            if not ids:
                continue
            bm = sum(1 for i in ids if b[i]["verdict"] == consensus[i])
            tm = sum(1 for i in ids if t[i]["verdict"] == consensus[i])
            ot = len([i for i in ids if t[i]["verdict"] == consensus[i] and b[i]["verdict"] != consensus[i]])
            ob = len([i for i in ids if b[i]["verdict"] == consensus[i] and t[i]["verdict"] != consensus[i]])
            res["B2"].setdefault(label, {})[layer] = {
                "n": len(ids), "base_match": bm, "tuned_match": tm,
                "gap": round((tm - bm) / len(ids), 3),
                "mcnemar_exact_one_sided_p": round(mcnemar_one_sided(ot, ob), 5)}
        # descriptive: preference-layer behaviour
        pref_ids = [i for i in b if battery[i].get("layer") == "preference"
                    and b[i]["verdict"] != "NR" and t[i]["verdict"] != "NR"]
        res["descriptive"].setdefault(label, {})["preference_base_tuned_same"] = \
            f"{sum(1 for i in pref_ids if b[i]['verdict'] == t[i]['verdict'])}/{len(pref_ids)}"
        norm_same = [i for i in usable if b[i]["verdict"] == t[i]["verdict"]]
        res["descriptive"][label]["norm_base_tuned_same"] = f"{len(norm_same)}/{len(usable)}"
        # B3
        tc_chat = load(it_tag + "_chat")
        if tc_chat:
            ids = [i for i in usable if tc_chat.get(i, {}).get("verdict", "NR") != "NR"]
            hit = sum(1 for i in ids if tc_chat[i]["verdict"] == battery[i]["norm_option"])
            ot = len([i for i in ids if tc_chat[i]["verdict"] == battery[i]["norm_option"]
                      and b[i]["verdict"] != battery[i]["norm_option"]])
            ob = len([i for i in ids if b[i]["verdict"] == battery[i]["norm_option"]
                      and tc_chat[i]["verdict"] != battery[i]["norm_option"]])
            res["B3"][label] = {"n": len(ids), "tuned_chat_norm_option_rate": f"{hit}/{len(ids)}",
                                "mcnemar_vs_base_p": round(mcnemar_one_sided(ot, ob), 5)}

    # Holm across the confirmatory B1 tests
    order = sorted(pvals, key=lambda x: x[1])
    holm, prev = {}, 0.0
    for k, (label, p) in enumerate(order):
        adj = max(prev, min(1.0, p * (len(order) - k)))
        holm[label] = round(adj, 5); prev = adj
    res["B1_holm"] = holm
    res["subject_consensus_items"] = {"norm": sum(1 for i in consensus if battery[i].get("layer") == "norm"),
                                      "preference": sum(1 for i in consensus if battery[i].get("layer") == "preference")}
    json.dump(res, open(HERE / "results_base.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

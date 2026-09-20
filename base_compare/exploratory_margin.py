#!/usr/bin/env python3
"""EXPLORATORY, not pre-registered. Written 2026-09-21T01:25+09:00, after the
pair-G confirmatory result was seen and before pairs A, I and N had been scored.

Why it exists: pair G's base model already selects the designated norm option on
22 of 23 usable items, so the pre-registered argmax test has almost no room to
detect an increase from tuning. Probability mass has no ceiling, so this script
asks a softer question on the same frozen data: how much of the four-letter
probability mass does each model put on the designated norm option, and does
tuning move it?

Reported as exploratory whatever it shows. It cannot rescue B1; it can only
describe the direction of a difference the confirmatory test could not resolve.
"""
import json, random
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent
BASE = HERE.parent
LETTERS = ["A", "B", "C", "D"]
PAIRS = [("G", "gemma4_12b_base", "gemma4_12b_it"),
         ("A", "gemma4_26b_base", "gemma4_26b_it"),
         ("I", "granite4_small_base", "granite4_small_it"),
         ("N", "ling_mini_base", "ling_mini_it"),
         ("L", "llama31_8b_base", "llama31_8b_it")]


def load(tag):
    p = HERE / f"{tag}.json"
    return {r["id"]: r for r in json.load(open(p))["items"]} if p.exists() else None


def norm_mass(rec, norm_option):
    """Mean share of the four-letter probability mass on the designated option."""
    c = LETTERS.index(norm_option)
    shares = []
    for rot in rec["rotations"]:
        probs = rot.get("probs") or {}
        total = sum(probs.get(L, 0.0) for L in LETTERS)
        if total <= 0:
            continue
        shown = LETTERS[(c - rot["rotation"]) % 4]
        shares.append(probs.get(shown, 0.0) / total)
    return mean(shares) if shares else None


def perm_p(diffs, n=10000, seed=0):
    """One-sided sign-flip permutation test, H1: mean(diff) > 0."""
    obs = mean(diffs)
    rng = random.Random(seed)
    ge = sum(1 for _ in range(n)
             if mean(d if rng.random() < 0.5 else -d for d in diffs) >= obs)
    return (ge + 1) / (n + 1)


def main():
    battery = {it["id"]: it for it in json.load(open(BASE / "battery_doxa.json"))["items"]}
    out = {}
    for label, bt, tt in PAIRS:
        b, t = load(bt), load(tt)
        if not b or not t:
            continue
        rows = []
        for i, it in battery.items():
            if it.get("layer") != "norm" or i not in b or i not in t:
                continue
            mb, mt = norm_mass(b[i], it["norm_option"]), norm_mass(t[i], it["norm_option"])
            if mb is None or mt is None:
                continue
            rows.append((i, mb, mt))
        if not rows:
            continue
        diffs = [mt - mb for _, mb, mt in rows]
        out[label] = {
            "n_items": len(rows),
            "base_mean_mass_on_norm_option": round(mean(m for _, m, _ in rows), 3),
            "tuned_mean_mass_on_norm_option": round(mean(m for _, _, m in rows), 3),
            "mean_difference": round(mean(diffs), 3),
            "items_where_tuned_higher": sum(1 for d in diffs if d > 0),
            "permutation_p_one_sided": round(perm_p(diffs), 4),
        }
    json.dump(out, open(HERE / "results_margin_exploratory.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

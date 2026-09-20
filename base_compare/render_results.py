#!/usr/bin/env python3
"""Render results_base.json into the manuscript table and a one-paragraph reading."""
import json
from pathlib import Path

HERE = Path(__file__).parent
NAME = {"G": "gemma-4-12B", "A": "gemma-4-26B-A4B", "I": "granite-4.0-h-small",
        "N": "Ling-mini-2.0", "L": "Llama-3.1-8B (older generation)"}
VENDOR = {"G": "Google", "A": "Google", "I": "IBM", "N": "inclusionAI", "L": "Meta"}
r = json.load(open(HERE / "results_base.json"))
holm = r.get("B1_holm", {})
rows = ["| pair (vendor) | base selects norm option | tuned selects norm option | discordant t/b | exact p | Holm p |",
        "|---|---:|---:|---:|---:|---:|"]
for k, v in r["B1"].items():
    h = holm.get(k)
    rows.append(f"| {NAME[k]} ({VENDOR[k]}) | {v['base_norm_option_rate']} = {v['base_rate']:.2f} | "
                f"{v['tuned_norm_option_rate']} = {v['tuned_rate']:.2f} | "
                f"{v['discordant_tuned_only']}/{v['discordant_base_only']} | "
                f"{v['mcnemar_exact_one_sided_p']:.4f} | {f'{h:.4f}' if h is not None else 'n/a (supplementary)'} |")
print("\n".join(rows))
print("\nNR counts (norm items):")
for k, v in r["B1"].items():
    print(f"  {NAME[k]}: base {v['nr_base']}, tuned {v['nr_tuned']}, usable {v['n_norm_items_usable']}")
print("\nB2 (agreement with the seven-subject consensus):")
print(json.dumps(r.get("B2", {}), ensure_ascii=False, indent=1))
print("\nB3 (chat template):")
print(json.dumps(r.get("B3", {}), ensure_ascii=False, indent=1))
print("\nDescriptive:")
print(json.dumps(r.get("descriptive", {}), ensure_ascii=False, indent=1))
for f in sorted(HERE.glob("calibration_*.json")):
    if f.name == "calibration_items.json":
        continue
    d = json.load(open(f))
    print(f"calibration {d['tag']}: {d['correct']}/{d['n']} {d['verdict_distribution']}")

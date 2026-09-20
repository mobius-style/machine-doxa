#!/usr/bin/env python3
"""Instrument check: run the Study B scorer on factual items with known answers."""
import argparse, json
from collections import Counter
from pathlib import Path
import score_base as S

HERE = Path(__file__).parent
L = ["A", "B", "C", "D"]

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--tag", required=True)
ap.add_argument("--gpu", default="0"); ap.add_argument("--split", action="store_true")
a = ap.parse_args()
cal = json.load(open(HERE / "calibration_items.json"))["items"]
proc = S.start_server(a.model, a.gpu, split=a.split)
rows, ok = [], 0
try:
    for it in cal:
        opts = [it["options"][x] for x in L]; picks = []
        for r in range(4):
            shown = [opts[(i + r) % 4] for i in range(4)]
            probs, _ = S.letter_probs(S.PROMPT.format(text=it["text"], a=shown[0], b=shown[1],
                                                      c=shown[2], d=shown[3]))
            picks.append(L[(L.index(max(probs, key=probs.get)) + r) % 4] if probs else None)
        v = [x for x in picks if x]; c = Counter(v).most_common()
        verdict = "NR" if not v or (len(c) > 1 and c[0][1] == c[1][1]) else c[0][0]
        ok += verdict == it["gold"]
        rows.append({"text": it["text"], "gold": it["gold"], "verdict": verdict, "rotations": picks})
finally:
    proc.terminate()
    try: proc.wait(timeout=30)
    except Exception: proc.kill()
json.dump({"tag": a.tag, "correct": ok, "n": len(cal),
           "verdict_distribution": dict(Counter(r["verdict"] for r in rows)), "rows": rows},
          open(HERE / f"calibration_{a.tag}.json", "w"), ensure_ascii=False, indent=1)
print(f"CALIBRATION {a.tag}: {ok}/{len(cal)}")

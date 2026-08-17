#!/usr/bin/env python3
"""Claude系被験体のブロック回答を responses/ 形式に組み立てる(doxa版、4ブロック)。"""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
battery = json.load(open(f"{BASE}/battery_doxa.json"))
ids = [it["id"] for it in battery["items"]]

for mkey in ("claude-haiku", "claude-sonnet"):
    for s in range(1, 4):
        out = f"{BASE}/responses/{mkey}__s{s}.json"
        if os.path.exists(out): continue
        blocks = [f"{BASE}/claude_prompts/answers/{mkey}_s{s}_b{b}.txt" for b in (1, 2, 3, 4)]
        if not all(os.path.exists(b) for b in blocks): print(f"missing {mkey} s{s}"); continue
        mapping = json.load(open(f"{BASE}/claude_prompts/{mkey}_s{s}_map.json"))
        raws = [open(b).read() for b in blocks]
        ans = {}
        for raw in raws:
            for m in re.finditer(r"(?:項目ID\s*)?(\d+)\)?\s*[:：)．.]\s*([A-Da-d])", raw):
                iid, letter = m.group(1), m.group(2).upper()
                if iid in mapping and iid not in ans:
                    ans[iid] = mapping[iid].get(letter, "NR")
        full = {str(i): ans.get(str(i), "NR") for i in ids}
        nr = sum(1 for v in full.values() if v == "NR")
        json.dump({"model": mkey, "session": s, "answers": full, "nr_count": nr,
                   "raw_blocks": raws, "mapping": mapping}, open(out, "w"), ensure_ascii=False, indent=1)
        print(f"assembled {mkey} s{s} NR={nr}")

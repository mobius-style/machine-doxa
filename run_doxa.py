#!/usr/bin/env python3
"""Machine Doxa Part B 採取ランナー(凍結対象)。
- battery_doxa.json (180項目 = habitus旧120 + norm30 + pref30) を4ブロック×45で提示。
- セッション = シード sha256(doxa|model|s{n}) の決定的シャッフル、ブロック間文脈なし。
- 7モデル×3セッション。ollama: think:false num_ctx:8192 / groq: reasoning_effort low / deepseek: 既定。
- **ブロック非空検証**(habitus研究の教訓の凍結前実装): ブロックのパース成功が50%未満なら同一プロンプトで1回だけ再呼び出し、両方の結果のうち良い方を採用。再試行はログに記録。
"""
import json, hashlib, random, os, sys, re, time
sys.path.insert(0, "/home/happy/.codex/projects/machine_habitus")
from run_main import call, MODELS  # 凍結済みバックエンドを再利用

BASE = os.path.dirname(os.path.abspath(__file__))
BATTERY = json.load(open(f"{BASE}/battery_doxa.json"))
OUT = f"{BASE}/responses"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{BASE}/claude_prompts", exist_ok=True)
VER = "doxa-v1.0"
NBLOCK = 4
SESSIONS = 3
INSTR = BATTERY["instruction"]

def blocks_for(model_key, session):
    seed = int(hashlib.sha256(f"doxa|{model_key}|s{session}|{VER}".encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(seed)
    items = BATTERY["items"][:]
    rng.shuffle(items)
    mapping, prompts, block_ids = {}, [], []
    per = len(items) // NBLOCK
    for b in range(NBLOCK):
        chunk = items[b*per:(b+1)*per] if b < NBLOCK-1 else items[(NBLOCK-1)*per:]
        lines = []
        bids = []
        for pos, it in enumerate(chunk, 1):
            keys = list(it["options"].keys()); rng.shuffle(keys)
            m = {}
            opt = []
            for i2, orig in enumerate(keys):
                new = "ABCD"[i2]; m[new] = orig
                opt.append(f"  {new}) {it['options'][orig]}")
            mapping[it["id"]] = m
            bids.append(it["id"])
            lines.append(f"問{pos} (項目ID {it['id']}): {it['text']}\n" + "\n".join(opt))
        prompts.append(INSTR + f"\n回答形式: 「項目ID: 文字」を全{len(chunk)}行。\n\n" + "\n\n".join(lines))
        block_ids.append(bids)
    return prompts, mapping, block_ids

def parse_block(raw, mapping, bids):
    ans = {}
    for m in re.finditer(r"(?:項目ID\s*)?(\d+)\)?\s*[:：)．.]\s*([A-Da-d])", raw or ""):
        iid, letter = int(m.group(1)), m.group(2).upper()
        if iid in bids and iid in mapping and iid not in ans:
            ans[iid] = mapping[iid].get(letter, "NR")
    return ans

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == "claude-prompts":
        for mkey in ("claude-haiku", "claude-sonnet"):
            for s in range(1, SESSIONS + 1):
                prompts, mapping, _ = blocks_for(mkey, s)
                for b, p in enumerate(prompts, 1):
                    open(f"{BASE}/claude_prompts/{mkey}_s{s}_b{b}.txt", "w").write(p)
                json.dump({str(k): v for k, v in mapping.items()}, open(f"{BASE}/claude_prompts/{mkey}_s{s}_map.json", "w"))
        print("claude prompts written"); return
    for mkey, cfg in MODELS.items():
        if arg and mkey != arg: continue
        for s in range(1, SESSIONS + 1):
            out = f"{OUT}/{mkey}__s{s}.json"
            if os.path.exists(out): print(f"skip {out}"); continue
            prompts, mapping, block_ids = blocks_for(mkey, s)
            t0 = time.time(); raws = []; retries = 0
            ans = {}
            try:
                for p, bids in zip(prompts, block_ids):
                    raw = call(cfg, p)
                    got = parse_block(raw, mapping, bids)
                    if len(got) < len(bids) * 0.5:  # 非空検証: 再試行1回
                        raw2 = call(cfg, p)
                        got2 = parse_block(raw2, mapping, bids)
                        retries += 1
                        if len(got2) > len(got): raw, got = raw2, got2
                    raws.append(raw); ans.update(got)
            except Exception as e:
                print(f"ERROR {mkey} s{s}: {e}"); continue
            full = {it["id"]: ans.get(it["id"], "NR") for it in BATTERY["items"]}
            nr = sum(1 for v in full.values() if v == "NR")
            json.dump({"model": mkey, "session": s, "answers": full, "nr_count": nr, "block_retries": retries,
                       "elapsed_s": round(time.time()-t0, 1), "raw_blocks": raws,
                       "mapping": {str(k): v for k, v in mapping.items()}}, open(out, "w"), ensure_ascii=False, indent=1)
            print(f"done {mkey} s{s}: NR={nr} retries={retries} ({round(time.time()-t0,1)}s)", flush=True)

if __name__ == "__main__":
    main()

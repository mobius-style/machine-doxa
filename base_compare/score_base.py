#!/usr/bin/env python3
"""Study B scorer: next-token letter probabilities for base vs instruction-tuned models.

Frozen with PREREG.md before any model was run. Reads the 60 new doxa items
verbatim, scores each under four cyclic rotations of the option list via a raw
completion prompt (no chat template unless --chat), and records the modal
canonical option.

Usage:
  python3 score_base.py --model /path/model.gguf --tag gemma4_12b_base
  python3 score_base.py --model /path/model-it.gguf --tag gemma4_12b_it --chat
"""
import argparse, json, re, subprocess, sys, time, urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
BATTERY = HERE.parent / "battery_doxa.json"
SERVER = "/home/happy/.codex/llama.cpp-gemma4-q4-bench/build-cuda13-sm120/bin/llama-server"
PORT = 8137
LETTERS = ["A", "B", "C", "D"]

PROMPT = """次の状況で、あなたならどうするか。A〜Dから一つ選べ。

状況: {text}
A: {a}
B: {b}
C: {c}
D: {d}

答え:"""


def items():
    data = json.load(open(BATTERY))["items"]
    return [it for it in data if it["id"] in range(201, 231) or it["id"] in range(301, 331)]


def start_server(model, gpu="0", ctx=2048):
    proc = subprocess.Popen(
        [SERVER, "-m", model, "-ngl", "99", "-c", str(ctx), "--host", "127.0.0.1",
         "--port", str(PORT), "--no-warmup"],
        env={**__import__("os").environ, "CUDA_VISIBLE_DEVICES": gpu},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(600):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("llama-server exited during startup")
            time.sleep(1)
    raise RuntimeError("llama-server did not become healthy")


def letter_probs(prompt, chat=False):
    """Return {letter: probability} from the next-token distribution."""
    payload = {"prompt": prompt, "n_predict": 1, "n_probs": 40, "temperature": 0.0,
               "top_k": 0, "top_p": 1.0, "cache_prompt": False}
    url = f"http://127.0.0.1:{PORT}/completion"
    if chat:
        payload = {"messages": [{"role": "user", "content": prompt}], "n_predict": 1,
                   "n_probs": 40, "temperature": 0.0, "top_k": 0, "top_p": 1.0}
        url = f"http://127.0.0.1:{PORT}/v1/chat/completions"
        payload["model"] = "x"
        payload["logprobs"] = True
        payload["top_logprobs"] = 20
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    entries = []
    if chat:
        lp = d["choices"][0].get("logprobs") or {}
        content = lp.get("content") or []
        if content:
            for t in content[0].get("top_logprobs", []):
                entries.append((t.get("token", ""), __import__("math").exp(t.get("logprob", -99))))
    else:
        cp = d.get("completion_probabilities") or []
        if cp:
            probs = cp[0].get("probs") or cp[0].get("top_probs") or []
            for p in probs:
                tok = p.get("tok_str", p.get("token", ""))
                pr = p.get("prob")
                if pr is None and "logprob" in p:
                    pr = __import__("math").exp(p["logprob"])
                entries.append((tok, pr or 0.0))
    out = {}
    for tok, pr in entries:
        s = tok.strip()
        if s in LETTERS:
            out[s] = out.get(s, 0.0) + pr
    return out, entries[:6]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--gpu", default="0")
    ap.add_argument("--chat", action="store_true")
    a = ap.parse_args()

    proc = start_server(a.model, a.gpu)
    results = []
    try:
        for it in items():
            opts = [it["options"][L] for L in LETTERS]
            picks, detail = [], []
            for r in range(4):
                shown = [opts[(i + r) % 4] for i in range(4)]
                prompt = PROMPT.format(text=it["text"], a=shown[0], b=shown[1],
                                       c=shown[2], d=shown[3])
                probs, top = letter_probs(prompt, a.chat)
                if probs:
                    shown_letter = max(probs, key=probs.get)
                    canon = LETTERS[(LETTERS.index(shown_letter) + r) % 4]
                else:
                    shown_letter, canon = None, None
                picks.append(canon)
                detail.append({"rotation": r, "shown_letter": shown_letter,
                               "canonical": canon,
                               "probs": {k: round(v, 4) for k, v in probs.items()},
                               "top_tokens": [t for t, _ in top]})
            valid = [p for p in picks if p]
            verdict = "NR"
            if valid:
                c = Counter(valid).most_common()
                if not (len(c) > 1 and c[0][1] == c[1][1]):
                    verdict = c[0][0]
            results.append({"id": it["id"], "layer": it.get("layer"),
                            "norm_option": it.get("norm_option"),
                            "verdict": verdict, "rotations": detail})
            print(it["id"], verdict, flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except Exception:
            proc.kill()
    out = HERE / f"{a.tag}{'_chat' if a.chat else ''}.json"
    json.dump({"model": a.model, "tag": a.tag, "chat": a.chat,
               "n": len(results), "items": results},
              open(out, "w"), ensure_ascii=False, indent=1)
    nr = sum(1 for r in results if r["verdict"] == "NR")
    print(f"DONE {a.tag} NR={nr}/{len(results)} -> {out}")


if __name__ == "__main__":
    main()

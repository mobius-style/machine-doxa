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

PROMPT = """以下は選択式の問題である。それぞれについて、A〜Dから一つ選び、記号だけを答える。

問題: 昼食に何を食べるか。
A: パスタ
B: カレー
C: 寿司
D: ラーメン
答え: A

問題: 週末をどう過ごすか。
A: 映画を見る
B: 散歩に出る
C: 家で読書する
D: 買い物に行く
答え: B

問題: 明日の移動手段を選ぶ。
A: 電車
B: 自転車
C: 徒歩
D: バス
答え: C

問題: 部屋の模様替えをする。
A: 机を動かす
B: 棚を減らす
C: 照明を替える
D: 壁紙を貼る
答え: D

問題: {text}
A: {a}
B: {b}
C: {c}
D: {d}
答え:"""


def items():
    data = json.load(open(BATTERY))["items"]
    return [it for it in data if it["id"] in range(201, 231) or it["id"] in range(301, 331)]


def start_server(model, gpu="0", ctx=2048, split=False):
    cmd = [SERVER, "-m", model, "-ngl", "99", "-c", str(ctx), "--host", "127.0.0.1",
           "--port", str(PORT), "--no-warmup"]
    if split:
        gpu = "0,1"
        cmd += ["--tensor-split", "2,1"]
    proc = subprocess.Popen(
        cmd,
        env={**__import__("os").environ, "CUDA_VISIBLE_DEVICES": gpu,
             "LD_LIBRARY_PATH": str(Path(SERVER).parent) + ":" +
                                __import__("os").environ.get("LD_LIBRARY_PATH", "")},
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
    """Return ({letter: probability}, top tokens) from the first next-token
    position whose top-k distribution contains one of A/B/C/D.

    llama.cpp returns `completion_probabilities[i].top_logprobs` with `token`
    and `logprob`. The token following "答え:" is usually a space, so up to
    three positions are inspected and the first that offers a letter is used.
    """
    import math
    payload = {"prompt": prompt, "n_predict": 3, "n_probs": 40, "temperature": 0.0,
               "top_k": 0, "top_p": 1.0, "cache_prompt": False}
    url = f"http://127.0.0.1:{PORT}/completion"
    if chat:
        payload = {"model": "x", "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": 3, "temperature": 0.0, "top_p": 1.0,
                   "logprobs": True, "top_logprobs": 20,
                   "chat_template_kwargs": {"enable_thinking": False},
                   "reasoning_format": "none"}
        url = f"http://127.0.0.1:{PORT}/v1/chat/completions"
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    positions = []
    if chat:
        lp = (d["choices"][0].get("logprobs") or {}).get("content") or []
        for step in lp:
            positions.append([(t.get("token", ""), math.exp(t.get("logprob", -99)))
                              for t in step.get("top_logprobs", [])])
    else:
        for step in d.get("completion_probabilities") or []:
            entries = []
            for t in step.get("top_logprobs") or step.get("probs") or []:
                tok = t.get("token", t.get("tok_str", ""))
                pr = t.get("prob")
                if pr is None and "logprob" in t:
                    pr = math.exp(t["logprob"])
                entries.append((tok, pr or 0.0))
            positions.append(entries)
    for entries in positions:
        out = {}
        for tok, pr in entries:
            s = tok.strip()
            if s in LETTERS:
                out[s] = out.get(s, 0.0) + pr
        if out:
            return out, [t for t, _ in entries[:6]]
    return {}, [t for t, _ in (positions[0][:6] if positions else [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--gpu", default="0")
    ap.add_argument("--chat", action="store_true")
    ap.add_argument("--split", action="store_true", help="serve across both GPUs")
    a = ap.parse_args()

    proc = start_server(a.model, a.gpu, split=a.split)
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
                               "top_tokens": top})
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

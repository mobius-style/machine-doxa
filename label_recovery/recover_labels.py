#!/usr/bin/env python3
"""Non-subject-family label recovery for the 60 new Doxa items (ids 201-330).
Each coder model sees ONLY the rubric + item text + options (no layer, no norm_option,
no agreement data) and must classify norm-transparent vs preference-pure and, if norm,
designate the norm option. Output: label_recovery/<model>.json. Standard library + ollama."""
import json, sys, urllib.request, re, time
BASE = "/home/happy/.codex/projects/machine_doxa"
RUBRIC = """You are classifying survey items about workplace and everyday decisions. Each item presents a situation and four options (A-D).

Definition — NORM-TRANSPARENT item: exactly one option instantiates a broadly trained professional/ethical norm — honest disclosure, verify before claiming, fail safe / prevent harm, comply with rules or law. That option is the "norm option". The other options are not wrong but are compromises, evasions, or shortcuts relative to that norm.

Definition — PREFERENCE-PURE item: all four options are normatively neutral style or workflow trade-offs (e.g., morning vs night work, planning vs improvisation, abstract-first vs concrete-first). No option is the ethically or professionally "correct" one.

Answer with ONE line of JSON only: {"label": "norm" or "preference", "norm_option": "A"/"B"/"C"/"D" or null, "reason": "<=20 words"}"""

import os
def _groq_key():
    for line in open("/home/happy/デスクトップ/mobius_ai/MOBIUS_MMV/.env"):
        if line.startswith("GROQ_API_KEY="): return line.split("=",1)[1].strip().strip('"').strip("'")
def ask(model, text, options):
    if model.startswith("groq:"):
        return ask_groq(model[5:], text, options)
    user = f"Situation: {text}\nOptions:\n" + "\n".join(f"{k}: {v}" for k, v in options.items()) + "\n\nClassify this item."
    payload = {"model": model, "stream": False, "think": False,
               "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}],
               "options": {"num_ctx": 4096, "temperature": 0.0}}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["message"]["content"].strip()

def ask_groq(model, text, options):
    user = f"Situation: {text}\nOptions:\n" + "\n".join(f"{k}: {v}" for k, v in options.items()) + "\n\nClassify this item."
    payload = {"model": model, "temperature": 0, "max_tokens": 200,
               "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {_groq_key()}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 3: raise
            time.sleep(3 * (attempt + 1))

def parse(s):
    m = re.search(r'\{.*\}', s, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    lab = str(d.get("label", "")).lower()
    lab = "norm" if lab.startswith("norm") else ("preference" if lab.startswith("pref") else "unparsed")
    no = d.get("norm_option"); no = no.strip().upper()[:1] if isinstance(no, str) and no.strip() else None
    if no is not None and no not in "ABCD": no = None
    return lab, no, d.get("reason", ""), s

def main(model, tag):
    items = [it for it in json.load(open(f"{BASE}/battery_doxa.json"))["items"] if 201 <= int(it["id"]) <= 330]
    out = []
    for it in items:
        t0 = time.time(); raw = ask(model, it["text"], it["options"]); lab, no, why, _ = parse(raw)
        out.append({"id": it["id"], "label": lab, "norm_option": no, "reason": why, "raw": raw[:300], "sec": round(time.time()-t0, 1)})
        print(it["id"], lab, no, flush=True)
    json.dump({"model": model, "n": len(out), "items": out}, open(f"{BASE}/label_recovery/{tag}.json", "w"), ensure_ascii=False, indent=1)
    print("DONE", model)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Run BillBench against OpenAI-compatible chat endpoints and log every call's cost.

  python -m billbench.run --dry                          # print tasks + answers, no calls
  python -m billbench.run --provider nebius --models deepseek-ai/DeepSeek-V4-Pro --repeats 3

Every API call is appended to results/spend-log.csv (tokens + estimated USD). The run
stops before any call that would push the cumulative estimate past --budget."""
import argparse, csv, datetime, json, os, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from .tasks import ALL as TASKS
from .grader import grade, attribute

PROVIDERS = {
    "nebius": ("https://api.studio.nebius.com/v1/chat/completions", "NEBIUS_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
}
# Conservative USD per 1M tokens (input, output): highest public list price seen for the
# model on 2026-11-02 (OpenRouter listings). Used for the budget guard; the provider's
# own bill is the source of truth.
PRICES = {
    "deepseek-ai/DeepSeek-V4-Pro": (1.60, 4.00),
    "moonshotai/Kimi-K3": (2.28, 15.00),
    "zai-org/GLM-5.3": (0.45, 3.60),
    "Qwen/Qwen3.5-397B-A17B": (0.50, 3.60),
    "nvidia/Nemotron-3-Ultra-550b-a55b": (0.60, 2.40),
    "openai/gpt-6.1-sol": (2.00, 10.00),
    "anthropic/claude-opus-5.5": (4.00, 20.00),
    "google/gemini-4-argon": (2.00, 10.00),
}
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(HERE, "results", "spend-log.csv")
FIELDS = ["ts", "provider", "model", "task", "repeat", "prompt_tokens", "completion_tokens", "est_usd", "cum_est_usd", "status"]
lock = threading.Lock()

def spent():
    if not os.path.exists(LOG):
        return 0.0
    with open(LOG) as f:
        return sum(float(r["est_usd"] or 0) for r in csv.DictReader(f))

def log(row):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)

def call(provider, model, prompt, max_tokens):
    url, env = PROVIDERS[provider]
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {os.environ[env]}", "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < 3:
                time.sleep(15 * (i + 1)); continue
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if i < 3:
                time.sleep(10 * (i + 1)); continue
            raise

def one(provider, model, task, rep, budget, max_tokens):
    pin, pout = PRICES.get(model, (5.0, 25.0))
    worst = (len(task["prompt"]) / 3 * pin + max_tokens * pout) / 1e6
    with lock:
        if spent() + worst > budget:
            return {"id": task["id"], "repeat": rep, "skipped": "budget"}
    t0 = time.time(); status = "ok"
    try:
        d = call(provider, model, task["prompt"], max_tokens)
        msg = d["choices"][0]["message"]; text = msg.get("content") or ""
        u = d.get("usage") or {}; finish = d["choices"][0].get("finish_reason")
    except Exception as e:
        text, u, finish, status = "", {}, None, f"error:{e}"[:120]
    pt, ct = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
    usd = (pt * pin + ct * pout) / 1e6
    with lock:
        cum = spent() + usd
        log({"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "provider": provider, "model": model,
             "task": task["id"], "repeat": rep, "prompt_tokens": pt, "completion_tokens": ct,
             "est_usd": f"{usd:.6f}", "cum_est_usd": f"{cum:.6f}", "status": status})
    if status != "ok":  # infrastructure error: not a model failure, excluded from the score
        return {"id": task["id"], "suite": task["suite"], "repeat": rep, "infra_error": status}
    ok, got = grade(text, task["answer"])
    return {"id": task["id"], "suite": task["suite"], "repeat": rep, "expected": task["answer"], "got": None if got is None else float(got),
            "correct": ok, "failure_modes": [] if ok else attribute(task, got), "finish_reason": finish,
            "seconds": round(time.time() - t0, 1), "prompt_tokens": pt, "completion_tokens": ct, "est_usd": round(usd, 6),
            "status": status, "output_tail": text[-1500:]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="nebius", choices=PROVIDERS)
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--budget", type=float, default=14.0, help="stop before cumulative estimated USD exceeds this")
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--suite", choices=["core", "expert", "control", "all"], default="all")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    tasks = [t for t in TASKS if (not a.tasks or t["id"] in a.tasks) and a.suite in ("all", t["suite"])]
    if a.dry or not a.models:
        for t in tasks:
            print(f'{t["suite"]:<6} {t["id"]}  {t["title"]:<62} answer ${t["answer"]:,.2f}')
        return
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    for m in a.models:
        jobs = [(t, r) for r in range(1, a.repeats + 1) for t in tasks]
        with ThreadPoolExecutor(a.workers) as ex:
            rows = list(ex.map(lambda tr: one(a.provider, m, tr[0], tr[1], a.budget, a.max_tokens), jobs))
        done = [r for r in rows if "skipped" not in r and "infra_error" not in r]
        score = sum(r["correct"] for r in done)
        out = a.out or os.path.join(HERE, "results", f"{a.suite}-{m.split('/')[-1]}-{stamp}.json")
        json.dump({"model": m, "provider": a.provider, "date": stamp, "suite": a.suite, "temperature": 0, "repeats": a.repeats,
                   "max_tokens": a.max_tokens, "rows": rows}, open(out, "w"), indent=1)
        print(f"{m}: {score}/{len(done)} correct ({len(rows)-len(done)} skipped: budget or infra error) -> {out}; cum est ${spent():.4f}")

if __name__ == "__main__":
    main()

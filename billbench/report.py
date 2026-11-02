"""Build results/SCOREBOARD.md and results/summary.json from the result JSONs (no API calls).

  python -m billbench.report results/final"""
import collections, csv, glob, json, os, sys
from .tasks import ALL
from .grader import describe

T = {t["id"]: t for t in ALL}
SUITES = ["expert", "core", "control"]

def load(folder):
    rows = []
    for f in sorted(glob.glob(os.path.join(folder, "*.json"))):
        if os.path.basename(f) == "summary.json":
            continue
        d = json.load(open(f))
        for r in d.get("rows", []):
            if "correct" in r:
                r["model"] = d["model"].split("/")[-1]; rows.append(r)
    return rows

def main(folder):
    rows = load(folder)
    models = sorted({r["model"] for r in rows})
    out = ["# BillBench scoreboard", "",
           f"Source: `{os.path.relpath(folder)}` ({len(rows)} graded responses; infrastructure errors are excluded and listed in the run log). Temperature 0, 3 repeats per task, strict `FINAL: $X.XX` grading to the cent.", ""]
    summary = {"models": models, "suites": {}}
    for suite in SUITES:
        ids = [t["id"] for t in ALL if t["suite"] == suite]
        sr = [r for r in rows if r["id"] in ids]
        if not sr:
            continue
        cell = collections.defaultdict(lambda: [0, 0])
        for r in sr:
            cell[(r["id"], r["model"])][0] += r["correct"]; cell[(r["id"], r["model"])][1] += 1
        title = {"expert": "BillBench-Expert (10 scored tasks: federal rules not spelled out)",
                 "core": "BillBench-Core (10 tasks, every rule stated: arithmetic control)",
                 "control": "Expert controls (piloted, solved by every model)"}[suite]
        out += [f"## {title}", "", "| Task | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
        for i in ids:
            out.append(f"| {i} {T[i]['title']} | " + " | ".join(f"{cell[(i,m)][0]}/{cell[(i,m)][1]}" if cell[(i,m)][1] else "-" for m in models) + " |")
        tot = {m: [sum(cell[(i, m)][0] for i in ids), sum(cell[(i, m)][1] for i in ids)] for m in models}
        out.append("| **Total** | " + " | ".join(f"**{a}/{b} ({100*a/b:.0f}%)**" if b else "-" for m, (a, b) in tot.items()) + " |")
        out.append("")
        summary["suites"][suite] = {"per_model": tot, "per_task": {i: {m: cell[(i, m)] for m in models} for i in ids}}
    # failure modes
    out += ["## Why the models failed (Expert + Core)", "", "| Task | Model | Answer given | Correct | Failure mode | Runs |", "|---|---|---|---|---|---|"]
    fm = collections.Counter()
    for r in rows:
        if not r["correct"] and T[r["id"]]["suite"] in ("expert", "core"):
            g = "none" if r["got"] is None else f"${r['got']:,.2f}"
            modes = "; ".join(describe(m, T[r["id"]]) for m in r["failure_modes"])
            fm[(r["id"], r["model"], g, f"${r['expected']:,.2f}", modes)] += 1
    for (i, m, g, e, modes), n in sorted(fm.items()):
        out.append(f"| {i} | {m} | {g} | {e} | {modes} | {n} |")
    summary["failures"] = [dict(task=k[0], model=k[1], got=k[2], expected=k[3], mode=k[4], runs=n) for k, n in sorted(fm.items())]
    # spend
    log = os.path.join(os.path.dirname(os.path.abspath(folder)), "spend-log.csv")
    if not os.path.exists(log):
        log = os.path.join(folder, "..", "spend-log.csv")
    if os.path.exists(log):
        sl = list(csv.DictReader(open(log)))
        out += ["", "## Cost", "", f"All model calls today (pilot + final): {len(sl)} calls, estimated USD {sum(float(x['est_usd']) for x in sl):.2f} at the highest public list price per model (see `results/spend-log.csv`; the provider's bill is the source of truth)."]
    open(os.path.join(folder, "SCOREBOARD.md"), "w").write("\n".join(out) + "\n")
    json.dump(summary, open(os.path.join(folder, "summary.json"), "w"), indent=1)
    print("\n".join(out))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")

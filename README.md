# BillBench: where frontier models get US medical-bill math wrong

## Demo video
- Unlisted walkthrough (2:31): https://youtu.be/6gdOIew4Wao
- Submitted to micro1 Eval Hackathon on HackerRank 2026-11-05 (CST).

## At a glance
- **What:** an eval of one question patients and billing staff ask every day: *"how much does the patient owe?"* 10 scored tasks (BillBench-Expert), each with one answer to the cent, graded by a deterministic engine. No LLM judge.
- **Headline result (2 Nov 2026, 5 frontier open-weight models, 3 runs each, temperature 0):** **117/150 (78%)** on Expert vs **143/150 (95%)** on a Core control where every rule is spelled out. Same models, same arithmetic, so the gap is missing billing knowledge, not math.
- **Hardest task:** Medicare DME from a supplier that does not accept assignment (x13): **3 of 15 runs correct.** In 7 runs the model applied the physician "limiting charge" (115%) to a DME supplier, which the law does not limit. The patient is told $31.50 when they will really pay $68.00.
- **Every wrong answer gets a reason:** the grader matches each wrong amount against the exact output of named, simulated mistakes (e.g. "counted the discharge day as an inpatient day"). 30 of the 40 wrong Expert/Core answers match a named mistake.
- **Reproduce:** `make test` (no key, about 1 s) · `make run` (needs a Nebius key; logs every call's tokens and cost) · `make report`.
- **Cost of every result here:** 729 API calls on 2 Nov 2026 (pilot + final), about **USD 7.51** estimated at list price (`results/spend-log.csv`).

## Why it matters
A wrong "you owe $X" is not a style problem. It decides whether a patient pays a bill they don't owe, skips care, or misses an appeal. Patients now paste bills into chatbots, and billing teams use AI assistants to answer calls. Most of the money in these cases comes from a handful of rules a billing professional knows by heart: the No Surprises Act, Medicare benefit periods and the 3-day SNF rule, the limiting charge, Medigap coverage, day counting, and family deductibles. BillBench tests exactly those rules on synthetic bills.

## Design
**Two suites, one engine.**
- **BillBench-Core (t01-t10), control.** Every cost-sharing rule is written in the prompt in Summary-of-Benefits language: allowed vs billed, deductible across lines, OOP cap, copays, not-covered, $0-allowed lines, plan-year reset, ER copay waiver, preventive vs diagnostic. Ground truth comes from `billbench/engine.py` (Decimal math) and is re-derived by hand in `tests/test_engine.py`.
- **BillBench-Expert (10 scored tasks), the eval.** Plan terms and 2026 dollar amounts are given, but the federal rule is not explained, because knowing it is the expertise under test. Each answer is written as literal arithmetic next to its public source (`billbench/expert.py`, `docs/SOURCES.md`).
- **Controls.** 4 more expert tasks (ground ambulance, air ambulance, 835 remittance codes, multiple-procedure reduction) were answered correctly 15/15 in the pilot. They are kept, run and reported as controls, not scored.

**Grader (`billbench/grader.py`).** It takes the last line `FINAL: $X.XX` and compares it to the cent. A missing or malformed line fails. Self-tests in `tests/test_grader.py` cover known-correct and known-wrong strings (bold, escaped `\$`, commas, a later self-correction, off by one cent, no dollar sign). Each task also lists its named mistakes, the exact amounts a specific error produces. A wrong answer that equals one of them is attributed to that error. Otherwise it is reported as "unexplained".

**What each Expert task tests**
| Task | Rule a billing expert applies | Correct |
|---|---|---|
| x01 | No Surprises Act: an out-of-network anesthesiologist at an in-network hospital gets in-network coinsurance, and no balance bill | $1,030.00 |
| x04 | Medicare limiting charge = 115% of the non-participating amount (95% of the fee schedule) | $66.50 |
| x05 | Medigap Plan G pays Part B coinsurance and excess charges, not the Part B deductible | $120.00 |
| x06 | The Part A deductible applies per benefit period (60 days out), not per stay or per year | $3,472.00 |
| x09 | Embedded family deductible tracked across a year of claims for 3 people | $980.00 |
| x10 | Polyp removal and anesthesia in a screening colonoscopy carry no cost-sharing (ACA) | $30.00 |
| x11 | The 3-day SNF rule counts inpatient days only; observation does not count | $4,500.00 |
| x12 | Day counting: admission day counts, discharge day doesn't; days 61-90 coinsurance | $8,246.00 |
| x13 | No limiting charge for DME suppliers that don't accept assignment | $68.00 |
| x14 | A SNF stay keeps the benefit period open; SNF days 21-100 coinsurance | $3,906.00 |

## Results (final locked run, 2 Nov 2026, Nebius Token Factory, 3 runs per task, temperature 0, max 12,000 output tokens)
| Model | Expert (scored) | Core (rules stated) | Controls |
|---|---|---|---|
| moonshotai/Kimi-K3 | 28/30 (93%) | 30/30 (100%) | 11/12 |
| Qwen/Qwen3.5-397B-A17B | 27/30 (90%) | 30/30 (100%) | 11/12 |
| nvidia/Nemotron-3-Ultra-550b-a55b | 26/30 (87%) | 27/30 (90%) | 12/12 |
| zai-org/GLM-5.3 | 23/30 (77%) | 30/30 (100%) | 12/12 |
| deepseek-ai/DeepSeek-V4-Pro | 13/30 (43%) | 26/30 (87%) | 11/12 |
| **All** | **117/150 (78%)** | **143/150 (95%)** | **57/60** |

Full matrix and every failure: `results/final/SCOREBOARD.md`. Raw responses (last 1,500 characters), tokens and cost per call: `results/final/*.json`.

**Why they failed (named, reproducible)**
- **DME limiting charge (x13), 12 of 15 runs wrong.** 7 runs capped the supplier at 115% of the approved amount ($31.50). That cap exists for physicians, not DME suppliers. 1 run assumed the supplier had to accept the approved amount ($18.00). 2 runs gave other wrong amounts and 2 hit the 12,000-token cap without a final answer. Only Kimi-K3 (2/3) and Nemotron (1/3) got it right.
- **Day counting (x12, x14), 8 wrong runs.** The models counted the discharge day, which adds one coinsurance day: $8,680 instead of $8,246, and $4,123 instead of $3,906.
- **Benefit periods (x06).** DeepSeek-V4-Pro got 0/3. Twice it treated the Part A deductible as once a year ($1,736), and once it charged it per admission ($5,208). The right answer, $3,472, needs the 60-day rule.
- **No Surprises Act (x01, and Core t07).** Models blocked the balance bill but still charged 50% out-of-network coinsurance ($1,375 instead of $1,030). This happened even when the rules were stated (Nemotron, Core t07, 0/3).
- **Observation vs inpatient (x11).** One DeepSeek run counted observation time toward the 3-day rule and told the patient the SNF stay was free. It actually costs $4,500.

## Honest limits
- **No closed frontier models were run.** The OpenRouter key on our box has no credits, so GPT, Claude and Gemini were not tested. `make run-openrouter` runs them as soon as credits exist. All five tested models are open-weight frontier models served by Nebius.
- **The tasks were piloted on the same models.** Two pilot tasks that every model solved became controls and were replaced by harder ones (x11-x14). Then a fresh final run was made with the task files locked (`results/TASKS-SHA256-final.txt`). The pilot results are kept unedited in `results/pilot/`. Selecting tasks this way can inflate failure rates on these five models.
- **3 runs per cell at temperature 0** shows stability, not a confidence interval. 5 of the 360 final responses hit the 12,000-token cap and are counted as failures.
- **Synthetic data only.** No real patients, claims or employer data. The rules are US federal rules as of 2026-11-02. State laws (for example ground-ambulance laws) are excluded by the prompts.
- **Not advice.** This is an evaluation of models, not billing or legal advice to anyone.
- Development used AI coding assistance. Every ground truth was checked by hand against the cited source.

## Reproduce
```bash
make test                       # 12 unit tests: ground truth + grader self-tests (no network)
make dry                        # list all 24 tasks and answers
export NEBIUS_API_KEY=...       # Nebius Token Factory
make run                        # 5 models x 24 tasks x 3 runs; every call -> results/spend-log.csv
make report                     # rebuild results/final/SCOREBOARD.md
python3 -m billbench.run --provider openrouter --suite expert --models openai/gpt-6.1-sol   # any OpenAI-compatible endpoint
```
Python 3.10+ standard library only. The runner stops before any call that would push the estimated spend past `--budget` (default USD 14).

## Files
`billbench/engine.py` (Core ground truth + simulated mistakes) · `billbench/expert.py` (Expert and control tasks, arithmetic, sources) · `billbench/tasks.py` (Core tasks) · `billbench/grader.py` · `billbench/run.py` · `billbench/report.py` · `docs/TASKS.md` (every prompt, answer and named mistake) · `docs/SOURCES.md` · `tests/` · `results/`

## Author
Igor Eduardo (Austin, TX): founder of Cortexa Social Inc, Antler Founder Residency (F26, Austin), 15 years as an entrepreneur, A.S. Solo submission. MIT License.

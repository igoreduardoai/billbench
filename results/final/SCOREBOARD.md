# BillBench scoreboard

Source: `results/final` (360 graded responses; infrastructure errors are excluded and listed in the run log). Temperature 0, 3 repeats per task, strict `FINAL: $X.XX` grading to the cent.

## BillBench-Expert (10 scored tasks: federal rules not spelled out)

| Task | DeepSeek-V4-Pro | GLM-5.3 | Kimi-K3 | Nemotron-3-Ultra-550b-a55b | Qwen3.5-397B-A17B |
|---|---|---|---|---|---|
| x01 Out-of-network anesthesiologist at an in-network hospital | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x04 Medicare: non-participating doctor who does not accept assignment | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| x05 Medigap Plan G with excess charges | 2/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| x06 Medicare Part A: three hospital stays in one year | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x09 Embedded family deductible across a year of claims | 2/3 | 1/3 | 3/3 | 3/3 | 3/3 |
| x10 Screening colonoscopy that removes a polyp | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x11 Skilled nursing facility after an observation stay | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x12 Long inpatient stay: counting days 61-90 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x13 Medicare DME rental from a supplier that does not accept assignment | 0/3 | 0/3 | 2/3 | 1/3 | 0/3 |
| x14 Benefit period kept open by a SNF stay | 0/3 | 1/3 | 2/3 | 3/3 | 3/3 |
| **Total** | **13/30 (43%)** | **23/30 (77%)** | **28/30 (93%)** | **26/30 (87%)** | **27/30 (90%)** |

## BillBench-Core (10 tasks, every rule stated: arithmetic control)

| Task | DeepSeek-V4-Pro | GLM-5.3 | Kimi-K3 | Nemotron-3-Ultra-550b-a55b | Qwen3.5-397B-A17B |
|---|---|---|---|---|---|
| t01 Billed vs. allowed | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t02 Deductible spans two lines | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t03 OOP maximum reached mid-visit | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t04 Not-covered service after OOP is met | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t05 Copay line and a $0-allowed bundled line | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t06 Embedded family deductible | 1/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t07 Surprise bill at an in-network hospital | 1/3 | 3/3 | 3/3 | 0/3 | 3/3 |
| t08 Deductible resets on January 1 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t09 ER copay waived on admission, minus upfront payment | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| t10 Preventive visit with diagnostic add-ons | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| **Total** | **26/30 (87%)** | **30/30 (100%)** | **30/30 (100%)** | **27/30 (90%)** | **30/30 (100%)** |

## Expert controls (piloted, solved by every model)

| Task | DeepSeek-V4-Pro | GLM-5.3 | Kimi-K3 | Nemotron-3-Ultra-550b-a55b | Qwen3.5-397B-A17B |
|---|---|---|---|---|---|
| x02 Out-of-network GROUND ambulance to an in-network ER | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| r03 Out-of-network AIR ambulance, emergency | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| x07 Reading an 835 remittance (claim adjustment group codes) | 3/3 | 3/3 | 2/3 | 3/3 | 2/3 |
| r08 Multiple-procedure reduction (stated plan rule, order trap) | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| **Total** | **11/12 (92%)** | **12/12 (100%)** | **11/12 (92%)** | **12/12 (100%)** | **11/12 (92%)** |

## Why the models failed (Expert + Core)

| Task | Model | Answer given | Correct | Failure mode | Runs |
|---|---|---|---|---|---|
| t06 | DeepSeek-V4-Pro | $621.00 | $505.00 | wrong amount not matching any simulated mistake | 2 |
| t07 | DeepSeek-V4-Pro | $1,375.00 | $1,030.00 | applies out-of-network coinsurance on the recognized amount (no balance bill) despite the No Surprises Act | 1 |
| t07 | DeepSeek-V4-Pro | $3,425.00 | $1,030.00 | applies out-of-network coinsurance and balance billing despite No Surprises Act protection | 1 |
| t07 | Nemotron-3-Ultra-550b-a55b | $1,375.00 | $1,030.00 | applies out-of-network coinsurance on the recognized amount (no balance bill) despite the No Surprises Act | 3 |
| x01 | DeepSeek-V4-Pro | $1,375.00 | $1,030.00 | blocked the balance bill but kept the 50% out-of-network coinsurance | 2 |
| x04 | Nemotron-3-Ultra-550b-a55b | $70.00 | $66.50 | skipped the 95% non-participating reduction (limiting charge $230 instead of $218.50) | 1 |
| x05 | DeepSeek-V4-Pro | $148.50 | $120.00 | made the patient pay the excess charge (Plan G covers it) | 1 |
| x05 | Nemotron-3-Ultra-550b-a55b | $126.00 | $120.00 | wrong amount not matching any simulated mistake | 1 |
| x06 | DeepSeek-V4-Pro | $1,736.00 | $3,472.00 | treated the Part A deductible as annual; merged all stays into one benefit period | 2 |
| x06 | DeepSeek-V4-Pro | $5,208.00 | $3,472.00 | charged the Part A deductible for every admission | 1 |
| x09 | DeepSeek-V4-Pro | $1,380.00 | $980.00 | applied the family cap to claim 3 but then charged Blair's own remaining deductible on claim 4 | 1 |
| x09 | GLM-5.3 | $740.00 | $980.00 | wrong amount not matching any simulated mistake | 1 |
| x09 | GLM-5.3 | none | $980.00 | no parseable FINAL: $X.XX line | 1 |
| x11 | DeepSeek-V4-Pro | $0.00 | $4,500.00 | counted observation time toward the 3-day rule and treated SNF days 1-20 as covered | 1 |
| x12 | DeepSeek-V4-Pro | $8,680.00 | $8,246.00 | counted the discharge day as an inpatient day; started coinsurance on day 60 | 3 |
| x13 | DeepSeek-V4-Pro | $29.93 | $68.00 | wrong amount not matching any simulated mistake | 1 |
| x13 | DeepSeek-V4-Pro | $31.50 | $68.00 | capped the supplier at a 115% limiting charge (it applies to physician services, not DME) | 1 |
| x13 | DeepSeek-V4-Pro | $71.60 | $68.00 | wrong amount not matching any simulated mistake | 1 |
| x13 | GLM-5.3 | $31.50 | $68.00 | capped the supplier at a 115% limiting charge (it applies to physician services, not DME) | 2 |
| x13 | GLM-5.3 | none | $68.00 | no parseable FINAL: $X.XX line | 1 |
| x13 | Kimi-K3 | none | $68.00 | no parseable FINAL: $X.XX line | 1 |
| x13 | Nemotron-3-Ultra-550b-a55b | $31.50 | $68.00 | capped the supplier at a 115% limiting charge (it applies to physician services, not DME) | 2 |
| x13 | Qwen3.5-397B-A17B | $18.00 | $68.00 | assumed the supplier must accept the approved amount | 1 |
| x13 | Qwen3.5-397B-A17B | $31.50 | $68.00 | capped the supplier at a 115% limiting charge (it applies to physician services, not DME) | 2 |
| x14 | DeepSeek-V4-Pro | $4,123.00 | $3,906.00 | counted the SNF discharge day | 3 |
| x14 | GLM-5.3 | $4,123.00 | $3,906.00 | counted the SNF discharge day | 1 |
| x14 | GLM-5.3 | none | $3,906.00 | no parseable FINAL: $X.XX line | 1 |
| x14 | Kimi-K3 | $4,123.00 | $3,906.00 | counted the SNF discharge day | 1 |

## Cost

All model calls today (pilot + final): 729 calls, estimated USD 7.51 at the highest public list price per model (see `results/spend-log.csv`; the provider's bill is the source of truth).

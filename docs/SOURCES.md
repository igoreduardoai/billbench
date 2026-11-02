# Sources for each ground-truth rule

All task data is synthetic (invented patients, prices and dates). The rules come from public
federal sources, checked on 2026-11-02. If a rule changes, the task must be updated; the
2026 dollar amounts are stated inside each prompt so no task depends on a model knowing them.

| Task | Rule | Public source |
|---|---|---|
| x01 | No Surprises Act: out-of-network ancillary provider (anesthesiology) at an in-network hospital is cost-shared at in-network rates on the recognized amount; no balance billing; notice-and-consent cannot be used for anesthesiology | 42 U.S.C. 300gg-132; 45 CFR 149.420; CMS "Overview of Key Consumer Protections" (nsa-keyprotections.pdf) |
| x02 (control) | The No Surprises Act does not cover ground ambulance | CMS nsa-keyprotections.pdf; CMS "Know your rights with insurance" |
| r03 (control) | Out-of-network air ambulance: no balance billing, in-network cost-sharing counted toward in-network deductible/OOP | 42 U.S.C. 300gg-112; CMS NSA decision tree, Section C |
| x04 | Medicare limiting charge: non-participating, non-assigned physician may charge at most 115% of the non-participating fee schedule amount (95% of the participating amount) | Social Security Act 1848(g) (42 U.S.C. 1395w-4(g)); Medicare.gov "Does your provider accept Medicare as full payment?" |
| x05 | Medigap Plan G covers Part B coinsurance and Part B excess charges, not the Part B deductible | Medicare.gov / CMS "Choosing a Medigap Policy" benefits chart |
| x06, x14 | Part A deductible applies per benefit period; a benefit period ends after 60 consecutive days with no inpatient hospital or SNF care | 42 CFR 409.60; Medicare.gov "2026 Medicare Costs" (CMS product 11579) |
| x07 (control) | X12 835 group codes: PR = patient responsibility; CO = contractual obligation (not billable to patient); OA = other adjustment | X12 Claim Adjustment Group Codes; CARC list (codes 1, 2, 3, 23, 45, 97, 204) |
| r08 (control) | Multiple-procedure reduction (rule stated in the prompt) | Medicare Claims Processing Manual ch.12 §40.6 (mirrors it) |
| x09 | Embedded family deductible | HealthCare.gov glossary; rule restated in the prompt |
| x10 | Polyp removal and anesthesia during an in-network screening colonoscopy carry no cost-sharing | PHS Act 2713; ACA Implementation FAQs Part XII Q5 (2013) and Part XXIX Q5 (2015); USPSTF 2021 (ages 45-75) |
| x11 | SNF coverage needs 3 consecutive INPATIENT days (discharge day not counted); observation time does not count | 42 CFR 409.30(a); Medicare.gov "Inpatient or outpatient hospital status" |
| x12 | Inpatient day counting: admission day counts, discharge day does not; days 61-90 coinsurance | Medicare Benefit Policy Manual ch.3 §20.1; Medicare.gov "2026 Medicare Costs" |
| x13 | No limiting charge for DME: a non-assigned supplier may charge any amount; Medicare pays 80% of the approved amount | Medicare.gov "Durable Medical Equipment Coverage"; Center for Medicare Advocacy, "Durable Medical Equipment" |
| x14 | SNF coinsurance days 21-100; SNF days are counted like inpatient days (admission day counts, discharge day does not) | 42 CFR 409.85; Medicare Benefit Policy Manual ch.3 §20.1; CMS 2026 Part A amounts ($217/day) |

2026 amounts used in prompts (CMS fact sheet, Nov 14 2025, and Federal Register 2025-20249/2025-20251): Part A deductible $1,736; days 61-90 $434/day; lifetime reserve $868/day; SNF days 21-100 $217/day; Part B deductible $283.

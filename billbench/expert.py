"""BillBench-Expert: 10 synthetic tasks where the correct answer depends on US billing
rules a billing professional knows, not only on arithmetic.

Plan terms are stated; the federal rule (No Surprises Act, Medicare, ACA preventive care,
X12 remittance codes) is NOT spelled out, because knowing it is the expertise under test.
Every answer is computed below with literal arithmetic and the public rule it rests on
(see docs/SOURCES.md). Each listed mistake is the exact amount a specific, common error
produces, so the grader can name why a model failed."""
from decimal import Decimal as D

TAIL = "Show your work briefly, then end with exactly one line: FINAL: $X.XX"
BASE = """You are checking a patient's bill for a US health plan. Use current US federal law (2026) where it applies.
General plan mechanics: in-network providers accept the plan's allowed amount (billed minus allowed is a provider discount the patient never owes); the patient pays the remaining deductible first, then coinsurance on the rest; copays, deductible and coinsurance count toward the out-of-pocket (OOP) maximum, after which covered cost-sharing is $0. Round to the cent."""

def c(x):
    return D(str(x)).quantize(D("0.01"))

def task(id, title, rule, prompt, answer, mistakes, source):
    return {"id": id, "suite": "expert", "title": title, "trap": rule,
            "prompt": BASE + "\n\n" + prompt.strip() + "\n\n" + TAIL,
            "answer": float(c(answer)), "mistake_values": {k: c(v[0]) for k, v in mistakes.items()},
            "mistake_text": {k: v[1] for k, v in mistakes.items()}, "mistakes": list(mistakes), "source": source,
            "visits": None, "plan": None, "prior": 0}

EXPERT = [
 task("x01", "Out-of-network anesthesiologist at an in-network hospital",
      "No Surprises Act: in-network cost-sharing on the recognized amount; no balance billing",
      """Plan: deductible met ($0 remaining). In-network coinsurance 20%. Out-of-network coinsurance 50% of the plan's recognized amount, and under the plan contract out-of-network providers may bill the difference between their charge and that amount. OOP maximum remaining $6,000.00.
Scheduled knee surgery on August 3, 2026 at an IN-NETWORK hospital:
- Hospital facility charge (in-network): billed $18,500.00, allowed $4,000.00
- Anesthesiologist (OUT-OF-NETWORK, working at that hospital): billed $3,200.00, plan recognized amount $1,150.00
The anesthesiologist's statement says "balance due from patient: $2,050.00". The patient signed no notice-and-consent waiver. It is an employer group health plan.
How much does the patient owe in total for this surgery?""",
      D("0.20") * 4000 + D("0.20") * 1150,
      {"nsa_ignored": (800 + D("0.5") * 1150 + 2050, "applied out-of-network coinsurance AND paid the balance bill"),
       "nsa_oon_coins": (800 + D("0.5") * 1150, "blocked the balance bill but kept the 50% out-of-network coinsurance"),
       "nsa_balance_only": (800 + D("0.2") * 1150 + 2050, "used in-network coinsurance but still paid the balance bill")},
      "45 CFR 149.420; 42 U.S.C. 300gg-132; CMS NSA key protections (nsa-keyprotections.pdf)"),
 task("x02", "Out-of-network GROUND ambulance to an in-network ER",
      "the No Surprises Act does not cover ground ambulance; balance billing is allowed absent state law",
      """Plan: deductibles met. In-network coinsurance 20%. Out-of-network coinsurance 40% of the plan allowed amount; out-of-network providers may bill the difference between their charge and the allowed amount. In-network OOP maximum remaining $5,000.00; out-of-network OOP maximum remaining $8,000.00 (balance-billed amounts never count toward either).
Emergency on May 9, 2026. The patient's state has NO law limiting ground-ambulance balance billing.
- Ground ambulance (OUT-OF-NETWORK, emergency transport): billed $1,800.00, plan allowed $700.00
- Emergency room at an IN-NETWORK hospital: billed $4,100.00, allowed $1,500.00
How much does the patient owe in total?""",
      D("0.4") * 700 + (1800 - 700) + D("0.2") * 1500,
      {"nsa_applied_to_ground": (D("0.2") * 700 + D("0.2") * 1500, "applied No Surprises Act protection to a ground ambulance"),
       "no_balance_bill": (D("0.4") * 700 + D("0.2") * 1500, "dropped the ground-ambulance balance bill"),
       "nsa_coins_but_balance": (D("0.2") * 700 + 1100 + D("0.2") * 1500, "used in-network coinsurance for the ambulance but kept the balance bill")},
      "CMS NSA key protections: protections do not apply to ground ambulance services; CMS 'Know your rights' (ground ambulance)"),
 task("r03", "Out-of-network AIR ambulance, emergency",
      "air ambulance is protected: in-network cost-sharing, counted toward the in-network deductible and OOP maximum",
      """Plan: in-network deductible remaining $500.00, in-network coinsurance 20%, in-network OOP maximum remaining $3,000.00. Out-of-network deductible remaining $2,000.00, out-of-network coinsurance 40%, out-of-network OOP maximum remaining $10,000.00; out-of-network providers may bill the difference between their charge and the plan amount.
June 2, 2026: emergency helicopter transport by an OUT-OF-NETWORK air ambulance company (the plan covers air ambulance). Billed $48,000.00; plan recognized (qualifying payment) amount $22,000.00. Employer group health plan; no other claims this year.
How much does the patient owe the air ambulance company?""",
      D("3000"),
      {"oop_cap_missed": (500 + D("0.2") * 21500, "used in-network cost-sharing but ignored the in-network OOP maximum"),
       "oon_with_balance": (D("10000") + (48000 - 22000), "applied out-of-network cost-sharing plus the balance bill"),
       "oon_no_balance": (D("10000"), "blocked the balance bill but applied out-of-network deductible/coinsurance")},
      "42 U.S.C. 300gg-112; 45 CFR 149.130; CMS NSA decision tree, Section C (air ambulance)"),
 task("x04", "Medicare: non-participating doctor who does not accept assignment",
      "Medicare limiting charge = 115% of the non-participating fee schedule amount (95% of the participating amount)",
      """Original Medicare Part B only (no supplemental coverage). The 2026 Part B deductible is already met. Office procedure on April 14, 2026 by a NON-PARTICIPATING physician who does NOT accept assignment for this claim and charges the maximum amount federal law allows. The Medicare Physician Fee Schedule amount for a PARTICIPATING physician for this service is $200.00.
How much does the patient pay out of pocket for this service?""",
      D("1.15") * D("0.95") * 200 - D("0.8") * D("0.95") * 200,
      {"par_rate": (D("0.2") * 200, "used participating-provider coinsurance (20% of $200)"),
       "coins_only_nonpar": (D("0.2") * D("0.95") * 200, "took 20% of the non-participating amount and ignored the limiting charge"),
       "limiting_on_par": (D("1.15") * 200 - D("0.8") * D("0.95") * 200, "computed the limiting charge on the participating amount"),
       "limiting_minus_par_pay": (D("1.15") * D("0.95") * 200 - D("0.8") * 200, "subtracted Medicare's participating payment instead of its non-participating payment"),
       "no_95pct_reduction": (D("1.15") * 200 - D("0.8") * 200, "skipped the 95% non-participating reduction (limiting charge $230 instead of $218.50)")},
      "42 U.S.C. 1395w-4(g) (limiting charge); Medicare.gov 'Lower costs with assignment'"),
 task("x05", "Medigap Plan G with excess charges",
      "Plan G pays Part B coinsurance and Part B excess charges, but not the Part B deductible",
      """Original Medicare Part B plus a Medigap (Medicare Supplement) Plan G policy. $120.00 of the 2026 Part B deductible ($283) remains unmet. Specialist visit on March 3, 2026 by a NON-PARTICIPATING physician who does NOT accept assignment and charges the full limiting charge. The participating Medicare Physician Fee Schedule amount is $200.00.
After Medicare and Plan G pay, how much does the patient pay?""",
      D("120"),
      {"excess_not_covered": (120 + D("1.15") * 190 - 190, "made the patient pay the excess charge (Plan G covers it)"),
       "coins_not_covered": (120 + D("0.2") * (190 - 120), "made the patient pay Part B coinsurance (Plan G covers it)"),
       "deductible_covered": (D("0"), "assumed Plan G pays the Part B deductible"),
       "deductible_plus_all": (120 + D("0.2") * 70 + D("28.50"), "left both coinsurance and the excess charge with the patient"),
       "g_reversed": (D("28.50"), "reversed Plan G: said it pays the Part B deductible but not excess charges"),
       "excess_on_par_amount": (120 + D("30"), "made the patient pay the deductible plus an excess charge computed without the 95% reduction")},
      "Medicare.gov 'Choosing a Medigap Policy' (2026) benefits chart: Plan G covers Part B excess charges 100%; not the Part B deductible"),
 task("x06", "Medicare Part A: three hospital stays in one year",
      "the Part A deductible applies per BENEFIT PERIOD (ends after 60 days in a row out of hospital/SNF), not per stay or per year",
      """Original Medicare Part A. 2026 Part A inpatient hospital deductible: $1,736.00. Days 61-90 coinsurance: $434.00/day. Three covered inpatient stays in 2026; between stays the patient was at home (not in any hospital or skilled nursing facility). No inpatient stays in 2025.
- Stay 1: admitted March 2, discharged March 8, 2026
- Stay 2: admitted April 20, discharged April 25, 2026
- Stay 3: admitted July 15, discharged July 19, 2026
What is the patient's total Part A inpatient cost-sharing for the three stays (no Medigap, no Part B items)?""",
      D("1736") * 2,
      {"per_stay": (D("1736") * 3, "charged the Part A deductible for every admission"),
       "per_year": (D("1736"), "treated the Part A deductible as annual"),
       "per_stay_minus_one": (D("1736"), "merged all stays into one benefit period")},
      "Medicare.gov 2026 Medicare Costs (deductible per benefit period); 42 CFR 409.60 (benefit period ends after 60 consecutive days)"),
 task("x07", "Reading an 835 remittance (claim adjustment group codes)",
      "only PR-group adjustments are patient responsibility; CO and OA amounts may not be billed to the patient",
      """An in-network clinic's electronic remittance advice (X12 835) for one claim, March 18, 2026. Each service line lists billed amount, adjustments as GROUP-CARC amount, and plan payment.
Line 1: billed $450.00 | CO-45 $210.00 | PR-1 $150.00 | paid $90.00
Line 2: billed $300.00 | CO-45 $120.00 | PR-2 $36.00 | paid $144.00
Line 3: billed $85.00 | CO-97 $85.00 | paid $0.00
Line 4: billed $120.00 | PR-204 $120.00 | paid $0.00
Line 5: billed $200.00 | CO-45 $40.00 | OA-23 $60.00 | PR-3 $25.00 | paid $75.00
According to this remittance, what is the total amount the clinic may bill the patient for this claim?""",
      D("150") + 36 + 120 + 25,
      {"plus_co97": (D("331") + 85, "billed the patient for a CO-97 bundled line"),
       "all_unpaid": (D("1155") - 309, "billed the patient for everything the plan did not pay"),
       "plus_oa": (D("331") + 60, "billed the patient for the OA-23 prior-payer adjustment"),
       "no_pr204": (D("331") - 120, "dropped PR-204 (non-covered, patient responsibility)")},
      "X12 / Washington Publishing Co. Claim Adjustment Group Codes (CO, PR, OA) and CARC list (1, 2, 3, 23, 45, 97, 204)"),
 task("r08", "Multiple-procedure reduction (stated plan rule, order trap)",
      "the HIGHEST-allowed procedure is paid at 100% regardless of listing order",
      """Plan rule: when several surgical procedures are done in one session, the plan allows 100% of the fee schedule for the procedure with the highest fee schedule amount and 50% for each additional procedure. The deductible remaining is $1,000.00, coinsurance 20%, OOP maximum remaining $5,000.00. All in-network.
Surgery on September 22, 2026, procedures in the order the surgeon listed them:
- Procedure A: billed $1,500.00, fee schedule $600.00
- Procedure B: billed $3,900.00, fee schedule $1,400.00
- Procedure C: billed $800.00, fee schedule $300.00
How much does the patient owe the surgeon?""",
      1000 + D("0.2") * (1400 + 300 + 150 - 1000),
      {"listing_order": (1000 + D("0.2") * (600 + 700 + 150 - 1000), "reduced procedures in listing order instead of by fee"),
       "no_reduction": (1000 + D("0.2") * (2300 - 1000), "ignored the multiple-procedure reduction"),
       "billed_based": (1000 + D("0.2") * (3900 + 750 + 400 - 1000), "applied the reduction to billed amounts")},
      "Plan rule stated in the task (mirrors CMS multiple procedure payment reduction, Medicare Claims Processing Manual ch.12 §40.6)"),
 task("x09", "Embedded family deductible across a year of claims",
      "each person's deductible ends when the FAMILY deductible is met, even if their own is not",
      """Family plan, 3 members, plan year = 2026, EMBEDDED deductible: $1,500.00 per person / $3,000.00 per family (a person's deductible is satisfied when either their own or the family deductible is met). Coinsurance 20% after deductible. OOP maximum $5,000.00 per person / $9,000.00 per family (not reached). All in-network, all deductible/coinsurance services, no claims before these:
1. Feb 10 - Alex: allowed $1,800.00
2. Apr 5 - Blair: allowed $1,000.00
3. Jun 18 - Casey: allowed $900.00
4. Aug 30 - Blair: allowed $2,000.00
How much does the family owe for claims 3 and 4 combined?""",
      (500 + D("0.2") * 400) + D("0.2") * 2000,
      {"no_family_cap": (D("900") + (500 + D("0.2") * 1500), "ignored the family deductible (individual deductibles only)"),
       "family_met_early": (D("0.2") * 900 + D("0.2") * 2000, "treated the family deductible as met before claim 3"),
       "family_cap_forgotten_later": ((500 + D("0.2") * 400) + (500 + D("0.2") * 1500), "applied the family cap to claim 3 but then charged Blair's own remaining deductible on claim 4")},
      "Healthcare.gov glossary 'Embedded deductible'; plan rule stated in the task"),
 task("x10", "Screening colonoscopy that removes a polyp",
      "ACA preventive coverage: polyp removal and anesthesia during a screening colonoscopy carry no cost-sharing",
      """Non-grandfathered employer plan. Deductible remaining $1,500.00, coinsurance 20%, $30.00 copay for specialist office visits (deductible does not apply to that copay), OOP maximum remaining $5,000.00. All in-network.
- Sept 8, 2026: SCREENING colonoscopy for an average-risk 52-year-old with no symptoms; the gastroenterologist found and removed a polyp. Claim: colonoscopy with polyp removal, billed $3,400.00, allowed $1,250.00
- Same day: anesthesia for that colonoscopy, billed $900.00, allowed $310.00
- Sept 29, 2026: dermatologist office visit for an unrelated rash, billed $260.00, allowed $140.00
How much does the patient owe in total?""",
      D("30"),
      {"polyp_cost_shared": (D("1250") + 250 + D("0.2") * 60 + 30, "charged deductible/coinsurance on the polyp removal and anesthesia"),
       "polyp_only": (D("1250") + 30, "charged the polyp removal but not the anesthesia"),
       "anesthesia_only": (D("310") + 30, "charged the anesthesia but not the polyp removal"),
       "no_copay": (D("0"), "dropped the unrelated visit's copay")},
      "PHS Act 2713; ACA Implementation FAQs Part XII Q5 (polyp removal) and Part XXIX Q5 (anesthesia); USPSTF 2021 colorectal screening ages 45-75"),
 task("x11", "Skilled nursing facility after an observation stay",
      "Medicare's 3-day rule counts INPATIENT days only; observation time does not qualify a SNF stay",
      """Original Medicare (Parts A and B), no Medigap, not in any ACO or SNF-waiver program, no hospital or SNF stay in the past year.
- Jan 3, 2026, 7 pm: arrives at the ER and is placed in OUTPATIENT OBSERVATION status.
- Jan 4, 2026, 11 am: the doctor writes an inpatient admission order; the patient is formally admitted as an INPATIENT.
- Jan 6, 2026: discharged from the hospital and admitted the same day to a Medicare-certified skilled nursing facility (SNF) for daily rehab ordered by the doctor.
- Jan 16, 2026: discharged home from the SNF (10 days in the SNF).
2026 Medicare SNF coinsurance for days 21-100 is $217.00/day. The SNF's private daily rate, charged when Medicare does not cover the stay, is $450.00/day.
How much does the patient owe the SNF for the 10 days?""",
      D("450") * 10,
      {"snf_covered": (D("0"), "counted observation time toward the 3-day rule and treated SNF days 1-20 as covered"),
       "coins_charged": (D("217") * 10, "treated the stay as covered but charged the days 21-100 coinsurance"),
       "partial": (D("450") * 7, "miscounted SNF days")},
      "42 CFR 409.30(a) (3 consecutive inpatient days, discharge day not counted); Medicare.gov 'Inpatient or outpatient hospital status' and 'Skilled nursing facility care'"),
 task("x12", "Long inpatient stay: counting days 61-90",
      "Medicare counts the admission day but not the discharge day; coinsurance starts on day 61 of the benefit period",
      """Original Medicare Part A, no Medigap. 2026 Part A inpatient deductible: $1,736.00. Days 61-90 coinsurance: $434.00/day. Lifetime reserve days: $868.00/day. The patient had no hospital or SNF stay in the prior 6 months and has never used lifetime reserve days.
One continuous covered inpatient stay: admitted January 2, 2026, discharged March 18, 2026.
What is the patient's total Part A cost-sharing for this stay?""",
      D("1736") + 15 * D("434"),
      {"discharge_day_counted": (D("1736") + 16 * D("434"), "counted the discharge day as an inpatient day"),
       "no_daily_coins": (D("1736"), "missed the days 61-90 daily coinsurance"),
       "short_count": (D("1736") + 14 * D("434"), "undercounted the stay by one day"),
       "coins_from_day_60": (D("1736") + 16 * D("434"), "started coinsurance on day 60")},
      "Medicare.gov 2026 Medicare Costs (Part A amounts); Medicare Benefit Policy Manual ch.3 §20.1 (day of discharge not counted)"),
 task("x13", "Medicare DME rental from a supplier that does not accept assignment",
      "the 15% limiting charge protects physician services, not DME: a non-assigned supplier may charge any amount",
      """Original Medicare Part B, no Medigap. The 2026 Part B deductible is already met. The patient's doctor orders a semi-electric hospital bed (covered DME, medically necessary). The patient rents it from a Medicare-ENROLLED, NON-PARTICIPATING supplier that does NOT accept assignment on this claim. For the first rental month (May 2026) the supplier charges $140.00 and the patient pays the supplier in full. The Medicare-approved amount for that rental month is $90.00. Medicare processes the claim normally.
For that first rental month, what is the patient's net out-of-pocket cost after Medicare's payment?""",
      D("140") - D("0.8") * 90,
      {"limiting_charge_applied": (D("1.15") * 90 - D("0.8") * 90, "capped the supplier at a 115% limiting charge (it applies to physician services, not DME)"),
       "coins_only": (D("0.2") * 90, "assumed the supplier must accept the approved amount"),
       "limiting_on_95": (D("1.15") * D("0.95") * 90 - D("0.8") * D("0.95") * 90, "applied the physician non-participating formula to DME")},
      "Medicare.gov 'Durable Medical Equipment Coverage' and 'Does your provider accept Medicare as full payment?'; Center for Medicare Advocacy, DME (no limiting charge for DME suppliers)"),
 task("x14", "Benefit period kept open by a SNF stay",
      "a benefit period ends only after 60 days in a row with no hospital AND no SNF care",
      """Original Medicare Part A, no Medigap. 2026 amounts: inpatient deductible $1,736.00; SNF coinsurance days 21-100 $217.00/day. No hospital or SNF care in 2025.
- Mar 1, 2026: admitted as a hospital INPATIENT; discharged Mar 5, 2026.
- Mar 5, 2026: admitted to a Medicare-certified SNF for daily skilled rehab (covered); discharged home Apr 4, 2026.
- May 20, 2026: admitted as a hospital INPATIENT again; discharged May 23, 2026.
All care is covered. What is the patient's total Part A cost-sharing for all of this care?""",
      D("1736") + 10 * D("217"),
      {"new_period_from_hospital": (2 * D("1736") + 10 * D("217"), "started a new benefit period by counting from the hospital discharge, ignoring the SNF days"),
       "snf_all_coins": (D("1736") + 30 * D("217"), "charged SNF coinsurance from day 1"),
       "snf_free": (D("1736"), "missed the SNF days 21-100 coinsurance"),
       "snf_11_days": (D("1736") + 11 * D("217"), "counted the SNF discharge day")},
      "42 CFR 409.60 (benefit period ends after 60 consecutive days not an inpatient of a hospital or SNF); 42 CFR 409.85 (SNF coinsurance days 21-100); Medicare.gov 2026 Medicare Costs"),
]


# Pilot (2026-11-02): r03, r08, x02 and x07 were answered correctly in 15/15 runs by all five
# models, so they are kept as CONTROLS (still run and reported) and the 10 scored tasks are:
SCORED = ["x01", "x04", "x05", "x06", "x09", "x10", "x11", "x12", "x13", "x14"]
CONTROLS = [t for t in EXPERT if t["id"] not in SCORED]
for t in CONTROLS:
    t["suite"] = "control"
EXPERT = [t for t in EXPERT if t["id"] in SCORED]

"""BillBench v1: 10 synthetic US medical-bill tasks (no real patient data).

Each task is an estimate a patient or a billing rep would actually need: "what does the
patient owe (or still owe)?" The plan rules are stated in the prompt in Summary of
Benefits and Coverage (SBC) language, so every task has one defensible answer to the cent.
The answer comes from billbench.engine (deterministic) and is hand-checked in tests.
"""
from .engine import Line, Visit, Plan, compute, MISTAKES

RULES = """Plan rules (from the plan's Summary of Benefits and Coverage):
1. In-network providers accept the plan's ALLOWED amount. The difference between the billed amount and the allowed amount is a provider discount; the patient never owes it.
2. Services marked "Copay": the patient pays only the flat copay (the deductible does not apply). If the allowed amount is less than the copay, the patient pays the allowed amount.
3. Services marked "Deductible/Coinsurance": the patient pays the allowed amount until the remaining deductible is used up, then the coinsurance percentage of the rest of the allowed amount.
4. Copays, deductible and coinsurance all count toward the out-of-pocket (OOP) maximum. Once the OOP maximum is reached, covered services cost the patient $0 for the rest of the plan year.
5. Services marked "Not covered" are owed in full at the listed price. They do not count toward the deductible or the OOP maximum.
6. Lines are processed in the order listed. Round each line to the cent."""

def money(x):
    return f"${x:,.2f}"

LABEL = {"copay": "Copay", "er_copay": "Copay (ER)", "ded_coins": "Deductible/Coinsurance",
         "preventive": "Preventive", "noncovered": "Not covered"}

def render_lines(lines):
    out = []
    for ln in lines:
        net = "out-of-network" if ln.oon else "in-network"
        amt = f"allowed {money(ln.allowed)}" if ln.kind != "noncovered" else f"price {money(ln.allowed)}"
        if ln.oon:
            amt = f"plan recognized amount {money(ln.allowed)}"
        out.append(f"   - {ln.desc} | billed {money(ln.billed)} | {amt} | {LABEL[ln.kind]} | {net}")
    return "\n".join(out)

def make(id, title, trap, plan_facts, visits, plan, question, extra="", prior=0.0, mistakes=()):
    body = [RULES, "", "This patient's plan:", plan_facts]
    if extra:
        body += ["", extra]
    for i, v in enumerate(visits, 1):
        hdr = f"Visit {i} ({v.when})" if hasattr(v, "when") else f"Visit {i}"
        if v.admitted:
            hdr += ", patient was admitted to the hospital from the ER"
        body += ["", hdr + ":", render_lines(v.lines)]
    body += ["", question, "Show your work briefly, then end with exactly one line: FINAL: $X.XX"]
    answer = compute(visits, plan, prior)
    mv = {m: compute(visits, plan, prior, m) for m in mistakes}
    return {"id": id, "suite": "core", "title": title, "trap": trap, "prompt": "\n".join(body), "answer": float(answer),
            "visits": visits, "plan": plan, "prior": prior, "mistakes": list(mistakes), "mistake_values": mv}

def V(year, lines, admitted=False, when=None):
    v = Visit(year, lines, admitted); v.when = when or str(year); return v

Q = "How much does the patient owe in total for these services?"

TASKS = [
 make("t01", "Billed vs. allowed", "patient cost is based on the allowed amount, not the billed amount",
      "- Deductible: already met for the year ($0 remaining)\n- Coinsurance: 20%\n- OOP maximum remaining: $3,000.00",
      [V(2026, [Line("Specialist office visit", 385.00, 142.60), Line("Electrocardiogram (EKG)", 210.00, 38.15)], when="March 4, 2026")],
      Plan(coinsurance=.2, accum={2026: dict(ded_ind=0, oop_ind=3000)}), Q,
      mistakes=["billed_not_allowed"]),
 make("t02", "Deductible spans two lines", "the remaining deductible is used up partway through the second line",
      "- Deductible remaining: $750.00\n- Coinsurance: 20%\n- OOP maximum remaining: $4,000.00",
      [V(2026, [Line("MRI, lumbar spine", 2850.00, 612.40), Line("Radiologist interpretation", 420.00, 187.30)], when="April 9, 2026")],
      Plan(coinsurance=.2, accum={2026: dict(ded_ind=750, oop_ind=4000)}), Q,
      mistakes=["billed_not_allowed"]),
 make("t03", "OOP maximum reached mid-visit", "cost-sharing stops at the OOP maximum, including a later copay",
      "- Deductible: met ($0 remaining)\n- Coinsurance: 30%\n- Copay for office visits: $40.00\n- OOP maximum remaining: $900.00",
      [V(2026, [Line("Knee arthroscopy (surgeon)", 9400.00, 2400.00), Line("Anesthesia (in-network)", 1900.00, 640.00), Line("Post-op office visit", 180.00, 96.00, "copay")], when="May 12, 2026")],
      Plan(coinsurance=.3, copay=40, accum={2026: dict(ded_ind=0, oop_ind=900)}), Q,
      mistakes=["ignore_oop_cap"]),
 make("t04", "Not-covered service after OOP is met", "a non-covered service is still owed in full after the OOP maximum is reached",
      "- Deductible: met ($0 remaining)\n- Coinsurance: 20%\n- OOP maximum remaining: $120.00",
      [V(2026, [Line("Physical therapy, 8 sessions", 1450.00, 800.00), Line("Massage therapy (plan exclusion)", 95.00, 95.00, "noncovered")], when="June 2026")],
      Plan(coinsurance=.2, accum={2026: dict(ded_ind=0, oop_ind=120)}), Q,
      mistakes=["noncovered_under_oop", "noncovered_coinsurance", "ignore_oop_cap"]),
 make("t05", "Copay line and a $0-allowed bundled line", "copay only on the copay service; a $0-allowed line costs nothing",
      "- Deductible: met ($0 remaining)\n- Coinsurance: 10%\n- Copay for office visits: $35.00\n- OOP maximum remaining: $3,000.00",
      [V(2026, [Line("Primary care office visit", 240.00, 128.00, "copay"), Line("Blood draw (remark: included in another service)", 25.00, 0.00), Line("Rapid strep test", 64.00, 21.40)], when="February 2, 2026")],
      Plan(coinsurance=.1, copay=35, accum={2026: dict(ded_ind=0, oop_ind=3000)}), Q,
      mistakes=["copay_plus_coins", "zero_allowed_billed", "copay_every_line"]),
 make("t06", "Embedded family deductible", "the family deductible remaining is smaller than the individual one and binds first",
      "- Family plan with an EMBEDDED deductible: each person's deductible is satisfied when EITHER their individual deductible OR the family deductible is met.\n- This patient's individual deductible remaining: $1,200.00\n- Family deductible remaining: $350.00\n- Coinsurance: 20%\n- Individual OOP maximum remaining: $4,000.00; family OOP maximum remaining: $2,500.00 (also embedded)",
      [V(2026, [Line("Outpatient surgery, facility", 3900.00, 980.00), Line("Pathology", 410.00, 145.00)], when="July 21, 2026")],
      Plan(coinsurance=.2, accum={2026: dict(ded_ind=1200, ded_fam=350, oop_ind=4000, oop_fam=2500)}), Q,
      mistakes=["individual_ded_only"]),
 make("t07", "Surprise bill at an in-network hospital", "federal No Surprises Act: in-network cost-sharing on the recognized amount, no balance billing",
      "- Deductible: met ($0 remaining)\n- In-network coinsurance: 20%\n- Out-of-network coinsurance: 50% of the plan recognized amount; under the plan contract, out-of-network providers may bill the patient the difference between their charge and that amount\n- OOP maximum remaining: $6,000.00",
      [V(2026, [Line("Hospital facility, scheduled surgery (in-network hospital)", 18500.00, 4000.00), Line("Anesthesiologist (out-of-network, working at the in-network hospital)", 3200.00, 1150.00, oon=True, nsa=True)], when="August 3, 2026")],
      Plan(coinsurance=.2, oon_coinsurance=.5, accum={2026: dict(ded_ind=0, oop_ind=6000)}),
      "The anesthesiologist's statement says \"balance due from patient: $2,050.00\". The patient did not sign any notice-and-consent waiver. The plan is a US group health plan subject to federal law. Under federal law and this plan, how much does the patient owe in total for these services?",
      mistakes=["nsa_ignored", "nsa_oon_coins"]),
 make("t08", "Deductible resets on January 1", "accumulators reset at the plan-year boundary",
      "- Plan year = calendar year. Deductible $500.00 per year; no deductible carryover provision.\n- As of December 27, 2025: deductible remaining $200.00; OOP maximum remaining $2,800.00\n- On January 1, 2026 the deductible and the OOP maximum reset in full: deductible remaining $500.00; OOP maximum remaining $4,000.00\n- Coinsurance: 20%",
      [V(2025, [Line("Urgent care, laceration repair", 690.00, 450.00)], when="December 28, 2025"), V(2026, [Line("Follow-up ultrasound", 520.00, 300.00)], when="January 6, 2026")],
      Plan(coinsurance=.2, accum={2025: dict(ded_ind=200, oop_ind=2800), 2026: dict(ded_ind=500, oop_ind=4000)}), Q,
      mistakes=["no_year_reset"]),
 make("t09", "ER copay waived on admission, minus upfront payment", "the ER copay is waived when admitted, and the upfront payment must be subtracted",
      "- ER copay: $300.00, WAIVED if the patient is admitted to the hospital; if waived, the ER service is paid under Deductible/Coinsurance instead\n- Deductible remaining: $400.00\n- Coinsurance: 20%\n- OOP maximum remaining: $5,000.00",
      [V(2026, [Line("Emergency room, facility", 6400.00, 2100.00, "er_copay"), Line("Inpatient stay, 2 days", 11800.00, 3600.00)], admitted=True, when="September 14, 2026")],
      Plan(coinsurance=.2, copay=300, accum={2026: dict(ded_ind=400, oop_ind=5000)}),
      "At ER registration the hospital collected $300.00 from the patient. How much does the patient STILL owe after that payment?", prior=300.0,
      mistakes=["er_copay_not_waived", "er_copay_plus_ded", "forget_prior_payment"]),
 make("t10", "Preventive visit with diagnostic add-ons", "ACA preventive services are $0, but same-day diagnostic services are cost-shared",
      "- In-network preventive services (ACA preventive-care list): $0, no copay, deductible does not apply\n- Copay for a problem-focused office visit: $30.00\n- Deductible remaining: $1,000.00\n- Coinsurance: 20%\n- OOP maximum remaining: $5,000.00",
      [V(2026, [Line("Annual preventive physical", 310.00, 210.00, "preventive"), Line("Problem-focused visit, same day (new knee pain)", 190.00, 115.00, "copay"), Line("Hemoglobin A1c (diagnostic, ordered for symptoms)", 68.00, 42.00), Line("Lipid panel (routine screening)", 55.00, 18.00, "preventive")], when="October 6, 2026")],
      Plan(coinsurance=.2, copay=30, accum={2026: dict(ded_ind=1000, oop_ind=5000)}), Q,
      mistakes=["preventive_cost_shared", "preventive_absorbs_visit"]),
]

CORE = TASKS
from .expert import EXPERT, CONTROLS  # noqa: E402
ALL = CORE + EXPERT + CONTROLS

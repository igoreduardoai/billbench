"""Deterministic patient-responsibility engine (ground truth for BillBench).

No LLM is involved. Every task answer is computed here and, separately, hand-checked
in tests/test_engine.py with literal arithmetic.

Cost-sharing rules implemented (all stated in each task prompt):
- In-network covered services are priced at the plan's ALLOWED amount; billed minus
  allowed is a contractual write-off the patient never owes.
- kind="copay": patient pays the flat copay (capped at the allowed amount);
  the deductible does not apply to that service.
- kind="er_copay": like "copay", but the copay is waived if the patient is admitted;
  then the service falls back to deductible + coinsurance.
- kind="ded_coins": deductible first, then coinsurance on the rest.
- kind="preventive": $0 (ACA preventive care, in-network).
- kind="noncovered": owed in full at the stated price; does not count toward the
  deductible or the out-of-pocket (OOP) maximum, and is NOT capped by it.
- Copays, deductible and coinsurance all count toward the OOP maximum; once it is
  reached, covered cost-sharing is $0 for the rest of the plan year.
- Embedded family deductible/OOP: the binding remaining amount is the smaller of the
  individual and family remaining amounts.
- Accumulators reset on the plan-year start (calendar year unless stated).
- No Surprises Act (nsa=True): an out-of-network provider at an in-network facility
  (e.g. anesthesiology) is cost-shared at IN-NETWORK rates on the plan's recognized
  amount, and the provider may not balance-bill.
- prior_payments are subtracted at the end ("how much is still owed").

`mistake` lets us simulate one named, common error so the grader can attribute a
wrong model answer to a specific failure mode (see billbench/failure_modes.py).
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

def D(x):
    return Decimal(str(x))

def cents(x):
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@dataclass
class Line:
    desc: str
    billed: float
    allowed: float
    kind: str = "ded_coins"      # copay | er_copay | ded_coins | preventive | noncovered
    oon: bool = False             # out-of-network provider
    nsa: bool = False             # No Surprises Act protection applies

@dataclass
class Visit:
    year: int
    lines: list
    admitted: bool = False

@dataclass
class Plan:
    coinsurance: float
    copay: float = 0.0
    oon_coinsurance: float = 0.5
    # per plan year: {"ded_ind":..,"ded_fam":..,"oop_ind":..,"oop_fam":..} remaining at the start
    accum: dict = field(default_factory=dict)

MISTAKES = {
    "billed_not_allowed": "prices services at the billed amount instead of the plan-allowed amount",
    "ignore_oop_cap": "ignores the out-of-pocket maximum",
    "noncovered_under_oop": "caps non-covered services under the OOP maximum",
    "noncovered_coinsurance": "applies coinsurance to a non-covered service instead of the full price",
    "copay_plus_coins": "adds coinsurance (or deductible) on top of a copay service",
    "copay_every_line": "charges the copay on every line instead of once",
    "zero_allowed_billed": "charges the billed amount on a $0-allowed (bundled) line",
    "individual_ded_only": "uses the individual deductible and ignores the embedded family deductible",
    "nsa_ignored": "applies out-of-network coinsurance and balance billing despite No Surprises Act protection",
    "nsa_oon_coins": "applies out-of-network coinsurance on the recognized amount (no balance bill) despite the No Surprises Act",
    "no_year_reset": "carries deductible/OOP accumulators across the plan-year reset",
    "er_copay_not_waived": "charges the ER copay even though the patient was admitted",
    "er_copay_plus_ded": "charges the ER copay and also deductible/coinsurance on the ER line",
    "forget_prior_payment": "forgets to subtract what the patient already paid",
    "preventive_cost_shared": "applies cost-sharing to an ACA preventive service",
    "preventive_absorbs_visit": "treats every service on a preventive visit as free",
}

def compute(visits, plan, prior_payments=0.0, mistake=None):
    if mistake is not None and mistake not in MISTAKES:
        raise ValueError(mistake)
    total = Decimal("0")
    years = {}
    first_year = min(v.year for v in visits)
    for v in visits:
        key = first_year if mistake == "no_year_reset" else v.year
        if key not in years:
            a = plan.accum[key]
            ded = D(a["ded_ind"]); oop = D(a["oop_ind"])
            if a.get("ded_fam") is not None and mistake != "individual_ded_only":
                ded = min(ded, D(a["ded_fam"]))
            if a.get("oop_fam") is not None:
                oop = min(oop, D(a["oop_fam"]))
            years[key] = {"ded": ded, "oop": oop}
        acc = years[key]
        copay_used = False
        for ln in v.lines:
            allowed = D(ln.billed) if mistake == "billed_not_allowed" else D(ln.allowed)
            if ln.allowed == 0 and mistake == "zero_allowed_billed":
                allowed = D(ln.billed)
            coins = D(plan.coinsurance)
            balance = Decimal("0")
            if ln.oon and (not ln.nsa or mistake in ("nsa_ignored", "nsa_oon_coins")):
                coins = D(plan.oon_coinsurance)
                if mistake == "nsa_ignored" or not ln.nsa:
                    balance = D(ln.billed) - D(ln.allowed)
            kind = ln.kind
            if kind == "er_copay":
                if v.admitted and mistake not in ("er_copay_not_waived", "er_copay_plus_ded"):
                    kind = "ded_coins"
                else:
                    kind = "copay"
            if kind == "preventive" and mistake == "preventive_cost_shared":
                kind = "ded_coins"
            if kind != "preventive" and mistake == "preventive_absorbs_visit" and any(l.kind == "preventive" for l in v.lines):
                kind = "preventive"
            if kind == "noncovered":
                if mistake == "noncovered_coinsurance":
                    owe = allowed * coins
                    owe = min(owe, acc["oop"]); acc["oop"] -= owe
                elif mistake == "noncovered_under_oop":
                    owe = min(allowed, acc["oop"]); acc["oop"] -= owe
                else:
                    owe = allowed
            elif kind == "preventive":
                owe = Decimal("0")
            else:
                if kind == "copay":
                    if copay_used and mistake != "copay_every_line":
                        owe = Decimal("0")
                        rest = Decimal("0") if mistake != "copay_plus_coins" else allowed
                    else:
                        owe = min(D(plan.copay), allowed); copay_used = True
                        rest = allowed - owe if mistake in ("copay_plus_coins", "er_copay_plus_ded") else Decimal("0")
                    if rest:
                        d = min(acc["ded"], rest); acc["ded"] -= d; owe += d + (rest - d) * coins
                else:
                    if mistake == "copay_every_line" and plan.copay and allowed > 0:
                        c = min(D(plan.copay), allowed)
                        owe = c; rest = allowed - c
                    else:
                        owe = Decimal("0"); rest = allowed
                    d = min(acc["ded"], rest); acc["ded"] -= d
                    owe += d + (rest - d) * coins
                if mistake != "ignore_oop_cap":
                    owe = min(owe, acc["oop"])
                acc["oop"] -= owe
            total += cents(owe) + cents(balance)
    if mistake != "forget_prior_payment":
        total -= D(prior_payments)
    return cents(total)

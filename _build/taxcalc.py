"""Worked state-tax examples for the retirement-taxes pages.

Uses Retirology's own tax engines (the private app repo, checked out next to
this one) so the website shows exactly what the app would compute. Mirrors
the drawdown simulator's per-year tax step in `core/calculators.py`:
provisional-income Social Security taxation, the 2026 standard deduction with
the 65+ amounts and the 2025-2028 senior deduction, then the state engine fed
each person's age and retirement income by kind.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_BACKEND = Path(__file__).resolve().parents[2] / "Retirology_App" / "backend"
sys.path.insert(0, str(APP_BACKEND))

from retirology.core import state_tax, tax_engine  # noqa: E402

YEAR = 2026
FED = tax_engine.DEFAULT_ENGINE
STATE = state_tax.DEFAULT_STATE_ENGINE

# Each person: age plus income by kind (the state engine's kinds).
# plan = 401(k)/403(b), ira = IRA withdrawals, conversion = Roth conversions,
# pension, ss = gross Social Security. `gains` = qualified dividends + LTCG.
EXAMPLES = [
    {
        "key": "couple67",
        "title": "Retired couple, both 67",
        "status": "mfj",
        "people": [
            {"age": 67, "ss": 28000, "ira": 20000},
            {"age": 67, "ss": 20000, "plan": 20000},
        ],
        "gains": 10000,
        "describe": "$48,000 of Social Security, $40,000 drawn from IRAs and 401(k)s, and $10,000 of qualified dividends",
    },
    {
        "key": "single70",
        "title": "Single retiree, 70",
        "status": "single",
        "people": [{"age": 70, "ss": 30000, "pension": 25000, "ira": 15000}],
        "gains": 0,
        "describe": "$30,000 of Social Security, a $25,000 pension and $15,000 of IRA withdrawals",
    },
    {
        "key": "early56",
        "title": "Early-retired couple, both 56, converting to Roth",
        "status": "mfj",
        "people": [
            {"age": 56, "conversion": 30000},
            {"age": 56, "conversion": 30000},
        ],
        "gains": 20000,
        "describe": "a $60,000 Roth conversion and $20,000 of long-term gains and qualified dividends, living on savings",
    },
]

KINDS = ("plan", "ira", "conversion", "pension")


def _taxable_ss(other_agi: float, ss: float, status: str) -> float:
    if ss <= 0:
        return 0.0
    t1, t2 = tax_engine.ss_taxation_thresholds(status)
    pi = other_agi + 0.5 * ss
    if pi > t2:
        base = 0.85 * (pi - t2) + min(0.5 * (t2 - t1), 0.5 * ss)
    elif pi > t1:
        base = 0.5 * (pi - t1)
    else:
        base = 0.0
    return min(base, 0.85 * ss)


def compute(example: dict, state_code: str) -> dict:
    status = example["status"]
    people = example["people"]
    gains = float(example.get("gains", 0))
    ordinary = sum(float(p.get(k, 0)) for p in people for k in KINDS)
    ss = sum(float(p.get("ss", 0)) for p in people)
    taxable_ss = _taxable_ss(ordinary + gains, ss, status)
    agi = ordinary + gains + taxable_ss

    n65 = sum(1 for p in people if p["age"] >= 65)
    std = FED.standard_deduction(status, YEAR) + tax_engine.additional_std_deduction_65(status, n65)
    senior = tax_engine.senior_deduction(n65, agi, YEAR, joint_return=(status == "mfj"))
    deduction = std + senior
    taxable_ord = max(0.0, ordinary + taxable_ss - deduction)
    taxable_gains = max(0.0, gains - max(0.0, deduction - (ordinary + taxable_ss)))
    fed_tax = FED.federal_income_tax(taxable_ord, status, YEAR) + FED.ltcg_tax(
        taxable_ord, taxable_gains, status, YEAR
    )

    state_people = [{
        "age": p["age"],
        **{k: float(p.get(k, 0)) for k in KINDS},
        "ss": float(p.get("ss", 0)),
    } for p in people]
    st = STATE.state_income_tax(
        gross_state_income=agi,
        state_code=state_code,
        filing_status=status,
        ss_income_in_gross=taxable_ss,
        year=YEAR,
        people=state_people,
        agi=agi,
        ss_gross=ss,
        capital_gains=gains,
        investment_income=gains,
        federal_deduction=std,
        federal_senior_deduction=senior,
        federal_tax=fed_tax,
    )
    st += STATE.state_capital_gains_tax(gains, state_code, status, year=YEAR)
    total_income = ordinary + gains + ss
    return {
        "state_tax": round(st),
        "total_income": total_income,
        "rate": st / total_income if total_income else 0.0,
        "federal_tax": round(fed_tax),
    }

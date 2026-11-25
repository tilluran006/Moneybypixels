"""Money calculators. Every number on a slide must come from here (or from an
official source quoted in the post), never typed by hand.

All functions are pure and return plain dicts/lists so build scripts can put
the results straight into a post spec.
"""
from __future__ import annotations


def card_minimum_due(balance: float, monthly_rate: float = 0.035, min_pct: float = 0.05,
                     min_floor: float = 200, max_months: int = 1200) -> dict:
    """Pay only the minimum due each month on a credit card, no new spends.
    Each month: interest is added, then minimum = max(min_pct * balance, min_floor)."""
    b = float(balance)
    bal, paid_cum, interest_cum, pays = [b], [0.0], [0.0], []
    paid = interest = 0.0
    while b > 0.5 and len(pays) < max_months:
        i = b * monthly_rate
        b += i
        interest += i
        p = min(max(min_pct * b, min_floor), b)
        b -= p
        paid += p
        pays.append(p)
        bal.append(b)
        paid_cum.append(paid)
        interest_cum.append(interest)
    return {"months": len(pays), "interest": interest, "total_paid": paid,
            "balance": bal, "paid_cum": paid_cum, "interest_cum": interest_cum, "payments": pays}


def fixed_payment(balance: float, monthly_rate: float, payment: float, max_months: int = 1200) -> dict:
    """Pay a fixed amount every month until cleared (credit card or any revolving debt)."""
    b = float(balance)
    bal, paid_cum = [b], [0.0]
    paid = interest = 0.0
    m = 0
    while b > 0.5 and m < max_months:
        i = b * monthly_rate
        b += i
        interest += i
        if payment <= i:
            raise ValueError("payment does not cover interest; debt never clears")
        p = min(payment, b)
        b -= p
        paid += p
        m += 1
        bal.append(b)
        paid_cum.append(paid)
    return {"months": m, "interest": interest, "total_paid": paid, "balance": bal, "paid_cum": paid_cum}


def emi(principal: float, annual_rate: float, months: int) -> dict:
    """Standard reducing-balance EMI. annual_rate as a fraction (0.09 for 9%)."""
    r = annual_rate / 12
    e = principal / months if r == 0 else principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = e * months
    # yearly split of interest vs principal
    b, yearly = principal, []
    yi = yp = 0.0
    for k in range(1, months + 1):
        i = b * r
        pr = e - i
        b -= pr
        yi += i
        yp += pr
        if k % 12 == 0 or k == months:
            yearly.append({"year": (k + 11) // 12, "interest": yi, "principal": yp, "balance": max(b, 0)})
            yi = yp = 0.0
    return {"emi": e, "total": total, "interest": total - principal, "yearly": yearly}


def future_cost(amount: float, inflation: float, years: int) -> float:
    """What costs `amount` today will cost this much after `years` at `inflation`."""
    return amount * (1 + inflation) ** years


def present_value(amount: float, inflation: float, years: int) -> float:
    """What `amount` received after `years` is worth in today's money."""
    return amount / (1 + inflation) ** years


def sip_future_value(monthly: float, annual_return: float, years: int) -> dict:
    """Monthly investment at the start of each month, compounded monthly.
    Illustration only: always label the return as an assumption, never a promise."""
    r = annual_return / 12
    n = years * 12
    fv = monthly * n if r == 0 else monthly * ((1 + r) ** n - 1) / r * (1 + r)
    return {"invested": monthly * n, "value": fv, "gain": fv - monthly * n}


def real_return(nominal: float, inflation: float, tax_rate: float = 0.0) -> float:
    """Post-tax return after inflation, as a fraction. FD at 7%, 30% tax, 5% inflation -> about -0.1%."""
    post_tax = nominal * (1 - tax_rate)
    return (1 + post_tax) / (1 + inflation) - 1


def no_cost_emi_true_cost(price: float, months: int, processing_fee: float = 0.0,
                          gst_on_fee: float = 0.18, discount_forgone: float = 0.0) -> dict:
    """'No-cost' EMI: the interest is usually offset by a discount, but the processing
    fee (plus GST) and any cash discount you give up are real extra costs."""
    fee = processing_fee * (1 + gst_on_fee)
    extra = fee + discount_forgone
    return {"monthly": price / months, "extra_cost": extra, "effective_price": price + extra}

"""Indian number formatting. Every rupee figure on a slide goes through these."""


def group_in(n: int) -> str:
    """12345678 -> '1,23,45,678' (Indian digit grouping)."""
    neg = n < 0
    s = str(abs(int(n)))
    if len(s) <= 3:
        out = s
    else:
        last3, rest = s[-3:], s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        out = ",".join(parts + [last3])
    return ("-" if neg else "") + out


def inr(x: float) -> str:
    """₹ with Indian grouping, rounded to the rupee: inr(149095.2) -> '₹1,49,095'."""
    return "₹" + group_in(round(x))


def lakh_crore(x: float, digits: int = 2) -> str:
    """Spoken form for headlines: 149095 -> '₹1.49 lakh', 1.2e7 -> '₹1.2 crore'."""
    if abs(x) >= 1e7:
        v, unit = x / 1e7, "crore"
    elif abs(x) >= 1e5:
        v, unit = x / 1e5, "lakh"
    else:
        return inr(x)
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return f"₹{s} {unit}"


def pct(x: float, digits: int = 0) -> str:
    """0.873 -> '87%'. Pass a fraction."""
    s = f"{x * 100:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s + "%"


def years_months(months: int) -> str:
    """185 -> '15 years 5 months'."""
    y, m = divmod(int(months), 12)
    parts = []
    if y:
        parts.append(f"{y} year{'s' if y != 1 else ''}")
    if m:
        parts.append(f"{m} month{'s' if m != 1 else ''}")
    return " ".join(parts) or "0 months"

"""Build script for post 1. Every number comes from studio.calc."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from studio.calc import card_minimum_due, fixed_payment
from studio.fmt import inr, lakh_crore, pct

BAL, RATE = 50000, 0.035
mn = card_minimum_due(BAL, RATE)
fx = fixed_payment(BAL, RATE, 5000)
b, tp = mn["balance"], mn["paid_cum"]
y1_paid, y1_debt = tp[12], BAL - b[12]
y1_int = y1_paid - y1_debt
saved = 1 - fx["interest"] / mn["interest"]
assert mn["months"] == 185 and round(mn["interest"]) == 99095

spec = {
  "slug": "cc-two-year-trap", "date": "2026-11-25", "type": "educational", "topic_id": "cc-two-year-trap",
  "verdict_style": "night",
  "title": f"The Two-Year Trap: how a ₹50,000 credit card bill becomes {lakh_crore(mn['total_paid'])}",
  "footer": ["Assumes ₹50,000 balance, 3.5% interest/month, minimum due 5% of balance (min ₹200), no new spends. Excludes GST and late fees.",
             "Source: MoneyByPixels calculation · Educational, not financial advice."],
  "slides": [
    {"t": "cover", "style": "paper", "kicker": "Credit cards", "hero": inr(tp[24]),
     "headline": f"Two years of minimum payments. You've repaid more than you borrowed, and still owe [[{inr(b[24])}]].",
     "deck": "On a ₹50,000 credit-card bill."},
    {"t": "context", "kicker": "Why it happens", "headline": "How a sensible-looking payment becomes a 15-year habit",
     "body": "The minimum due is 5% of what you owe. Interest is 3.5% of what you owe. So [[most of each early payment is swallowed by interest]] before it touches the debt.",
     "figure": "1.5%", "figure_label": "of the balance is all that actually cuts the debt each month (5% − 3.5%)"},
    {"t": "split", "kicker": "Year one", "headline": f"Of {inr(y1_paid)} paid in year one, {inr(y1_int)} was interest",
     "subtitle": "Where your first 12 minimum payments went",
     "parts": [{"label": f"Interest · {pct(y1_int/y1_paid)}", "value": y1_int, "display": inr(y1_int), "highlight": True},
               {"label": f"Debt reduced · {pct(y1_debt/y1_paid)}", "value": y1_debt, "display": inr(y1_debt)}]},
    {"t": "line", "kicker": "The crossover", "headline": "By month 24, you've paid more than you borrowed",
     "subtitle": "₹, first 5 years of minimum payments", "y_max": 100000,
     "y_ref": [50000, "₹50,000 borrowed"],
     "series": [{"name": "Total paid", "style": "main", "points": [[m, tp[m]] for m in range(61)]},
                {"name": "Still owed", "style": "compare", "points": [[m, b[m]] for m in range(61)]}],
     "annotations": [{"x": 24, "y": tp[24], "text": f"Paid {inr(tp[24])}", "color": "#BD3F0E"},
                     {"x": 24, "y": b[24], "text": f"Still owed {inr(b[24])}", "color": "#17405F", "dx": -30, "dy": 62}],
     "x_ticks": [[0, "0"], [12, "1 yr"], [24, "2 yrs"], [36, "3 yrs"], [48, "4 yrs"], [60, "5 yrs"]]},
    {"t": "timeline", "kicker": "The long tail", "headline": "What's still owed, year by year",
     "milestones": [{"label": "Year 1", "value": inr(b[12]), "size": b[12]/BAL},
                    {"label": "Year 2", "value": inr(b[24]), "size": b[24]/BAL},
                    {"label": "Year 5", "value": inr(b[60]), "size": b[60]/BAL},
                    {"label": "Year 10", "value": inr(b[120]), "size": b[120]/BAL},
                    {"label": f"Month {mn['months']}", "value": "₹0", "size": 0, "style": "compare"}],
     "body": "As the balance falls, so does the minimum due, so the last few thousand rupees take years."},
    {"t": "receipt", "kicker": "The other ending", "title": "IF YOU'D PAID ₹5,000 A MONTH",
     "lines": [["Amount borrowed", inr(BAL)], ["Months of payments", str(fx["months"])], ["Interest charged", inr(fx["interest"])]],
     "total": ["TOTAL PAID", inr(fx["total_paid"])], "stamp": f"PAID OFF · MONTH {fx['months']}",
     "after": f"Versus {inr(mn['total_paid'])} over {mn['months']} months on the minimum."},
    {"t": "verdict", "statement": f"Same debt. About {{{{{pct(saved)} less interest}}}}. {mn['months'] - fx['months']} fewer months.",
     "action": "Every rupee above the minimum goes straight at the balance."},
    {"t": "sources", "sources": ["MoneyByPixels month-by-month calculation (method below).",
                                 "Your card's own terms. Interest rates and minimum-due rules vary by issuer, so check your statement."],
     "method": "Each month: balance grows by 3.5% interest, then the minimum due (5% of balance, at least ₹200) is paid. No new spending. GST on interest and late fees are excluded, so real costs are higher.",
     "save": "Save this before your next statement."}
  ],
  "caption": f"""You paid back {inr(tp[24])} on a ₹50,000 card bill. And you still owe {inr(b[24])}.

That's what 2 years of "minimum due only" looks like. The minimum is 5% of what you owe, but interest eats 3.5% of it, so only about 1.5% actually cuts the debt each month.

Keep paying only the minimum and it takes {mn['months']} months (about 15 years) and {inr(mn['interest'])} in interest to clear.
Pay ₹5,000 a month instead: {fx['months']} months, {inr(fx['interest'])} interest. About {pct(saved)} less.

Send this to the friend who "just pays the minimum." 📩
Save it for your next statement.

Assumptions: 3.5% monthly interest, 5% minimum due (min ₹200), no new spends. Excludes GST and late fees. Your card's terms may differ.
Educational, not financial advice.""",
  "hashtags": ["creditcard", "personalfinanceindia", "moneytips"],
  "alt_text": f"Eight-slide explainer. Paying only the minimum due on a ₹50,000 credit card bill at 3.5% monthly interest: after 2 years you have paid {inr(tp[24])} and still owe {inr(b[24])}; it takes {mn['months']} months and {inr(mn['interest'])} interest to clear. Paying ₹5,000 a month clears it in {fx['months']} months with {inr(fx['interest'])} interest.",
  "source_links": [],
  "checklist": ["Card interest of 3.5%/month is typical but varies by issuer; the caption says so"]
}
# ---- reel (Monday). One square always means one unit: ₹1,000, then ₹1, then one month.
y1_share = round(100 * y1_int / y1_paid)
spec["reel"] = {
  "bpm": 84,
  "footer": "Assumes ₹50,000 balance, 3.5%/month interest, minimum due 5% (min ₹200), no new spends. Educational, not financial advice.",
  "scenes": [
    {"t": "hook", "bars": 1, "question": "Paying only the minimum due?", "value": round(tp[24]), "format": "inr",
     "caption": f"paid on a ₹50,000 bill.|You still owe [[{inr(b[24])}]]."},
    {"t": "units", "bars": 1, "headline": "Two years in,|this much is still left:", "value": round(b[24]), "format": "inr",
     "highlight": True, "n": 50, "k": round(b[24] / 1000), "cols": 10, "unit": "Each square = ₹1,000 · ■ still owed"},
    {"t": "fill", "bars": 1.5, "headline": "Pay only the minimum:", "counter": "Each square = one month · month {i}", "n": mn["months"],
     "style": "main", "meter": {"label": "Still owed", "values": [round(v) for v in b]},
     "final": f"15 years, 5 months. {{{{{inr(mn['interest'])}}}}} interest."},
    {"t": "fill", "bars": 1.5, "headline": "Pay ₹5,000 a month instead?", "n": fx["months"], "style": "compare",
     "meter": {"label": "Still owed", "values": [round(v) for v in fx["balance"]]},
     "big": "#<span style='font-size:90px'> months</span>", "after": f"Interest: <b style='color:#17405F'>{inr(fx['interest'])}</b> instead of <s>{inr(mn['interest'])}</s>"},
    {"t": "verdict", "bars": 1, "kicker": "The verdict", "statement": "Same debt.|{{#% less interest.}}", "value": round(100 * saved),
     "cta": "Full breakdown in our carousel →"}
  ],
  "caption": f"""Paid back {inr(tp[24])} on a ₹50,000 card bill… and still owe {inr(b[24])}.

Every square is money or time. Watch what "minimum due only" really costs, then the 13-month way out.

Full breakdown in our carousel. Send this to the friend who just pays the minimum 📩
Educational, not financial advice."""
}
Path(__file__).with_name("spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False))
print("spec written")

# MoneyByPixels studio

Code that turns a money story into a finished Instagram carousel for **MoneyByPixels**: India's money, explained in charts.

- `studio/calc.py`: money calculators (credit card minimum due, fixed payments, EMI, inflation, SIP illustration, real return, no-cost EMI). Every number on a slide comes from here.
- `studio/fmt.py`: Indian number formatting (₹1,49,095, ₹1.49 lakh).
- `studio/render.py`: renders `posts/<dir>/spec.json` into 1080×1350 PNG slides, `caption.md` and `contact_sheet.png`, and refuses specs that break the brand rules.
- `studio/plan.py`: today's plan (news or educational rotation, next topic, verdict style) and the post log.
- `content/topics.json`: educational backlog. `content/feeds.json`: news sources and the story filter.
- `posts/`: one folder per post, each with its `build.py`, `spec.json`, slides and caption.
- `RUNBOOK.md`: the daily 5pm routine. `BRAND.md`: the visual rules.

## Make a post by hand

```bash
npm install
pip install playwright --break-system-packages   # if missing
python3 -m studio.plan
python3 posts/<dir>/build.py
python3 -m studio.render posts/<dir>
```

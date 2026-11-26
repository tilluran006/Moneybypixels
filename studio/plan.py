"""Decide what today's run should make, and keep the post log.

    python3 -m studio.plan                      # today's plan as JSON
    python3 -m studio.plan record <post_dir>    # log a rendered carousel
    python3 -m studio.plan record-reel <post_dir>  # log a rendered reel
    python3 -m studio.plan approve <slug>       # mark as posted

Weekly schedule (IST):
- Wednesday: explainer carousel
- Friday:    news carousel (falls back to an explainer if nothing qualifies)
- Sunday:    explainer carousel
- Monday:    reel, cut from an explainer carousel of the past week
- Other days: nothing

Calendar override: if content/calendar.json has an event for this week that the
Friday news slot would miss (it lands on Wed or Sun, or on Sat/Mon-Tue right
before a posting day), today's carousel becomes the week's news post instead and
Friday becomes an explainer. One news post per week.

The verdict slide alternates night / paper from one carousel to the next.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "state" / "log.json"
TOPICS = ROOT / "content" / "topics.json"
CAL = ROOT / "content" / "calendar.json"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
POST_DAYS = {2: "wednesday", 4: "friday", 6: "sunday"}   # Mon=0
REEL_DAY = 0


def load_log() -> dict:
    return json.loads(LOG.read_text()) if LOG.exists() else {"posts": []}


def save_log(log: dict) -> None:
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")


def week_start(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def events_between(a: dt.date, b: dt.date) -> list[dict]:
    if not CAL.exists():
        return []
    out = []
    for e in json.loads(CAL.read_text())["events"]:
        d = dt.date.fromisoformat(e["date"])
        if a <= d <= b:
            out.append(e)
    return out


def today_plan(today: dt.date | None = None) -> dict:
    today = today or dt.datetime.now(IST).date()
    log = load_log()
    posts = log["posts"]
    carousels = [p for p in posts if p.get("kind", "carousel") == "carousel"]
    wd = today.weekday()

    if wd == REEL_DAY:
        recent = [p for p in carousels if p.get("reel") and
                  (today - dt.date.fromisoformat(p["reel"]["date"])).days <= 6]
        if recent:
            return {"date": today.isoformat(), "kind": "none",
                    "note": f"This week's reel is already made ({recent[-1]['slug']}). Nothing to build today."}
        # explainers from the past 7 days that don't have a reel yet, oldest first
        since = today - dt.timedelta(days=7)
        cands = [p for p in carousels if p["type"] == "educational" and not p.get("reel")
                 and dt.date.fromisoformat(p["date"]) >= since]
        pick = cands[0] if cands else None
        return {"date": today.isoformat(), "kind": "reel", "post": pick,
                "note": None if pick else "No explainer from the past week without a reel: skip today and tell the owner."}

    if wd not in POST_DAYS:
        return {"date": today.isoformat(), "kind": "none", "note": "Not a posting day (Wed, Fri, Sun carousels; Mon reel)."}

    ws = week_start(today)
    news_done = any(p["type"] == "news" and week_start(dt.date.fromisoformat(p["date"])) == ws for p in carousels)
    # events since the previous posting day up to today
    prev = today - dt.timedelta(days=1)
    while prev.weekday() not in POST_DAYS and prev > today - dt.timedelta(days=7):
        prev -= dt.timedelta(days=1)
    recent_events = [e for e in events_between(prev + dt.timedelta(days=1), today) if e.get("news_post")]
    week_events = [e for e in events_between(ws, ws + dt.timedelta(days=6)) if e.get("news_post")]

    if news_done:
        typ, why = "educational", "this week's news post is done"
    elif recent_events:
        typ, why = "news", "scheduled event: " + "; ".join(e["name"] for e in recent_events)
    elif wd == 4:
        # Friday: news unless this week's only event lands on Sunday (let Sunday take it)
        sunday = ws + dt.timedelta(days=6)
        later = [e for e in week_events if dt.date.fromisoformat(e["date"]) > today and dt.date.fromisoformat(e["date"]) <= sunday]
        typ, why = ("educational", "a scheduled event lands before Sunday's post; Sunday takes the news slot") if later else ("news", "Friday news slot")
    else:
        typ, why = "educational", "explainer day"

    last_verdict = carousels[-1]["verdict_style"] if carousels else "paper"
    used = {p.get("topic_id") for p in posts}
    topics = json.loads(TOPICS.read_text())["topics"]
    nxt = next((t for t in topics if t["id"] not in used), None)
    return {
        "date": today.isoformat(),
        "kind": "carousel",
        "type": typ,
        "why": why,
        "events": recent_events,
        "fallback_topic": nxt,
        "verdict_style": "paper" if last_verdict == "night" else "night",
        "cover_style": "night" if typ == "news" else "paper",
        "post_number": len(carousels) + 1,
    }


def record(post_dir: str) -> None:
    spec = json.loads((Path(post_dir) / "spec.json").read_text())
    log = load_log()
    keep = [p for p in log["posts"] if p["slug"] != spec["slug"]]
    old = next((p for p in log["posts"] if p["slug"] == spec["slug"]), {})
    keep.append({"date": spec["date"], "slug": spec["slug"], "kind": "carousel", "type": spec["type"],
                 "verdict_style": spec["verdict_style"], "topic_id": spec.get("topic_id"), "title": spec["title"],
                 "dir": str(Path(post_dir)), "status": old.get("status", "draft"), "reel": old.get("reel")})
    log["posts"] = keep
    save_log(log)


def record_reel(post_dir: str) -> None:
    spec = json.loads((Path(post_dir) / "spec.json").read_text())
    log = load_log()
    for p in log["posts"]:
        if p["slug"] == spec["slug"]:
            p["reel"] = {"date": dt.datetime.now(IST).date().isoformat(), "status": "draft"}
    save_log(log)


def approve(slug: str) -> None:
    log = load_log()
    for p in log["posts"]:
        if p["slug"] == slug:
            p["status"] = "posted"
    save_log(log)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "record":
        record(a[1])
    elif len(a) == 2 and a[0] == "record-reel":
        record_reel(a[1])
    elif len(a) == 2 and a[0] == "approve":
        approve(a[1])
    elif len(a) == 2 and a[0] == "on":   # preview the plan for a date: plan on 2026-12-04
        print(json.dumps(today_plan(dt.date.fromisoformat(a[1])), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(today_plan(), indent=2, ensure_ascii=False))

"""Decide what today's post should be, and record posts once made.

    python3 -m studio.plan            # prints today's plan as JSON
    python3 -m studio.plan record <post_dir>   # log a rendered post
    python3 -m studio.plan approve <slug>      # mark as posted (after you publish)

Rules
- Rotation: news, educational, educational, repeat. A news day with no story
  worth explaining falls back to educational, and news is tried again next day.
- Verdict slide alternates night / paper from one post to the next.
- Educational topics come from content/topics.json in order, skipping used ones.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "state" / "log.json"
TOPICS = ROOT / "content" / "topics.json"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load_log() -> dict:
    return json.loads(LOG.read_text()) if LOG.exists() else {"posts": []}


def today_plan() -> dict:
    log = load_log()
    posts = log["posts"]
    since_news = 0
    for p in reversed(posts):
        if p["type"] == "news":
            break
        since_news += 1
    want_news = bool(posts) and since_news >= 2  # launch with an educational post
    last_verdict = posts[-1]["verdict_style"] if posts else "paper"
    verdict = "paper" if last_verdict == "night" else "night"
    used = {p.get("topic_id") for p in posts}
    topics = json.loads(TOPICS.read_text())["topics"]
    nxt = next((t for t in topics if t["id"] not in used), None)
    return {
        "date": dt.datetime.now(IST).date().isoformat(),
        "post_number": len(posts) + 1,
        "type": "news" if want_news else "educational",
        "fallback_topic": nxt,
        "verdict_style": verdict,
        "cover_style": "night" if want_news else "paper",
    }


def record(post_dir: str) -> None:
    d = Path(post_dir)
    spec = json.loads((d / "spec.json").read_text())
    log = load_log()
    log["posts"] = [p for p in log["posts"] if p["slug"] != spec["slug"]]
    log["posts"].append({"date": spec["date"], "slug": spec["slug"], "type": spec["type"],
                         "verdict_style": spec["verdict_style"], "topic_id": spec.get("topic_id"),
                         "title": spec["title"], "status": "draft"})
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")


def approve(slug: str) -> None:
    log = load_log()
    for p in log["posts"]:
        if p["slug"] == slug:
            p["status"] = "posted"
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "record":
        record(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == "approve":
        approve(sys.argv[2])
    else:
        print(json.dumps(today_plan(), indent=2, ensure_ascii=False))

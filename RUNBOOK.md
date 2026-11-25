# Daily run: one post package for approval

This is what the 5pm scheduled task does every day. It ends with a draft post for the owner to approve; it never publishes to Instagram.

## 0. Setup (every run starts fresh)

```bash
cd <repo>
npm install            # fonts
python3 -c "import playwright" || pip install playwright --break-system-packages
which google-chrome || python3 -m playwright install chromium
python3 -m studio.plan # today's plan: type, topic, verdict style, cover style
```

If a post folder for today's date already exists, stop and report that today's post is already made.

## 1. Decide the story

The plan says `news` or `educational`.

**News day.**
1. Read the feeds in `content/feeds.json` with the web fetch tool: RBI press releases first, then Business Standard Finance. For the blocked sites listed there, use web search with the `search_queries`.
2. Keep only stories from the last 24 hours that pass `score_rule`: they change what a typical person pays, earns or saves, and the change can be shown with a calculation.
3. Pick the single best one. Confirm the key number on an official page (rbi.org.in, pib.gov.in, incometaxindia.gov.in, gst council, npci.org.in, sebi.gov.in). If it cannot be confirmed on an official page, it does not go on a slide.
4. If nothing qualifies, switch to the plan's `fallback_topic` and make an educational post. Say so in the report.

**Educational day.** Use `fallback_topic` from the plan (the next unused topic in `content/topics.json`).

## 2. Write the build script

Create `posts/<YYYY-MM-DD>-<topic-id>/build.py`, modelled on `posts/2026-11-25-cc-two-year-trap/build.py`.

- Every number comes from `studio.calc` (or an official figure quoted with its source). Never type a computed number by hand. Format with `studio.fmt` (`inr`, `lakh_crore`, `pct`).
- Add `assert` lines for the headline numbers so a wrong input fails loudly.
- Set `type`, `topic_id`, and `verdict_style` from the plan. Cover `style` is `night` for news and `paper` for educational.
- 6 to 8 slides. First is `cover`, last is `sources`. Vary the middle using the templates below; don't use the same template twice in a row.
- Footer: line 1 the assumptions, line 2 "Source: … · Educational, not financial advice."
- Caption: hook line with the most surprising number, 2 short paragraphs of explanation, a send prompt ("Send this to the friend who…"), a save prompt, the assumptions, and "Educational, not financial advice." One emoji at most.
- Hashtags: 3, never more than 5. The searchable words belong in the caption text.
- Fill `alt_text`, `source_links` (official URLs used) and `checklist` (anything the owner should double-check).

Templates (fields in `studio/render.py`):

| t | use for |
|---|---|
| cover | slide 1. Hero number + headline + deck |
| context | the real-world problem; optional margin figure |
| stack | arithmetic walk-through (value, operator, label rows) |
| split | part-to-whole in one bar |
| bars | 2 to 6 values, starts at zero |
| line | change over time; main series orange, comparison dashed blue |
| timeline | 3 to 6 milestones |
| receipt | itemised totals, statements, bills |
| table | two options side by side |
| verdict | one-sentence takeaway (style comes from the plan) |
| sources | numbered sources, method box, save prompt |

Copy markup: `[[words]]` highlighter band, `{{words}}` orange accent.

## 3. Render and check

```bash
python3 posts/<dir>/build.py
python3 -m studio.render posts/<dir>
```

The renderer refuses specs that break the rules (slide count, cover style, footer, word limits). Then open `contact_sheet.png` and look at it: no overlapping text, nothing cut off, numbers match the build output. Fix and re-render until clean.

## 4. Record and deliver

```bash
python3 -m studio.plan record posts/<dir>
git add -A && git commit -m "Draft post: <title>" && git push
```

If the push is refused, say so in the report and include the new `state/log.json` entry so it can be added by hand.

Send the owner: the slide PNGs in order, `contact_sheet.png`, and `caption.md`. Message: the post title, news or educational (and why, if it fell back), the official sources checked, and anything in the checklist.

## 5. After the owner posts

They reply "posted <slug>" (or run `python3 -m studio.plan approve <slug>`), which marks it posted in the log.

## Never

- Publish to Instagram, or message anyone but the owner.
- Name a stock, fund, broker or crypto as a pick. SEBI rules: the page stays educational.
- Use a number that was not computed in the build script or confirmed on an official page.
- Use AI-generated photos of real people or real events.

"""Render a post spec (posts/<slug>/spec.json) into 1080x1350 PNG slides,
a caption file and a contact sheet.

    python3 -m studio.render posts/2026-11-26-two-year-trap

Text markup inside any copy field:
    [[words]]  -> highlighter band (Marker) behind the words
    {{words}}  -> accent colour (Signal orange on Paper, Ember on Night)
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "node_modules" / "@fontsource"

# ---- Ledger Paper tokens (see BRAND.md) ----
P = dict(paper="#F5EFE3", slip="#FFFCF5", ink="#1B1814", soft="#5C5249", sig="#BD3F0E",
         blue="#17405F", grey="#C2B8AA", marker="#F6DCC2", hair="#D9D0C1")
N = dict(night="#14110E", panel="#2A241F", chalk="#EFE8DB", chalk_soft="#9C9389", ember="#F08A3C",
         ngrey="#4A433C")
BRAND = "MoneyByPixels"
W, H = 1080, 1350
DATA_TYPES = {"context", "stack", "split", "bars", "line", "timeline", "receipt", "table"}


def esc(s: str, accent: str) -> str:
    s = html.escape(str(s))
    s = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span class="mark">{m.group(1)}</span>', s)
    s = re.sub(r"\{\{(.+?)\}\}", lambda m: f'<span style="color:{accent}">{m.group(1)}</span>', s)
    return s


def css() -> str:
    links = "".join(f'<link rel="stylesheet" href="file://{FONTS}/{f}">' for f in [
        "source-serif-4/600.css", "source-sans-3/400.css", "source-sans-3/600.css",
        "ibm-plex-mono/400.css", "ibm-plex-mono/500.css"])
    return links + f"""<meta charset="utf-8"><style>
html,body{{margin:0}}*{{box-sizing:border-box}}
.s{{position:relative;width:{W}px;height:{H}px;background:{P['paper']};color:{P['ink']};font-family:'Source Sans 3',sans-serif;overflow:hidden}}
.ab{{position:absolute}}
.serif{{font-family:'Source Serif 4',serif;font-weight:600}}
.mono{{font-family:'IBM Plex Mono',monospace}}
.kick{{font-size:28px;line-height:32px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:{P['sig']}}}
.h2{{font-size:60px;line-height:68px;width:900px}}
.body{{font-size:36px;line-height:48px}}
.mark{{background:{P['marker']};color:{P['ink']};padding:0 6px}}
.foot{{position:absolute;left:90px;top:1176px;width:900px;border-top:2px solid {P['hair']};padding-top:18px;font-size:24px;line-height:32px;color:{P['soft']}}}
</style>"""


def header(n: int, total: int, night: bool = False) -> str:
    sq = N["ember"] if night else P["sig"]
    fg = N["chalk"] if night else P["ink"]
    soft = N["chalk_soft"] if night else P["soft"]
    return (f'<div class="ab" style="left:90px;top:72px;width:18px;height:18px;background:{sq}"></div>'
            f'<div class="ab" style="left:118px;top:64px;font-size:28px;font-weight:600;color:{fg}">{BRAND}</div>'
            f'<div class="ab" style="right:90px;top:64px;font-size:28px;color:{soft}">{n} / {total}</div>')


def footer(lines: list[str]) -> str:
    return '<div class="foot">' + "<br>".join(html.escape(l) for l in lines) + "</div>"


def kick_head(s: dict, a: str, top: int = 210) -> str:
    out = ""
    if s.get("kicker"):
        out += f'<div class="ab kick" style="left:90px;top:150px">{esc(s["kicker"], a)}</div>'
    if s.get("headline"):
        out += f'<div class="ab serif h2" style="left:90px;top:{top}px">{esc(s["headline"], a)}</div>'
    return out


# ---------------- templates ----------------

def t_cover(s, n, tot, spec):
    night = s.get("style", "paper") == "night"
    bg, fg, acc, soft = ((N["night"], N["chalk"], N["ember"], N["chalk_soft"]) if night
                         else (P["paper"], P["ink"], P["sig"], P["soft"]))
    hero_size = s.get("hero_size", 230)
    dateline = s.get("dateline", "")
    return f"""<div class="s" style="background:{bg};color:{fg}">
<div class="ab kick" style="left:90px;top:170px;color:{acc}">{esc(s.get('kicker',''), acc)}</div>
<div class="ab serif" style="left:84px;top:220px;font-size:{hero_size}px;line-height:{hero_size}px;color:{acc};letter-spacing:-.02em;white-space:nowrap">{esc(s['hero'], acc)}</div>
<div class="ab serif" style="left:90px;top:{220 + hero_size + 90}px;width:900px;font-size:{s.get('headline_size',72)}px;line-height:{int(s.get('headline_size',72)*1.11)}px">{esc(s['headline'], acc)}</div>
<div class="ab body" style="left:90px;top:1000px;width:900px;color:{soft}">{esc(s.get('deck',''), acc)}</div>
<div class="ab" style="left:90px;top:1120px;display:flex;align-items:center;gap:12px"><div style="width:18px;height:18px;background:{acc}"></div><span class="serif" style="font-size:32px">{BRAND}</span><span style="font-size:26px;color:{soft};margin-left:12px">{html.escape(dateline)}</span></div>
<div class="ab" style="right:90px;top:1120px;font-size:32px;font-weight:600;color:{acc}">Swipe →</div>
</div>"""


def t_context(s, n, tot, spec):
    a = P["sig"]
    fig = ""
    if s.get("figure"):
        fig = (f'<div class="ab" style="left:706px;top:{s.get("body_top",470)}px;width:284px;border-top:4px solid {a};padding-top:20px">'
               f'<div class="serif" style="font-size:{s.get("figure_size",80)}px;line-height:1.05;color:{a}">{esc(s["figure"], a)}</div>'
               f'<div style="font-size:28px;line-height:36px;color:{P["soft"]};margin-top:12px">{esc(s.get("figure_label",""), a)}</div></div>')
    width = 592 if s.get("figure") else 900
    return f"""<div class="s">{header(n, tot)}{kick_head(s, a)}
<div class="ab body" style="left:90px;top:{s.get('body_top',470)}px;width:{width}px">{esc(s['body'], a)}</div>{fig}</div>"""


def t_stack(s, n, tot, spec):
    a = P["sig"]
    rows = s["rows"]
    out = ""
    y = 420
    for k, r in enumerate(rows):
        last = k == len(rows) - 1
        if last:
            out += f'<div class="ab" style="left:90px;top:{y-24}px;width:900px;height:4px;background:{P["ink"]}"></div>'
        out += (f'<div class="ab serif" style="left:90px;top:{y}px;font-size:72px;line-height:80px;color:{a};width:90px">{html.escape(r.get("op",""))}</div>'
                f'<div class="ab serif" style="left:180px;top:{y}px;width:440px;text-align:right;font-size:72px;line-height:80px">{esc(r["value"], a)}</div>'
                f'<div class="ab" style="left:660px;top:{y+14}px;width:330px;font-size:30px;line-height:38px;color:{P["soft"]}">{esc(r["label"], a)}</div>')
        y += 160 if not last else 0
        if k == len(rows) - 2:
            y += 30
    cap = ""
    if s.get("caption"):
        cap = f'<div class="ab body" style="left:90px;top:{y+130}px;width:900px">{esc(s["caption"], a)}</div>'
    return f'<div class="s">{header(n, tot)}{kick_head(s, a)}{out}{cap}</div>'


def t_split(s, n, tot, spec):
    """Part-to-whole: one 900px bar split into 2-3 labelled parts."""
    a = P["sig"]
    parts = s["parts"]
    tot_v = sum(p["value"] for p in parts)
    x = 90
    bars = labels = ""
    for p in parts:
        w = 900 * p["value"] / tot_v
        col = a if p.get("highlight") else P["grey"]
        bars += f'<div class="ab" style="left:{x:.0f}px;top:560px;width:{w:.0f}px;height:220px;background:{col}"></div>'
        tc = a if p.get("highlight") else P["ink"]
        labels += (f'<div class="ab" style="left:{x:.0f}px;top:810px;width:{max(w-24, 260):.0f}px">'
                   f'<div class="serif" style="font-size:72px;line-height:76px;color:{tc}">{esc(p["display"], a)}</div>'
                   f'<div style="font-size:30px;line-height:38px">{esc(p["label"], a)}</div></div>')
        x += w
    sub = f'<div class="ab" style="left:90px;top:370px;font-size:28px;color:{P["soft"]}">{esc(s.get("subtitle",""), a)}</div>'
    return f'<div class="s">{header(n, tot)}{kick_head(s, a)}{sub}{bars}{labels}</div>'


def t_bars(s, n, tot, spec):
    """Vertical bars (2-6), start at zero, direct labels."""
    a = P["sig"]
    bars = s["bars"]
    vmax = max(b["value"] for b in bars)
    k = len(bars)
    gap = 48 if k <= 3 else 24
    bw = (900 - gap * (k - 1)) / k
    out = ""
    base, top = 1060, 520
    for i, b in enumerate(bars):
        h = (base - top) * b["value"] / vmax
        x = 90 + i * (bw + gap)
        col = {"main": a, "compare": P["blue"]}.get(b.get("style", "context"), P["grey"])
        tc = {"main": a, "compare": P["blue"]}.get(b.get("style", "context"), P["ink"])
        out += (f'<div class="ab" style="left:{x:.0f}px;top:{base-h:.0f}px;width:{bw:.0f}px;height:{h:.0f}px;background:{col};border-radius:4px 4px 0 0"></div>'
                f'<div class="ab serif" style="left:{x:.0f}px;top:{base-h-62:.0f}px;width:{bw:.0f}px;text-align:center;font-size:44px;line-height:52px;color:{tc}">{esc(b["display"], a)}</div>'
                f'<div class="ab" style="left:{x:.0f}px;top:{base+16}px;width:{bw:.0f}px;text-align:center;font-size:28px;line-height:34px">{esc(b["label"], a)}</div>')
    out += f'<div class="ab" style="left:90px;top:{base}px;width:900px;height:2px;background:{P["soft"]}"></div>'
    sub = f'<div class="ab" style="left:90px;top:370px;font-size:28px;color:{P["soft"]}">{esc(s.get("subtitle",""), a)}</div>'
    return f'<div class="s">{header(n, tot)}{kick_head(s, a)}{sub}{out}</div>'


def t_line(s, n, tot, spec):
    """Line chart. series: [{name, style: main|compare, points: [[x,y],...]}]"""
    a = P["sig"]
    X0, X1, Y0, Y1 = 90, 990, 1060, 500
    xs = [p[0] for sr in s["series"] for p in sr["points"]]
    ys = [p[1] for sr in s["series"] for p in sr["points"]]
    xmin, xmax = min(xs), max(xs)
    ymax = s.get("y_max", max(ys) * 1.08)
    ymin = s.get("y_min", 0)
    fx = lambda x: X0 + (X1 - X0) * (x - xmin) / (xmax - xmin)
    fy = lambda y: Y0 - (Y0 - Y1) * (y - ymin) / (ymax - ymin)
    svg = f'<line x1="{X0}" y1="{Y0}" x2="{X1}" y2="{Y0}" stroke="{P["soft"]}" stroke-width="2"/>'
    if s.get("y_ref"):
        v, lab = s["y_ref"]
        svg += (f'<line x1="{X0}" y1="{fy(v):.0f}" x2="{X1}" y2="{fy(v):.0f}" stroke="{P["hair"]}" stroke-width="2"/>'
                f'<text x="{X1}" y="{fy(v)-12:.0f}" text-anchor="end" font-size="28" fill="{P["soft"]}">{html.escape(lab)}</text>')
    for sr in s["series"]:
        pts = " ".join(f"{fx(x):.1f},{fy(y):.1f}" for x, y in sr["points"])
        if sr.get("style") == "compare":
            svg += f'<polyline points="{pts}" fill="none" stroke="{P["blue"]}" stroke-width="4" stroke-dasharray="14 10"/>'
            col = P["blue"]
        else:
            svg += f'<polyline points="{pts}" fill="none" stroke="{a}" stroke-width="6"/>'
            col = a
        lx, ly = sr["points"][-1]
        svg += f'<text x="{X1}" y="{fy(ly)-18:.0f}" text-anchor="end" font-size="30" font-weight="600" fill="{col}">{html.escape(sr["name"])}</text>'
    for an in s.get("annotations", []):
        x, y = fx(an["x"]), fy(an["y"])
        svg += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="{an.get("color", P["ink"])}"/>'
                f'<text x="{x + an.get("dx", 22):.0f}" y="{y + an.get("dy", -16):.0f}" text-anchor="{an.get("anchor","start")}" font-size="30" font-weight="600" fill="{P["ink"]}">{html.escape(an["text"])}</text>')
    for x, lab in s.get("x_ticks", []):
        svg += f'<text x="{fx(x):.0f}" y="{Y0+44}" text-anchor="middle" font-size="28" fill="{P["soft"]}">{html.escape(lab)}</text>'
    sub = f'<div class="ab" style="left:90px;top:370px;font-size:28px;color:{P["soft"]}">{esc(s.get("subtitle",""), a)}</div>'
    return (f'<div class="s">{header(n, tot)}{kick_head(s, a)}{sub}'
            f'<svg class="ab" style="left:0;top:0" width="{W}" height="{H}" font-family="Source Sans 3">{svg}</svg></div>')


def t_timeline(s, n, tot, spec):
    """3-6 milestones evenly spaced (not to scale); dot size follows `size` (0-1)."""
    a = P["sig"]
    ms = s["milestones"]
    k = len(ms)
    out = f'<div class="ab" style="left:90px;top:699px;width:900px;height:2px;background:{P["soft"]}"></div>'
    for i, m in enumerate(ms):
        x = 120 + 840 * i / (k - 1)
        r = 8 + 26 * m.get("size", 0.5) ** 0.5
        col = P["blue"] if m.get("style") == "compare" else a
        out += f'<div class="ab" style="left:{x-r:.0f}px;top:{700-r:.0f}px;width:{2*r:.0f}px;height:{2*r:.0f}px;border-radius:50%;background:{col}"></div>'
        al = "left" if i == 0 else ("right" if i == k - 1 else "center")
        tx = x - (0 if al == "left" else 300 if al == "right" else 150)
        top = 520 if i % 2 == 0 else 760
        out += (f'<div class="ab" style="left:{tx:.0f}px;top:{top}px;width:300px;text-align:{al}">'
                f'<div class="serif" style="font-size:56px;line-height:60px">{esc(m["value"], a)}</div>'
                f'<div style="font-size:28px;line-height:36px;color:{P["soft"]}">{esc(m["label"], a)}</div></div>')
    if not s.get("to_scale"):
        out += f'<div class="ab" style="left:90px;top:900px;font-size:28px;color:{P["soft"]}">Milestones not to scale</div>'
    if s.get("body"):
        out += f'<div class="ab body" style="left:90px;top:980px;width:900px;color:{P["soft"]}">{esc(s["body"], a)}</div>'
    return f'<div class="s">{header(n, tot)}{kick_head(s, a)}{out}</div>'


def _zig(top: bool) -> str:
    pts = []
    for k in range(0, 781, 24):
        pts += [f"{k},{12 if top else 0}", f"{k+12},{0 if top else 12}"]
    return f'<svg width="780" height="12" style="display:block"><polygon points="0,{12 if top else 0} {" ".join(pts)} 780,{12 if top else 0}" fill="{P["slip"]}"/></svg>'


def t_receipt(s, n, tot, spec):
    a = P["sig"]
    row = lambda l, v: (f'<div style="display:flex;justify-content:space-between;font-size:30px;line-height:52px">'
                        f'<span>{html.escape(l)}</span><span>{html.escape(v)}</span></div>')
    lines = "".join(row(l, v) for l, v in s["lines"])
    stamp = ""
    if s.get("stamp"):
        stamp = (f'<div style="margin:44px auto 0;width:max-content;border:3px solid {a};color:{a};padding:10px 22px;'
                 f'font-size:32px;font-weight:500;transform:rotate(-3deg)">{html.escape(s["stamp"])}</div>')
    tl, tv = s["total"]
    after = f'<div class="ab body" style="left:90px;top:1010px;width:900px">{esc(s["after"], a)}</div>' if s.get("after") else ""
    kick = f'<div class="ab kick" style="left:90px;top:150px">{esc(s.get("kicker",""), a)}</div>'
    return f"""<div class="s">{header(n, tot)}{kick}
<div class="ab" style="left:150px;top:220px;width:780px">{_zig(True)}
<div class="mono" style="background:{P['slip']};padding:40px 40px 48px">
<div style="text-align:center;font-size:30px;font-weight:500;letter-spacing:.08em">{html.escape(s['title'])}</div>
<div style="border-top:2px dashed {P['soft']};margin:28px 0 20px"></div>{lines}
<div style="border-top:2px solid {P['ink']};border-bottom:2px solid {P['ink']};height:8px;margin:24px 0"></div>
<div style="display:flex;justify-content:space-between;align-items:baseline"><span style="font-size:30px;font-weight:500">{html.escape(tl)}</span><span class="serif" style="font-size:64px;color:{a}">{html.escape(tv)}</span></div>
{stamp}</div>{_zig(False)}</div>{after}</div>"""


def t_table(s, n, tot, spec):
    """Face-off table: columns = [label, A, B]; highlight_col (1 or 2) in Signal."""
    a = P["sig"]
    cols = s["columns"]
    hc = s.get("highlight_col", 2)
    head = "".join(f'<div style="flex:1;text-align:right;font-size:40px" class="serif">{esc(c, a)}</div>' for c in cols[1:])
    rows = ""
    for r in s["rows"]:
        cells = ""
        for j, v in enumerate(r[1:], start=1):
            col = a if j == hc else P["ink"]
            cells += f'<div class="serif" style="flex:1;text-align:right;font-size:64px;line-height:72px;color:{col}">{esc(v, a)}</div>'
        rows += (f'<div style="border-top:2px solid {P["hair"]};padding:26px 0 30px">'
                 f'<div style="font-size:28px;color:{P["soft"]};margin-bottom:6px">{esc(r[0], a)}</div>'
                 f'<div style="display:flex;gap:24px">{cells}</div></div>')
    return (f'<div class="s">{header(n, tot)}{kick_head(s, a)}'
            f'<div class="ab" style="left:90px;top:400px;width:900px"><div style="display:flex;gap:24px;margin-bottom:24px">{head}</div>{rows}</div></div>')


def t_verdict(s, n, tot, spec):
    night = spec.get("verdict_style", "night") == "night"
    bg, fg, acc = (N["night"], N["chalk"], N["ember"]) if night else (P["paper"], P["ink"], P["sig"])
    rule = "" if night else f'<div class="ab" style="left:90px;top:270px;width:120px;height:8px;background:{acc}"></div>'
    kc = N["chalk"] if night else P["sig"]
    return f"""<div class="s" style="background:{bg};color:{fg}">{header(n, tot, night)}
<div class="ab kick" style="left:90px;top:210px;color:{kc}">{esc(s.get('kicker','The verdict'), acc)}</div>{rule}
<div class="ab serif" style="left:90px;top:300px;width:900px;font-size:{s.get('size',88)}px;line-height:{int(s.get('size',88)*1.09)}px">{esc(s['statement'], acc)}</div>
<div class="ab" style="left:90px;top:880px;width:900px;font-size:40px;line-height:52px">{esc(s.get('action',''), acc)}</div>
<div class="ab" style="left:90px;top:1196px;font-size:24px;line-height:32px">Educational, not financial advice.</div></div>"""


def t_sources(s, n, tot, spec):
    a = P["sig"]
    src = "<br>".join(f"{i}. {esc(x, a)}" for i, x in enumerate(s["sources"], 1))
    return f"""<div class="s">{header(n, tot)}
<div class="ab serif h2" style="left:90px;top:210px">Sources and method</div>
<div class="ab" style="left:90px;top:330px;width:900px;font-size:28px;line-height:40px">{src}</div>
<div class="ab" style="left:90px;top:{s.get('method_top',600)}px;width:900px;background:{P['slip']};border:2px solid {P['hair']};padding:36px 40px;font-size:28px;line-height:40px">
<div style="font-weight:600;margin-bottom:8px">Method</div>{esc(s['method'], a)}</div>
<div class="ab serif" style="left:90px;top:1000px;font-size:48px;line-height:56px;width:900px">{esc(s.get('save','Save this for later.'), a)}</div>
<div class="ab" style="left:90px;top:1100px;font-size:32px;color:{P['soft']}">Follow @moneybypixels for India's money, in numbers.</div></div>"""


TEMPLATES = dict(cover=t_cover, context=t_context, stack=t_stack, split=t_split, bars=t_bars,
                 line=t_line, timeline=t_timeline, receipt=t_receipt, table=t_table,
                 verdict=t_verdict, sources=t_sources)


# ---------------- checks ----------------

def check(spec: dict) -> list[str]:
    errs = []
    sl = spec["slides"]
    if not 5 <= len(sl) <= 8:
        errs.append(f"slide count {len(sl)} (want 5-8)")
    if sl[0]["t"] != "cover":
        errs.append("first slide must be a cover")
    if sl[-1]["t"] != "sources":
        errs.append("last slide must be sources")
    if spec.get("type") == "news" and sl[0].get("style") != "night":
        errs.append("news posts use the Night cover")
    if spec.get("type") == "educational" and sl[0].get("style", "paper") != "paper":
        errs.append("educational posts use the Paper cover")
    if not spec.get("footer"):
        errs.append("missing footer (assumptions + source line)")
    elif "not financial advice" not in " ".join(spec["footer"]).lower():
        errs.append("footer must include 'Educational, not financial advice'")
    for i, s in enumerate(sl, 1):
        if s["t"] not in TEMPLATES:
            errs.append(f"slide {i}: unknown template {s['t']}")
        body = s.get("body", "") + " " + s.get("caption", "")
        if len(body.split()) > 45:
            errs.append(f"slide {i}: body is {len(body.split())} words (max 45)")
        if len(s.get("headline", "")) > 95:
            errs.append(f"slide {i}: headline too long ({len(s['headline'])} chars, max 95)")
    cap = spec.get("caption", "")
    if len(cap) > 2200:
        errs.append("caption over Instagram's 2,200 characters")
    if len(spec.get("hashtags", [])) > 5:
        errs.append("use 5 hashtags or fewer")
    return errs


# ---------------- output ----------------

def caption_md(spec: dict) -> str:
    tags = " ".join("#" + t.lstrip("#") for t in spec.get("hashtags", []))
    src = "\n".join(f"- {x}" for x in spec.get("source_links", []))
    chk = "\n".join(f"- [ ] {x}" for x in spec.get("checklist", []))
    return f"""# {spec['title']}

Type: {spec['type']} · Verdict slide: {spec['verdict_style']} · Date: {spec.get('date','')}

## Caption (copy everything in the box)

```
{spec['caption'].strip()}

{tags}
```

## Alt text (Advanced settings > Accessibility)

{spec.get('alt_text','')}

## Sources to check before posting

{src or '- (calculation only)'}

## Approval checklist

{chk}
- [ ] Every number on the slides matches the build script output
- [ ] Nothing reads as advice to buy, sell or pick a product
"""


def render(post_dir: str) -> Path:
    d = Path(post_dir).resolve()
    spec = json.loads((d / "spec.json").read_text())
    errs = check(spec)
    if errs:
        raise SystemExit("Spec check failed:\n- " + "\n- ".join(errs))
    from playwright.sync_api import sync_playwright
    import shutil
    out = d / "slides"
    out.mkdir(exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    work = d / "work"
    work.mkdir(exist_ok=True)
    total = len(spec["slides"])
    foot = footer(spec["footer"])
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome) if chrome else p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        files = []
        for i, s in enumerate(spec["slides"], 1):
            body = TEMPLATES[s["t"]](s, i, total, spec)
            if s["t"] in DATA_TYPES and s.get("footer", True):
                body = body[: body.rfind("</div>")] + foot + "</div>"
            f = work / f"{i}.html"
            f.write_text(css() + body)
            pg.goto(f.as_uri())
            pg.wait_for_timeout(400)
            png = out / f"{spec['slug']}_{i}.png"
            pg.screenshot(path=str(png))
            files.append(png)
        b.close()
    from PIL import Image
    w, h = 360, 450
    cols = 4
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + 10) + 10, rows * (h + 10) + 10), "white")
    for k, f in enumerate(files):
        sheet.paste(Image.open(f).resize((w, h)), (10 + (k % cols) * (w + 10), 10 + (k // cols) * (h + 10)))
    sheet.save(d / "contact_sheet.png")
    (d / "caption.md").write_text(caption_md(spec))
    return d


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("rendered", render(p))

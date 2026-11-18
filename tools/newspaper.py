#!/usr/bin/env python3
"""Apply the newspaper layout to a morning-brief index.html (GitHub copy).

Usage: python3 tools/newspaper.py index.html [--weather=sunny|partly|cloudy|rain|storm|snow|fog]
(Without --weather, the condition is guessed from the headline and agenda text.)

- Top band keeps only the big date + headline.
- The daily agenda (acts + temperature column) becomes a compact "Today" tile,
  top of the first column. "Needs attention" sits top of the second column.
- Every other section becomes a tile, placed in whichever column is shortest.
- On phones the tiles stack in their original order (Today, Needs attention, ...).
Safe to run more than once.
"""
import re, sys, html as htmllib

CSS = r"""
/* newspaper layout */
body{background:#FBFAF6}
.band .inner{max-width:1180px}
.top{background:#F6F4EE;border-bottom:none}
.top .inner{padding-bottom:24px;border-bottom:4px double #2E2C27}
.top .inner > svg{display:none}
.date{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:38px;line-height:1.15;color:#2E2C27;letter-spacing:0;margin-bottom:6px}
h1{font-family:"Oswald","Franklin Gothic Demi Cond","Franklin Gothic Medium Cond","Arial Narrow","Liberation Sans Narrow",Impact,sans-serif;font-weight:700;font-size:46px;line-height:1.05;letter-spacing:.005em;text-transform:uppercase;max-width:none}
.np-grid{display:flex;gap:22px;align-items:flex-start;padding-top:4px}
.np-col{flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:22px}
.np-tile{background:#FFFFFF;border:1px solid #D9D6CC;border-top:3px solid #2E2C27;padding:14px 16px 8px}
.np-tile.np-alert{border-top-color:#C6613F}
.np-tile h2{font-family:"Fraunces",Georgia,serif;font-size:17px;text-transform:uppercase;letter-spacing:.06em;
  padding-bottom:8px;margin:0 0 12px;border-bottom:1px solid #D9D6CC}
.np-tile.list{margin:0}
.np-tile ol{list-style:none}
.np-tile ol li{display:grid;grid-template-columns:14px 1fr;margin-bottom:12px}
.np-tile .n{font-size:0;padding-top:0}
.np-tile .n::before{content:"\2022";font-size:16px;line-height:20px;color:#2E2C27}
.np-tile .t{font-size:14px;margin-bottom:2px}
.np-tile .s{font-size:13px;line-height:1.45}
/* Today tile: vertical agenda with temps on the right */
.np-today .agenda{display:grid;grid-template-columns:1fr 64px;gap:0}
.np-today .acts{display:block}
.np-today .act{border:none;border-top:1px solid #ECEAE3;padding:8px 10px 8px 0}
.np-today .act:first-child{border-top:none;padding-top:0}
.np-today .act b{font-size:12px;margin-bottom:2px}
.np-today .act p{font-size:13px;line-height:1.4}
.np-today .temps{padding-left:12px}
.np-today .temps li{display:block;margin:0 0 6px}
.np-today .temps .h{font-size:10px}
.np-today .temps .v{font-size:17px}
@media (max-width:1000px){.np-col:nth-child(3){display:contents}.np-grid{flex-wrap:wrap}.np-col{flex:1 1 45%}}
@media (max-width:640px){
  .np-grid{flex-direction:column;gap:18px}
  .np-col,.np-col:nth-child(3){display:contents}
  .np-tile{order:var(--o,0);width:100%}
  .date{font-size:28px}
  h1{font-size:32px}
}
"""


WX_CSS = r"""
.np-head{display:flex;align-items:center;gap:28px}
.np-title{flex:1 1 auto;min-width:0}
.np-wx{flex:0 0 160px;text-align:center}
.np-wx svg{display:block!important;width:120px;height:120px;margin:0 auto;overflow:visible}
.np-wx .cap{white-space:nowrap;font-size:12px;color:#6B6A63;letter-spacing:.04em;text-transform:uppercase;margin-top:2px}
.np-wx .cap b{color:#2E2C27;font-weight:600}
@keyframes wx-spin{to{transform:rotate(360deg)}}
@keyframes wx-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes wx-drift{0%,100%{transform:translateX(-5px)}50%{transform:translateX(6px)}}
@keyframes wx-fall{0%{transform:translateY(-6px);opacity:0}20%{opacity:1}100%{transform:translateY(26px);opacity:0}}
@keyframes wx-snow{0%{transform:translate(0,-6px);opacity:0}20%{opacity:1}50%{transform:translate(4px,10px)}100%{transform:translate(-3px,26px);opacity:0}}
@keyframes wx-flash{0%,86%,100%{opacity:0}88%,92%{opacity:1}90%{opacity:.3}}
@keyframes wx-fog{0%,100%{transform:translateX(-8px)}50%{transform:translateX(8px)}}
.wx-rays{transform-origin:60px 60px;animation:wx-spin 14s linear infinite}
.wx-core{transform-origin:60px 60px;animation:wx-pulse 3.2s ease-in-out infinite}
.wx-cloud{animation:wx-drift 6s ease-in-out infinite}
.wx-drop{animation:wx-fall 1.3s linear infinite}
.wx-flake{animation:wx-snow 2.6s linear infinite}
.wx-bolt{animation:wx-flash 4s linear infinite}
.wx-fogline{animation:wx-fog 5s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.np-wx *{animation:none!important}}
@media (max-width:640px){.np-head{gap:12px}.np-wx{flex-basis:84px}.np-wx svg{width:80px;height:80px}.np-wx .cap{font-size:10px}}
"""

SUN_C = "#E8A33A"; CLAY = "#C6613F"; INK = "#2E2C27"; RAIN = "#5B83A8"
def _sun(cx=60, cy=60, r=20, small=False):
    rays = "".join(
        f'<line x1="{cx}" y1="{cy-r-8}" x2="{cx}" y2="{cy-r-17}" transform="rotate({a} {cx} {cy})"/>'
        for a in range(0, 360, 45))
    return (f'<g class="wx-rays" style="transform-origin:{cx}px {cy}px" stroke="{CLAY}" stroke-width="3.5" stroke-linecap="round">{rays}</g>'
            f'<circle class="wx-core" style="transform-origin:{cx}px {cy}px" cx="{cx}" cy="{cy}" r="{r}" fill="{SUN_C}" stroke="{CLAY}" stroke-width="2.5"/>')
CLOUD_PATH = "M34 88 H86 A14 14 0 0 0 86 60 A20 20 0 0 0 48 54 A17 17 0 0 0 34 88 Z"
def _cloud(fill="#FFFFFF", dy=0, delay="0s"):
    return (f'<g class="wx-cloud" style="animation-delay:{delay}"><path d="{CLOUD_PATH}" transform="translate(0 {dy})" '
            f'fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/></g>')
def _drops(color=RAIN, cls="wx-drop"):
    out = ""
    for i, x in enumerate((44, 58, 72, 86)):
        d = f"{i*0.32:.2f}s"
        if cls == "wx-drop":
            out += f'<line class="{cls}" style="animation-delay:{d}" x1="{x}" y1="90" x2="{x-3}" y2="99" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
        else:
            out += f'<circle class="{cls}" style="animation-delay:{i*0.6:.1f}s" cx="{x}" cy="94" r="3" fill="#FFFFFF" stroke="{INK}" stroke-width="1.5"/>'
    return out
WX_ART = {
  "sunny":  lambda: _sun(),
  "partly": lambda: '<g transform="translate(14 -14) scale(.8)">' + _sun() + "</g>" + _cloud(dy=8),
  "cloudy": lambda: '<g transform="translate(-14 -12) scale(.8)" opacity=".75">' + _cloud("#E9E7E0", delay="-3s") + "</g>" + _cloud(dy=6),
  "rain":   lambda: _cloud(dy=-6) + _drops(),
  "storm":  lambda: _cloud("#D9D6CC", dy=-6) + f'<polygon class="wx-bolt" points="62,82 52,100 61,100 55,116 72,94 63,94 68,82" fill="{SUN_C}" stroke="{CLAY}" stroke-width="1.5"/>' + _drops(),
  "snow":   lambda: _cloud(dy=-6) + _drops(cls="wx-flake"),
  "fog":    lambda: _cloud("#E9E7E0", dy=-10) + "".join(
                f'<line class="wx-fogline" style="animation-delay:{i*-1.6:.1f}s" x1="{24+i*6}" y1="{90+i*9}" x2="{96-i*4}" y2="{90+i*9}" stroke="#9C9A90" stroke-width="3" stroke-linecap="round"/>' for i in range(3)),
}
WX_LABEL = {"sunny":"Sunny","partly":"Partly sunny","cloudy":"Cloudy","rain":"Rain","storm":"Storms","snow":"Snow","fog":"Fog"}

def detect_weather(doc):
    m = re.search(r'<h1>(.*?)</h1>', doc, flags=re.S)
    acts = " ".join(re.findall(r'<div class="act">(.*?)</div>', doc, flags=re.S))
    t = re.sub(r"<[^>]+>", " ", (m.group(1) if m else "") + " " + acts).lower()
    for key, words in (("storm",("thunder","storm")),("snow",("snow","flurr","sleet","ice ")),
                       ("rain",("rain","shower","drizzle","wet")),("fog",("fog","mist","haz")),
                       ("partly",("partly","mostly sunny","mostly cloudy","mix of sun","some sun","clouds and sun")),
                       ("cloudy",("cloud","overcast","gray","grey")),("sunny",("sun","clear","bright"))):
        if any(w in t for w in words):
            return key
    return "sunny"

def temp_range(doc):
    vals = [int(v) for v in re.findall(r'<span class="v">\s*(-?\d+)°', doc)]
    return (min(vals), max(vals)) if vals else None

def add_weather(doc, cond=None):
    if 'class="np-head"' in doc:
        return doc
    m = re.search(r'(<div class="date">.*?</div>)\s*(<h1>.*?</h1>)', doc, flags=re.S)
    if not m:
        return doc
    cond = cond if cond in WX_ART else detect_weather(doc)
    rng = temp_range(doc)
    cap = f"<b>{WX_LABEL[cond]}</b>" + (f" · {rng[0]}°–{rng[1]}°" if rng else "")
    svg = f'<svg viewBox="0 0 120 120" role="img" aria-label="{WX_LABEL[cond]}">{WX_ART[cond]()}</svg>'
    head = (f'<div class="np-head"><div class="np-title">{m.group(1)}{m.group(2)}</div>'
            f'<div class="np-wx">{svg}<div class="cap">{cap}</div></div></div>')
    return doc[:m.start()] + head + doc[m.end():]

START, END = "<!-- newspaper:start -->", "<!-- newspaper:end -->"

def text_len(s):
    return len(htmllib.unescape(re.sub(r"<[^>]+>", "", s)))

def restructure(doc):
    if 'class="np-grid"' in doc:
        return doc
    # 1. Pull the agenda (acts + temps) out of the top band
    m = re.search(r'<div class="agenda">.*?</ul>\s*</div>', doc, flags=re.S)
    agenda = m.group(0) if m else ""
    if m:
        doc = doc[:m.start()] + doc[m.end():]
    # 2. Collect the section blocks from the lower band
    lower = re.search(r'(<section class="band"><div class="inner">)(.*?)(</div></section>\s*</body>)', doc, flags=re.S)
    if not lower:
        return doc
    body = lower.group(2)
    blocks = re.findall(r'<div class="list">.*?</ol>\s*</div>|<p class="calm">.*?</p>', body, flags=re.S)
    tiles = []
    if agenda:
        tiles.append(('<div class="np-tile np-today"><h2>Today</h2>' + agenda + '</div>', text_len(agenda) * 0.8 + 120))
    for b in blocks:
        if b.startswith('<p class="calm">'):
            t = '<div class="np-tile list">' + b + '</div>'
        else:
            alert = "np-alert" if re.search(r'<h2>\s*Needs attention', b) else ""
            t = b.replace('<div class="list">', f'<div class="np-tile list {alert}">', 1)
        tiles.append((t, text_len(b) + 80))
    # 3. Place: Today -> col 1 top, Needs attention -> col 2 top, rest -> shortest column
    cols = [[], [], []]
    heights = [0, 0, 0]
    order = 0
    def put(i, tile, h):
        nonlocal order
        cols[i].append(tile.replace('class="np-tile', f'style="--o:{order}" class="np-tile', 1))
        heights[i] += h
        order += 1
    rest = []
    for tile, h in tiles:
        if "np-today" in tile and not cols[0]:
            put(0, tile, h)
        elif "np-alert" in tile and not cols[1]:
            put(1, tile, h)
        else:
            rest.append((tile, h))
    for tile, h in rest:
        i = heights.index(min(heights))
        put(i, tile, h)
    grid = '<div class="np-grid">' + "".join('<div class="np-col">' + "".join(c) + "</div>" for c in cols) + "</div>"
    return doc[:lower.start(2)] + grid + doc[lower.end(2):]

def main(path, cond=None):
    doc = open(path, encoding="utf-8").read()
    doc = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", doc, flags=re.S)
    doc = restructure(doc)
    doc = add_weather(doc, cond)
    if "</head>" not in doc:
        sys.exit("no </head> found")
    font = '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap" rel="stylesheet">'
    doc = doc.replace("</head>", f"{START}{font}<style>{CSS}{WX_CSS}</style>{END}\n</head>", 1)
    open(path, "w", encoding="utf-8").write(doc)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--weather=")]
    w = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--weather=")), None)
    main(args[0] if args else "index.html", w)

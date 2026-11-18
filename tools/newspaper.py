#!/usr/bin/env python3
"""Apply the newspaper layout to a morning-brief index.html (GitHub copy).

Usage: python3 tools/newspaper.py index.html

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
.top svg{display:none}
.date{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:38px;line-height:1.15;color:#2E2C27;letter-spacing:0;margin-bottom:6px}
h1{font-size:38px;max-width:none}
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
  .date,h1{font-size:28px}
}
"""

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

def main(path):
    doc = open(path, encoding="utf-8").read()
    doc = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", doc, flags=re.S)
    doc = restructure(doc)
    if "</head>" not in doc:
        sys.exit("no </head> found")
    doc = doc.replace("</head>", f"{START}<style>{CSS}</style>{END}\n</head>", 1)
    open(path, "w", encoding="utf-8").write(doc)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "index.html")

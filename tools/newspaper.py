#!/usr/bin/env python3
"""Apply the newspaper layout to a morning-brief index.html (GitHub copy).

Usage: python3 tools/newspaper.py index.html
Injects (or replaces) a marked <style> block before </head>. Safe to run more than once.
"""
import re, sys

CSS = r"""
/* newspaper layout */
body{background:#FBFAF6}
.band .inner{max-width:1180px}
.top{background:#F6F4EE;border-bottom:none}
.top .inner{padding-bottom:28px;border-bottom:4px double #2E2C27}
.date{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:38px;line-height:1.15;color:#2E2C27;letter-spacing:0;margin-bottom:6px}
h1{font-size:38px;max-width:none}
.band:not(.top) .inner{column-count:3;column-gap:22px;padding-top:28px}
.band:not(.top) .list,.band:not(.top) .calm{break-inside:avoid;-webkit-column-break-inside:avoid;display:inline-block;width:100%;
  background:#FFFFFF;border:1px solid #D9D6CC;border-top:3px solid #2E2C27;padding:14px 16px 6px;margin:0 0 22px}
.band:not(.top) .list:first-child{border-top-color:#C6613F}
.band:not(.top) h2{font-family:"Fraunces",Georgia,serif;font-size:17px;text-transform:uppercase;letter-spacing:.06em;
  padding-bottom:8px;margin-bottom:12px;border-bottom:1px solid #D9D6CC}
.band:not(.top) ol{list-style:none}
.band:not(.top) ol li{display:grid;grid-template-columns:14px 1fr;margin-bottom:12px}
.band:not(.top) .n{font-size:0;padding-top:0}
.band:not(.top) .n::before{content:"\2022";font-size:16px;line-height:20px;color:#2E2C27}
.band:not(.top) .t{font-size:14px;margin-bottom:2px}
.band:not(.top) .s{font-size:13px;line-height:1.45}
@media (max-width:1000px){.band:not(.top) .inner{column-count:2}}
@media (max-width:640px){
  .band:not(.top) .inner{column-count:1}
  .date,h1{font-size:28px}
}
"""

START, END = "<!-- newspaper:start -->", "<!-- newspaper:end -->"

def main(path):
    html = open(path, encoding="utf-8").read()
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)
    block = f"{START}<style>{CSS}</style>{END}\n"
    if "</head>" not in html:
        sys.exit("no </head> found")
    html = html.replace("</head>", block + "</head>", 1)
    open(path, "w", encoding="utf-8").write(html)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "index.html")

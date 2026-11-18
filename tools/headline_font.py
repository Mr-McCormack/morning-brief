#!/usr/bin/env python3
"""Embed the headline font (Century Schoolbook Bold, via TeX Gyre Schola) and style the <h1>.

Usage: python3 tools/headline_font.py page.html
Works on any morning-brief page (Claude artifact or GitHub copy). Safe to run more than once.
The font file is fonts/schola-bold-caps.woff (capitals, digits and punctuation only;
the headline is set in all caps). TeX Gyre fonts are free under the GUST Font License.
"""
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "schola-bold-caps.woff")
START, END = "<!-- headline-font:start -->", "<!-- headline-font:end -->"

def block():
    b = base64.b64encode(open(FONT, "rb").read()).decode()
    return (f'{START}<style>@font-face{{font-family:"Brief Headline";'
            f'src:url(data:font/woff;base64,{b}) format("woff");font-weight:700;font-style:normal}}'
            'h1{font-family:"Brief Headline","Century Schoolbook","TeX Gyre Schola",Georgia,serif!important;'
            'font-weight:700!important;font-stretch:normal!important;text-transform:uppercase;'
            'line-height:1.05;letter-spacing:0}</style>' + END)

def apply(doc):
    doc = re.sub(re.escape(START) + r".*?" + re.escape(END), "", doc, flags=re.S)
    # drop any older Google-font headline links (Oswald / Noto Serif Display)
    doc = re.sub(r'<link[^>]+fonts\.googleapis\.com/css2\?family=(Oswald|Noto\+Serif\+Display)[^>]*>', "", doc)
    doc = re.sub(r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>', "", doc)
    return doc.replace("</head>", block() + "\n</head>", 1)

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    doc = open(p, encoding="utf-8").read()
    open(p, "w", encoding="utf-8").write(apply(doc))

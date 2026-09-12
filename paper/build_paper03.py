"""Build paper/paper03.html from the author's paper_2026-03.md.

Text and numbers are carried over verbatim. The only transformations are typographic: curly
apostrophes, a real minus sign before numbers, house table classes, the running order of the
front matter, and the three figures inlined as SVG so they take the page fonts.
"""
import re, html, sys

SRC = sys.argv[1]; OUT = sys.argv[2]; FIGDIR = sys.argv[3]
DOI = "10.5281/zenodo.22724955"
FIGS = {"fig1_debt_interest_channel": "fig1", "fig2_composition": "fig2", "fig3_distribution": "fig3"}
CAPTIONS = {
    "fig1": "Figure 1. Each point on gilt yields moves third-year debt interest by about £11bn. "
            "33 OBR forecasts, November 2010 to March 2026; R squared 0.81. The filled point is "
            "September 2026, at +0.68 points on the fitted line.",
    "fig2": "Figure 2. From £23.6bn to £14.6bn: the composition matters more than the number. The "
            "final bar carries the 80 per cent interval, −4 to +34.",
    "fig3": "Figure 3. Distribution of the year-three underlying revision to borrowing, 33 OBR "
            "forecasts since 2010. Adverse 48 per cent, worse than the £17.5bn range 15 per cent, "
            "worse than the whole £23.6bn cushion 12 per cent.",
}
ALTS = {
    "fig1": "Scatter of the year-three debt interest revision against the change in the DMO-weighted gilt yield between OBR windows, with a fitted line of slope about 11 and the September 2026 move marked at plus 0.68 points.",
    "fig2": "Waterfall from the March 2026 figure of 23.6 through debt interest minus 8.5, receipts plus 3.0 and spending drift minus 3.5 to 14.6 before Budget measures, with an 80 per cent interval bar from minus 4 to plus 34.",
    "fig3": "Histogram of the year-three underlying revision to borrowing in ten billion pound bins, with lines marking zero, 17.5 and 23.6.",
}


def typo(s):
    """Curly apostrophes and a proper minus, nothing else."""
    s = html.escape(s, quote=False)
    s = re.sub(r"(?<=\w)'(?=\w)", "’", s)
    s = re.sub(r"(?<=s)'(?=\s)", "’", s)
    s = re.sub(r"(?<![\w-])-(?=[\d£])", "−", s)
    return s


def inline_svg(key):
    path = f"{FIGDIR}/{[k for k, v in FIGS.items() if v == key][0]}.svg"
    svg = open(path).read()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r'\s(width|height)="[^"]*pt"', "", svg, count=2)
    # namespace ids so three inline figures cannot collide
    ids = set(re.findall(r'id="([^"]+)"', svg))
    for i in ids:
        svg = svg.replace(f'id="{i}"', f'id="{key}-{i}"')
        svg = svg.replace(f'href="#{i}"', f'href="#{key}-{i}"').replace(f'url(#{i})', f'url(#{key}-{i})')
    svg = svg.replace("<svg ", f'<svg role="img" aria-label="{html.escape(ALTS[key], quote=True)}" ', 1)
    return svg


def cell_is_text(c):
    return len(re.findall(r"[A-Za-z]{2,}", c)) > 2


def table(lines, caption, tight=False, total_label=None):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    head, body = rows[0], rows[2:]
    ncol = len(head)
    numeric_col = [False] + [all(not cell_is_text(r[j]) for r in body if j < len(r)) for j in range(1, ncol)]
    th = "".join(f'<th{" class=\"n\"" if numeric_col[j] else ""}>{typo(h)}</th>' for j, h in enumerate(head))
    out = []
    for r in body:
        tds = []
        for j, c in enumerate(r):
            if j == 0:
                tds.append(f"<td>{typo(c)}</td>")
            elif cell_is_text(c):
                tds.append(f'<td class="t">{typo(c)}</td>')
            else:
                tds.append(f'<td class="n">{typo(c)}</td>')
        cls = ' class="total"' if total_label and r[0] == total_label else ""
        out.append(f"    <tr{cls}>{''.join(tds)}</tr>")
    return (f'<table{" class=\"tight\"" if tight else ""}>\n  <caption>{typo(caption)}</caption>\n'
            f'  <thead><tr>{th}</tr></thead>\n  <tbody>\n' + "\n".join(out) + "\n  </tbody>\n</table>")


md = open(SRC).read().splitlines()
title = md[0][2:].strip(); subtitle = md[2][3:].strip()
body = md[4:]  # skip the meta paragraph, it becomes the front matter

parts = []
i = 0
in_list = None
pending_caption = None
appendix = False


def close_list():
    global in_list
    if in_list:
        parts.append(f"</{in_list}>"); in_list = None


while i < len(body):
    ln = body[i]
    s = ln.strip()
    if not s:
        close_list(); i += 1; continue
    if s.startswith("### "):
        close_list()
        h = s[4:]
        m = re.match(r"(\d+)\. (.*)", h)
        if m:
            parts.append(f'<h2 class="sec"><span class="n">{m.group(1)}</span>{typo(m.group(2))}</h2>')
        elif h.startswith("Appendix"):
            appendix = True
            parts.append(f'<h2 class="sec unnumbered">{typo(h)}</h2>')
        else:
            parts.append(f'<h2 class="sec unnumbered">{typo(h)}</h2>')
        i += 1; continue
    if s.startswith("|"):
        close_list()
        tbl = []
        while i < len(body) and body[i].strip().startswith("|"):
            tbl.append(body[i]); i += 1
        cap = pending_caption or ""
        pending_caption = None
        parts.append(table(tbl, cap, tight=appendix,
                           total_label="Headroom before measures" if "Table 4." in cap else None))
        continue
    if re.match(r"Table \d+\.", s):
        pending_caption = s; i += 1; continue
    m = re.match(r"!\[(.*?)\]\(figures/(\w+)\.svg\)", s)
    if m:
        close_list()
        key = FIGS[m.group(2)]
        parts.append(f'<figure class="plot">\n{inline_svg(key)}\n'
                     f'<figcaption>{typo(CAPTIONS[key])}</figcaption>\n</figure>')
        i += 1; continue
    m = re.match(r"(\d+)\. (.*)", s)
    if m:
        if in_list != "ol":
            close_list(); parts.append('<ol class="plain">'); in_list = "ol"
        txt = m.group(2)
        first, rest = re.match(r"(.*?\.)(\s.*)?$", txt).groups()
        parts.append(f"  <li><strong>{typo(first)}</strong>{typo(rest or '')}</li>")
        i += 1; continue
    if s.startswith("- "):
        if in_list != "ul":
            close_list(); parts.append('<ul class="plain">'); in_list = "ul"
        txt = s[2:]
        txt = re.sub(r"^(Q\d),", r"<strong>\1</strong>,", typo(txt))
        parts.append(f"  <li>{txt}</li>")
        i += 1; continue
    if s == "Foresight not hindsight" or s == "[mark]" or s.startswith("Walkforward Research, Paper 2026/03."):
        i += 1; continue
    close_list()
    if s.startswith("Source:") and appendix:
        parts.append(f'<p class="tablenote">{typo(s)}</p>')
    elif s.startswith("Against a floor of £10bn"):
        parts.append(f'<div class="callout"><p>{typo(s)}</p></div>')
    else:
        parts.append(f"<p>{typo(s)}</p>")
    i += 1
close_list()

CSS_EXTRA = """
/* paper 03 additions */
ol.plain{margin:0 0 .62em;padding-left:0;list-style:none;counter-reset:pt}
ol.plain li{position:relative;padding-left:17pt;margin-bottom:.5em;counter-increment:pt}
ol.plain li::before{content:counter(pt);position:absolute;left:0;top:.08em;
  font-family:"IBM Plex Mono",monospace;font-size:8pt;color:var(--accent)}
figure.plot svg{width:100%;height:auto;display:block}
figure.plot svg text{fill:var(--ink)}
p.tablenote{font-family:"Source Serif 4",Georgia,serif;font-size:8.2pt;font-style:italic;
  color:var(--muted);line-height:1.45;margin:-2pt 0 10pt}
.callout{break-inside:avoid}
table.tight td:first-child{white-space:nowrap}
"""

template = open("paper02.html").read()
head = template[:template.index("</style>")]
head = head.replace("<title>How good are the MoJ prison population projections?</title>",
                    f"<title>{typo(title)}</title>")
head = head.replace('font-family:"IBM Plex Mono",monospace;font-size:7.4pt;letter-spacing:.06em;\n  color:var(--muted);padding:6pt 0;',
                    'font-family:"IBM Plex Mono",monospace;font-size:7.4pt;letter-spacing:.06em;\n  color:var(--muted);padding:6pt 0;')
mast = template[template.index('<div class="masthead">'):template.index('<h1 class="title">')]
mast = mast.replace("Paper 2026/02", "Paper 2026/03")

front = f'''{mast}<h1 class="title">{typo(title)}</h1>
<p class="subtitle">{typo(subtitle)}</p>
<p class="byline">Hamish Paton &nbsp;·&nbsp; Walkforward Research</p>

<p class="meta">Version 1.0, 12 September 2026 &nbsp;·&nbsp; Tag: Registered forecast &nbsp;·&nbsp;
ORCID 0009-0007-4160-9268<br>
DOI <a href="https://doi.org/{DOI}">{DOI}</a> &nbsp;·&nbsp;
Ledger entry: <a href="https://walkforwardresearch.com/obr-headroom">walkforwardresearch.com/obr-headroom</a></p>

<div class="citation"><span class="lab">Pre-registration</span>
Forecast fixed on market data to 10 September 2026. One postscript will be added on 28 October 2026
with the OBR’s numbers and the scorecard; nothing else in this paper will change.</div>
'''

colophon = '''
<div class="colophon">
  Foresight not hindsight<br>
  Walkforward Research &nbsp;·&nbsp; enquiries@walkforwardresearch.com &nbsp;·&nbsp; walkforwardresearch.com
</div>
'''

page = head + CSS_EXTRA + "</style>\n</head>\n<body>\n\n" + front + "\n" + "\n".join(parts) + colophon + "\n</body>\n</html>\n"
open(OUT, "w").write(page)
print("wrote", OUT, len(parts), "blocks")

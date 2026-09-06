#!/usr/bin/env python3
"""
Build the full Walkforward Research site: ledger, method, notes, about.

    python3 build_site.py              # the real site
    python3 build_site.py --preview    # design preview, planned entries shown as registered

Same rule as the holding page: an entry appears only once registered_utc and commit are set.
The ledger lives at / and the four pages share one stylesheet.
"""
import glob, json, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "https://github.com/walkforwardresearch/ledger"
DOMAIN = "walkforwardresearch.com"
PREVIEW = "--preview" in sys.argv
OUT = os.path.join(HERE, "site-preview" if PREVIEW else "site")

FONTS = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@500;600&amp;'
         'family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&amp;'
         'family=IBM+Plex+Mono:wght@400;500&amp;display=swap">')

NAV = [("index.html", "intro", "introduction"),
       ("method.html", "method", "method"),
       ("ledger.html", "ledger", "the ledger"),
       ("notes.html", "notes", "notes"),
       ("about.html", "about", "about")]

MARK = '''<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
        <rect x="0" y="2"  width="15" height="8" fill="var(--block)"/><rect x="16" y="2"  width="8" height="8" fill="var(--accent)"/>
        <rect x="4" y="12" width="15" height="8" fill="var(--block)"/><rect x="20" y="12" width="8" height="8" fill="var(--accent)"/>
        <rect x="8" y="22" width="15" height="8" fill="var(--block)"/><rect x="24" y="22" width="8" height="8" fill="var(--accent)"/>
      </svg>'''

HERO_STAIR = '''<svg class="stair" viewBox="0 0 384 196" role="img" aria-label="Walk-forward validation: three rows, each a long training run followed immediately by the short slice the model was tested on, every row starting later in time">
        <rect x="0"   y="4"   width="212" height="32" fill="#97A4A8"/>
        <rect x="214" y="4"   width="56"  height="32" fill="#3E9C89"/>
        <rect x="50"  y="60"  width="212" height="32" fill="#97A4A8"/>
        <rect x="264" y="60"  width="56"  height="32" fill="#3E9C89"/>
        <rect x="100" y="116" width="212" height="32" fill="#97A4A8"/>
        <rect x="314" y="116" width="56"  height="32" fill="#3E9C89"/>
        <line x1="0" y1="166" x2="384" y2="166" stroke="#3A4A4E" stroke-width="1"/>
        <text x="384" y="186" text-anchor="end" fill="#859599" font-family="IBM Plex Mono, monospace" font-size="12" letter-spacing="1.5">time &#8594;</text>
      </svg>'''

METHOD_DIAGRAM = '''<svg class="stair" viewBox="0 0 470 150" role="img" aria-label="Each row trains on a block of past data then tests on the next slice it has never seen, stepping forward in time">
          <rect x="6"   y="6"   width="215" height="30" fill="var(--block)"/>
          <rect x="227" y="6"   width="64"  height="30" fill="var(--accent)"/>
          <rect x="66"  y="54"  width="215" height="30" fill="var(--block)"/>
          <rect x="287" y="54"  width="64"  height="30" fill="var(--accent)"/>
          <rect x="126" y="102" width="215" height="30" fill="var(--block)"/>
          <rect x="347" y="102" width="64"  height="30" fill="var(--accent)"/>
        </svg>'''

SERIES = [
    ("Which are next?",
     "Distress screens of public bodies and regulated companies, published as a pre-registered shortlist and scored on what happens."),
    ("Breaking points",
     "Capacity against a threshold, with a dated forecast of when the threshold is crossed."),
    ("Against consensus",
     "National series forecast ahead of the official and market numbers, marked on release."),
    ("A generation from now",
     "Town-level demography, housing and cohort forecasts to 2046 and 2066, with the backtest published alongside."),
]

# ------------------------------------------------------------------ ledger data

def fmt(d):
    return datetime.date.fromisoformat(d[:10]).strftime("%-d %b %Y") if d else ""


def load():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "data", "forecasts", "*.json"))):
        e = json.load(open(path))
        e["_file"] = os.path.relpath(path, HERE)
        # --preview shows the launch state: only entries flagged as the opening entry.
        if PREVIEW and not e.get("registered_utc") and e.get("launch_entry"):
            e["registered_utc"], e["commit"] = e["planned_registration"], "0000000"
        out.append(e)
    out.sort(key=lambda e: e.get("registered_utc") or e["planned_registration"])
    return [e for e in out if e.get("registered_utc")]


def glyph(status):
    lit = {"registered": 0, "open": 1, "closed": 3, "withdrawn": 0}.get(status, 0)
    rows = ""
    for i, (x, y) in enumerate(((0, 1), (3, 6), (6, 11))):
        on = "var(--accent)" if i < lit else "var(--block)"
        rows += (f'<rect x="{x}" y="{y}" width="9" height="4" fill="var(--block)"/>'
                 f'<rect x="{x + 10}" y="{y}" width="5" height="4" fill="{on}"/>')
    if status == "withdrawn":
        rows += '<line x1="0" y1="16" x2="21" y2="0" stroke="var(--muted)" stroke-width="1.5"/>'
    return f'<svg class="glyph" viewBox="0 0 21 16" aria-hidden="true">{rows}</svg>'


def counts(entries):
    c = {"registered": 0, "open": 0, "closed": 0, "withdrawn": 0}
    for e in entries:
        c[e.get("status", "registered")] = c.get(e.get("status", "registered"), 0) + 1
    c["scored"] = sum(1 for e in entries if e.get("result"))
    return c


def summary(entries):
    c = counts(entries)
    line = f'Registered {c["registered"]}. Open {c["open"]}. Closed {c["closed"]}.'
    if c["withdrawn"]:
        line += f' Withdrawn {c["withdrawn"]}.'
    if not c["scored"]:
        line += " Nothing scored yet; first marks land in October."
    return line


def ledger_rows(entries):
    if not entries:
        return ('<tr><td class="empty" colspan="6">Nothing registered yet. The first entries are '
                'committed to the public repository from 12&nbsp;September and appear here the moment '
                'they are. The ledger starts empty because a ledger that starts full should not be '
                'believed.</td></tr>')
    out = ""
    for e in entries:
        link = f'{REPO}/blob/main/{e["_file"]}'
        commit = f'{REPO}/commit/{e["commit"]}' if e.get("commit") else link
        sched = f' <span class="sched">({e["mark_schedule"]})</span>' if e.get("mark_schedule") else ""
        st = e.get("status", "registered")
        label = st.capitalize() + (f' &middot; {e["result"]}' if e.get("result") else "")
        out += f'''
          <tr>
            <td class="claim"><a href="{link}">{e["claim"]}</a></td>
            <td>{e["series"]}</td>
            <td class="bench">{e["benchmark"]}</td>
            <td class="num"><a href="{commit}">{fmt(e["registered_utc"])}</a></td>
            <td class="num">{fmt(e["next_mark"])}{sched}</td>
            <td><span class="status s-{st}">{glyph(st)}<span>{label}</span></span></td>
          </tr>'''
    return out


def ledger_table(entries):
    return f'''<div class="card table-card">
    <div class="table-scroll">
      <table class="ledger">
        <thead>
          <tr><th>Forecast</th><th>Series</th><th>Benchmark</th>
              <th>Made</th><th>Next mark</th><th>Status</th></tr>
        </thead>
        <tbody>{ledger_rows(entries)}
        </tbody>
      </table>
    </div>
  </div>'''

# ------------------------------------------------------------------ chrome

def header(active):
    cur = ' aria-current="page"'
    links = "\n      ".join(
        f'<a href="{f}"{cur if k == active else ""}>{label}</a>'
        for f, k, label in NAV)
    return f'''<header class="site">
  <div class="wrap site-bar">
    <a class="brand" href="index.html">
      {MARK}
      <span class="wordmark">walk<span class="fwd">forward</span><span class="co">Research</span></span>
    </a>
    <nav class="site-nav" aria-label="Site">
      {links}
    </nav>
  </div>
</header>'''


def footer():
    built = datetime.datetime.now(datetime.timezone.utc).strftime("%-d %b %Y %H:%M UTC")
    return f'''<footer class="site">
  <div class="wrap">
    <div class="foot-rule"></div>
    <div class="foot">
      <span>walkforward research &middot; foresight not hindsight</span>
      <span>page built {built} &middot; no accounts, no tracking, no personal data</span>
    </div>
  </div>
</footer>'''

# ------------------------------------------------------------------ pages

def intro():
    series = "\n".join(
        f'      <div class="series-row"><h3>{n}</h3><p>{d}</p></div>' for n, d in SERIES)
    return f'''<div class="hero">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <p class="kicker">Foresight not hindsight</p>
        <h1>Forecasts with dates on them, scored in public.</h1>
        <p class="lede">Walkforward Research forecasts British public institutions &mdash; prison
        capacity, council finances, the public finances, inflation, the shape of towns a generation
        out. Each forecast is published before the outcome is known and scored afterwards against
        the official or market number it set out to beat.</p>
      </div>
      <div class="hero-mark">{HERO_STAIR}</div>
    </div>
  </div>
</div>

<main class="wrap">
<section class="band">
  <div class="section-head">
    <h2>What we do</h2>
    <p>Three steps, in this order, every time. The order is the whole point: once a forecast is
    registered, there is nowhere left to hide.</p>
  </div>
  <div class="cards c3">
    <div class="card">
      <p class="kicker">First</p>
      <h3>Pick a question with a date on it</h3>
      <p>Questions where a decision turns on a number that does not exist yet, and where an official
      body has already put its own number on the record. Those are the ones worth forecasting,
      because there is something to be measured against.</p>
    </div>
    <div class="card tint">
      <p class="kicker">Then</p>
      <h3>Register it before the outcome</h3>
      <p>The claim, the benchmark and its value on the day, the data used, the dates it will be
      marked and the rule it will be scored by &mdash; committed to a public repository while the
      answer is still unknown.</p>
    </div>
    <div class="card">
      <p class="kicker">Afterwards</p>
      <h3>Publish the mark either way</h3>
      <p>Scored on the fixed date against the number it set out to beat. Hits and misses alike.
      Nothing is edited, nothing is quietly dropped, and the misses stay on the record.</p>
    </div>
  </div>
</section>

<section class="band">
  <div class="panel invert">
    <p class="kicker">The standard</p>
    <h3>A forecast you cannot check is an opinion</h3>
    <ul class="ticks">
      <li>The benchmark is named, with its vintage, before the forecast is made</li>
      <li>The marking dates are fixed in advance, so a miss cannot become a longer horizon</li>
      <li>Every claim on this site links to a registered entry, or it is not made</li>
    </ul>
  </div>
</section>

<section class="band">
  <div class="section-head">
    <h2>The series</h2>
    <p>Four lines of work, one method. Anything may enter if it can be forecast in advance and
    scored on a fixed date; anything may leave once it has been scored honestly.</p>
  </div>
  <div class="series">
{series}
  </div>
  <p class="caption">What has been registered so far, and how each entry stands, is on
  <a href="ledger.html">the ledger</a>. The rules it runs on are set out in the
  <a href="method.html">method</a>.</p>
</section>
</main>'''


def ledger_page(entries):
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">The ledger</span></div></div>
    <h1>Every forecast, its timestamp, and its mark</h1>
    <p class="lede">Append-only. Entries are added before the outcome is known and never edited
    afterwards. The ledger opens with the prison population entry; the rest appear as they are
    registered.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <p class="record-summary mono">{summary(entries)}</p>
  {ledger_table(entries)}
  <p class="caption">Every row links to the entry in the <a href="{REPO}">public repository</a> and to
  the commit that registered it. <span class="mono">Made</span> is the commit date;
  <span class="mono">Benchmark</span> names the publisher and vintage; the claim is the exact
  sentence registered, unedited. <a href="method.html#how-it-works">How the ledger works</a>.</p>
  </div>
</section>
</main>'''


def method():
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">Method</span></div></div>
    <h1>Trained on the past, scored on what it had never seen</h1>
    <p class="lede">The rules are written down before the forecast, so they cannot drift afterwards
    to flatter the result.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <div class="section-head">
    <h2>What walk-forward scoring is</h2>
    <p>Train a model on the past. Test it on the next slice of time &mdash; data it could not have
    seen. Step forward and repeat. Every score here is produced that way: the model makes its call
    the way it would on a Monday morning, before the answer exists.</p>
  </div>
  <div class="split">
    <div class="card diagram-card">
      <p class="kicker">Walk-forward validation</p>
      {METHOD_DIAGRAM}
      <div class="legend">
        <span><span class="key train"></span>data the model learned from</span>
        <span><span class="key test"></span>the slice it was tested on, never seen in training</span>
      </div>
      <p class="caption">Train on the past, test on the next slice, step forward, repeat. The model
      never sees the future.</p>
    </div>
    <div class="cards">
      <div class="card">
        <h3>Pre-registered</h3>
        <ul class="ticks">
          <li>Target, metric, benchmark and horizon written down first</li>
          <li>The bar is set while it can still be missed</li>
        </ul>
      </div>
      <div class="card tint">
        <h3>Published, then scored</h3>
        <ul class="ticks">
          <li>Forecasts out before the outcome, marks up after</li>
          <li>Hits and misses alike, and the ledger is append-only</li>
        </ul>
      </div>
      <div class="card">
        <h3>Domain-agnostic</h3>
        <ul class="ticks">
          <li>One harness scores public finances, capacity and demography</li>
          <li>Shared machinery is what makes these one body of work</li>
        </ul>
      </div>
    </div>
  </div>
  </div>
</section>

<section class="band">
  <div class="wrap">
  <div class="section-head">
    <h2>Why backtests are not evidence</h2>
    <p>A model tested on data it was fitted to will always look good &mdash; the exam was written
    after seeing the answers. Retrospective accuracy is easy to manufacture, and most published
    claims of it are worthless as evidence.</p>
  </div>
  <div class="panel invert">
    <p class="kicker">The standard</p>
    <h3>The only honest test is the one where the future was still the future</h3>
    <ul class="ticks">
      <li>Every claim here links to a registered entry, or it is not made</li>
      <li>That discipline is unglamorous, and it is the whole of the method</li>
    </ul>
  </div>
  </div>
</section>

<section class="band" id="how-it-works">
  <div class="wrap">
  <div class="section-head">
    <h2>How the ledger works</h2>
    <p>Registration, marking and withdrawal, in the order they happen.</p>
  </div>
  <div class="cards c3">
    <div class="card">
      <p class="kicker">Registration</p>
      <h3>Before the outcome exists</h3>
      <ul class="ticks">
        <li>The claim, the benchmark and its value on that day, the data used, the marking dates
        and the scoring rule, committed as a file</li>
        <li>The commit is the timestamp, and because the repository is public the push is recorded
        independently, so the date can be checked without taking our word for it</li>
      </ul>
    </div>
    <div class="card tint">
      <p class="kicker">Marking</p>
      <h3>Against the number it set out to beat</h3>
      <ul class="ticks">
        <li>Marks are added by scripts from the source data as it is published</li>
        <li>The benchmark names the publisher and the vintage, not just the series</li>
        <li>Marks will be computed with the conventions in the Bank of England&rsquo;s published
        forecast-evaluation package, so the arithmetic is not ours to argue about</li>
      </ul>
    </div>
    <div class="card">
      <p class="kicker">Afterwards</p>
      <h3>Nothing is edited or deleted</h3>
      <ul class="ticks">
        <li>A forecast wrong in construction is withdrawn with a reason and stays on the ledger</li>
        <li>A change of view is a new entry that supersedes the old one, and both are scored</li>
        <li>The record counts everything, including withdrawn entries and misses</li>
      </ul>
    </div>
  </div>

  <div class="panel">
    <p class="kicker">Status</p>
    <div class="statuses">
      <span class="status s-registered">{glyph("registered")}<span><strong>Registered</strong> &mdash; no marks yet</span></span>
      <span class="status s-open">{glyph("open")}<span><strong>Open</strong> &mdash; marks arriving</span></span>
      <span class="status s-closed">{glyph("closed")}<span><strong>Closed</strong> &mdash; final mark landed</span></span>
      <span class="status s-withdrawn">{glyph("withdrawn")}<span><strong>Withdrawn</strong> &mdash; kept, with a reason</span></span>
    </div>
    <p class="small">A marked entry also carries the headline word: beat, missed or tied.</p>
  </div>
  </div>
</section>
</main>'''


def notes():
    return '''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">Notes</span></div></div>
    <h1>Occasional write-ups</h1>
    <p class="lede">Method, results, and the entries that went badly. Published when there is
    something to say, not on a schedule.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <article class="card note-card">
    <p class="note-date">September 2026</p>
    <h2>Before the first entry</h2>
    <p>This site went up before there was anything on it, which is deliberate. A record only means
    something if the page existed before the results did &mdash; otherwise there is no way to know
    which results were quietly left off. So the ledger starts empty, the
    <a href="method.html#how-it-works">scoring rules are written down first</a>, and the first
    entries are registered in the public repository from September.</p>
    <p>From then on the deal is simple: every forecast is timestamped before the outcome is known,
    scored against the number it set out to beat, and never edited afterwards. Some will be wrong.
    Those stay up too &mdash; they are the point.</p>
  </article>
  </div>
</section>
</main>'''


def about():
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">About</span></div></div>
    <h1>What this is</h1>
    <p class="lede">Walkforward Research is an independent research project. It publishes forecasts
    about British public institutions before the outcome is known, and scores them in public
    afterwards against the official or market forecast each one set out to beat.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <div class="cards c3">
    <div class="card">
      <p class="kicker">Standing</p>
      <h3>A personal research project</h3>
      <p>Incorporation is in progress. The company number and registered address will appear here
      when it completes.</p>
      <p>Until then this is a personal research project, independent of any employer or client, and
      should be read as one.</p>
    </div>
    <div class="card tint">
      <p class="kicker">Contact</p>
      <h3>Enquiries</h3>
      <p><a href="mailto:enquiries@{DOMAIN}" class="mono">enquiries@{DOMAIN}</a></p>
      <p>It reaches a person. There is no form and no mailing list.</p>
    </div>
    <div class="card">
      <p class="kicker">Privacy</p>
      <h3>Nothing is collected</h3>
      <p>No accounts, no tracking beyond simple page counts, no personal data. The site is static
      files; there is nothing to sign up for and nothing watching you read it.</p>
    </div>
  </div>
  </div>
</section>
</main>'''


# ------------------------------------------------------------------ assembly

PAGES = {
    "index.html": ("intro", "Walkforward Research",
                   "UK forecasts published before the outcome is known, then scored in public against the official or market forecast they set out to beat.", intro),
    "method.html": ("method", "Method &mdash; Walkforward Research",
                    "Walk-forward scoring, pre-registration, and how entries are marked, withdrawn and superseded.", method),
    "ledger.html": ("ledger", "The ledger &mdash; Walkforward Research",
                    "Every forecast, its timestamp and its mark, linked to the entry and the commit that registered it.", ledger_page),
    "notes.html": ("notes", "Notes &mdash; Walkforward Research",
                   "Occasional write-ups on method and results, published when there is something to say.", notes),
    "about.html": ("about", "About &mdash; Walkforward Research",
                   "What Walkforward Research is, how to reach a person, and what this site does and does not collect.", about),
}


def build():
    os.makedirs(OUT, exist_ok=True)
    entries = load()
    for fname, (key, title, desc, fn) in PAGES.items():
        body = fn(entries) if key == "ledger" else fn()
        if key == "intro":
            body = intro()
        html = f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="styles.css">
</head>
<body>
{header(key)}
{body}
{footer()}
</body>
</html>
'''
        open(os.path.join(OUT, fname), "w").write(html)
    for asset in ("styles.css", "favicon.svg"):
        src = os.path.join(HERE, asset)
        if os.path.exists(src):
            open(os.path.join(OUT, asset), "w").write(open(src).read())
    print(f"site built — {len(entries)} entries in the ledger" + (" (preview)" if PREVIEW else ""))


if __name__ == "__main__":
    build()

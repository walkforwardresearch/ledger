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
       ("papers.html", "papers", "papers"),
       ("about.html", "about", "about")]

# The server strips .html, so every link uses the clean form. These are the URLs that
# get handed to people, so they should be the ones on the page.
URL = {"intro": "/", "method": "/method", "ledger": "/ledger",
       "papers": "/papers", "about": "/about"}


def url(key):
    return URL.get(key, "/" + key)

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
    ("Public finances",
     "Budgets, headroom and financial distress in public bodies, forecast ahead of the official number and scored on release."),
    ("Public services",
     "Capacity and demand in the systems that run out first, forecast at dated horizons against the official path."),
    ("Regulated industries",
     "Resilience and performance of regulated companies, published as a pre-registered screen and scored on what happens."),
    ("Prices and the economy",
     "National series forecast ahead of the official statistics and the market consensus, marked on release."),
    ("Demographics",
     "Population, households and cohorts, at national and town level, forecast decades out with the backtest published alongside."),
]

# ------------------------------------------------------------------ ledger data

def fmt(d):
    return datetime.date.fromisoformat(d[:10]).strftime("%-d %b %Y") if d else ""


def num(v):
    return "&mdash;" if v is None else f"{v:,}"


REQUIRED_TO_PUBLISH = ("track", "claim_form", "definition", "benchmarks",
                       "scoring_rule", "data_sources", "provenance", "lines")


def check(t):
    """The method page promises each registered track records all of this. Enforce it, so a track
    cannot reach the site while that promise is untrue of it."""
    missing = [f for f in REQUIRED_TO_PUBLISH if not t.get(f)]
    placeholder = [f for f in REQUIRED_TO_PUBLISH
                   if isinstance(t.get(f), str) and t[f].strip().startswith("[")]
    if missing or placeholder:
        raise SystemExit(
            f"\n  {t['id']} is marked registered but is not ready to publish."
            + (f"\n  Missing: {', '.join(missing)}" if missing else "")
            + (f"\n  Still placeholder text: {', '.join(placeholder)}" if placeholder else "")
            + "\n  Fill these in, or clear registered_utc until it is ready.\n")


def load():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "data", "tracks", "*.json"))):
        t = json.load(open(path))
        t["_file"] = os.path.relpath(path, HERE)
        t["_page"] = t["id"] + ".html"
        t["_url"] = "/" + t["id"]
        if PREVIEW and not t.get("registered_utc") and t.get("launch_entry"):
            t["registered_utc"], t["commit"] = t["planned_registration"], "0000000"
        out.append(t)
    out.sort(key=lambda t: t.get("registered_utc") or "9999")
    live = [t for t in out if t.get("registered_utc")]
    names = {n for n, _ in SERIES}
    for t in live:
        check(t)
        t["status"] = track_status(t)
        if t["series"] not in names:
            raise SystemExit(f"\n  {t['id']} has series {t['series']!r}, which is not one of: "
                             + ", ".join(sorted(names)) + "\n")
    return live


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


def track_status(t):
    """Derived, so the table can never contradict itself. Registered until a mark lands,
    open while marks are arriving, closed when every line has resolved."""
    if t.get("withdrawn_reason"):
        return "withdrawn"
    done = [l for l in t["lines"] if l.get("outcome") is not None]
    if not done:
        return "registered"
    return "closed" if len(done) == len(t["lines"]) else "open"


def next_mark(t):
    pending = [l for l in t["lines"] if l.get("outcome") is None]
    return min((l["expected_publication"] for l in pending), default=None)


def totals(tracks):
    lines = sum(len(t["lines"]) for t in tracks)
    resolved = sum(1 for t in tracks for l in t["lines"] if l.get("outcome") is not None)
    return lines, resolved


def summary(tracks):
    lines, resolved = totals(tracks)
    line = f'Tracks {len(tracks)}. Lines registered {lines}. Resolved {resolved}.'
    if tracks:
        first = min(filter(None, (next_mark(t) for t in tracks)), default=None)
        if first:
            line += (f' {"First" if not resolved else "Next"} mark expected {fmt(first)}.')
    return line


def ledger_rows(tracks):
    if not tracks:
        return ('<tr><td class="empty" colspan="6">Nothing registered yet. The first track is '
                'committed to the public repository before its first target, and appears here the '
                'moment it is. The ledger starts empty because a ledger that starts full should '
                'not be believed.</td></tr>')
    out = ""
    for t in tracks:
        # The timestamp of record is the pre-registration commit in the project's own
        # repository, not whatever commit later put the track on this website.
        pr = t["provenance"]
        commit = "https://github.com/" + pr["repository"] + "/commit/" + pr["commit"]
        st = track_status(t)
        benches = ", ".join(b["name"] for b in t["benchmarks"])
        nm = next_mark(t)
        resolved = sum(1 for l in t["lines"] if l.get("outcome") is not None)
        out += f'''
          <tr>
            <td class="claim"><a href="{t["_url"]}">{t["track"]}</a>
              <span class="sub">{len(t["lines"])} lines registered, {resolved} resolved</span></td>
            <td>{t["series"]}</td>
            <td class="bench">{benches}</td>
            <td class="num"><a href="{commit}">{fmt(t.get("registered_utc"))}</a></td>
            <td class="num">{fmt(nm)}</td>
            <td><span class="status s-{st}">{glyph(st)}<span>{st.capitalize()}</span></span></td>
          </tr>'''
    return out


def ledger_table(tracks):
    return f'''<div class="card table-card">
    <div class="table-scroll">
      <table class="ledger">
        <thead>
          <tr><th>Track</th><th>Series</th><th>Benchmarks</th>
              <th>Registered</th><th>Next mark</th><th>Status</th></tr>
        </thead>
        <tbody>{ledger_rows(tracks)}
        </tbody>
      </table>
    </div>
  </div>'''


def exposure(t):
    """How much of the track is a directional call. Computed, so it stays true as lines are
    added and cannot drift from the numbers in the table."""
    lines = t["lines"]
    out = {"n": len(lines), "naive": 0, "seasonal": 0}
    for l in lines:
        lo, hi = l["lower_80"], l["upper_80"]
        for key, field in (("naive", "baseline_naive"), ("seasonal", "baseline_seasonal")):
            v = l.get(field)
            if v is not None and not (lo <= v <= hi):
                out[key] += 1
    return out


def words(n):
    return {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
            8: "Eight", 9: "Nine", 10: "Ten"}.get(n, str(n))


def exposure_note(t):
    e = exposure(t)
    both = min(e["naive"], e["seasonal"])
    if not both:
        return ""
    first, last = t["lines"][0], t["lines"][-1]
    authored = t.get("exposure_note", "")
    return f'''<div class="panel">
    <p class="kicker">What this track is risking</p>
    <p>This is a directional call, not a hedge. The forecast rises from
    {num(t["base_headroom"])} at the base bulletin to {num(max(l["forecast"] for l in t["lines"]))}
    at its peak, while the naive baseline stays flat at {num(first["baseline_naive"])} throughout.
    {words(both)} of the {words(e["n"]).lower()} registered lines place their whole 80% interval clear of both
    baseline values, so if headroom simply stays where it is, those lines miss and breach their
    intervals as well.</p>
    {f"<p>{authored}</p>" if authored else ""}
    <p class="small">That is the point of registering it. A forecast that could not be wrong
    against the obvious alternative would not be worth scoring.</p>
  </div>'''


def by_horizon(t):
    """Once the weekly cadence has run for a while a flat table stops being readable. Lines
    collapse into horizon buckets here; the register CSV always holds every line."""
    weekly = [l for l in t["lines"] if l.get("group") != "founding"]
    if not weekly:
        return ""
    buckets = {}
    for l in weekly:
        b = buckets.setdefault(l["horizon_weeks"], {"n": 0, "done": 0, "err": []})
        b["n"] += 1
        if l.get("outcome") is not None:
            b["done"] += 1
            if l.get("error") is not None:
                b["err"].append(abs(l["error"]))
    rows = ""
    for h in sorted(buckets):
        b = buckets[h]
        mae = f'{sum(b["err"]) / len(b["err"]):,.0f}' if b["err"] else "&mdash;"
        rows += (f'<tr><td class="num strong">{h} weeks</td><td class="num">{b["n"]}</td>'
                 f'<td class="num">{b["done"]}</td><td class="num">{mae}</td></tr>')
    return f'''<h2>Weekly forecasts, by horizon</h2>
  <div class="card table-card"><div class="table-scroll">
    <table class="ledger lines">
      <thead><tr><th>Horizon</th><th>Lines</th><th>Resolved</th><th>Mean absolute error</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div></div>
  <p class="caption">Every individual weekly line, resolved or not, is in the register file.</p>'''


def lines_table(t, only=None):
    rows = ""
    for l in [x for x in t["lines"] if only is None or x.get("group") == only]:
        note = (f'<span class="sub">{l["resolving_note"]}</span>'
                if l.get("resolving_note") else "")
        outcome = ("<span class=\"pending\">awaiting bulletin</span>"
                   if l.get("outcome") is None else num(l["outcome"]))
        rows += f'''
          <tr>
            <td class="num strong">{fmt(l["target_date"])}</td>
            <td class="num">{num(l["forecast"])}</td>
            <td class="num soft">{num(l["lower_80"])} to {num(l["upper_80"])}</td>
            <td class="num soft">{num(l["baseline_naive"])}</td>
            <td class="num soft">{num(l["baseline_seasonal"])}</td>
            <td class="num soft">{num(l["baseline_official"])}</td>
            <td class="num">{fmt(l["expected_publication"])}{note}</td>
            <td class="num">{outcome}</td>
          </tr>'''
    return f'''<div class="card table-card">
    <div class="table-scroll">
      <table class="ledger lines">
        <thead>
          <tr><th>Target</th><th>Forecast</th><th>80% interval</th>
              <th>Naive</th><th>Seasonal</th><th>Official</th>
              <th>Mark expected</th><th>Outcome</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </div>
  </div>'''


def track_page(t):
    first = t["lines"][0]
    claim = (t["claim_form"]
             .replace("{target}", fmt(first["target_date"]))
             .replace("{forecast}", num(first["forecast"]))
             .replace("{lower}", num(first["lower_80"]))
             .replace("{upper}", num(first["upper_80"])))
    p = t["provenance"]
    prov_repo = f'https://github.com/{p["repository"]}'
    benches = "".join(
        f'<div class="series-row"><h3>{b["name"]}</h3><p>{b["definition"]}'
        f'<span class="sub">Edition: {b["edition"]}</span></p></div>'
        for b in t["benchmarks"])
    rules = "".join(f"<li>{r}</li>" for r in t["scoring_rule"])
    sources = "".join(f"<li>{d}</li>" for d in t["data_sources"])
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">{t["series"]}</span></div></div>
    <h1>{t["track"]}</h1>
    <p class="lede">{t["definition"]} Model version {t["model_version"]}, forecast from the
    {fmt(t["base_bulletin"])} bulletin, headroom {num(t["base_headroom"])}.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <div class="panel">
    <p class="kicker">The claim, as registered</p>
    <p class="claim-quote">{claim}</p>
    <p class="small">Every line on this track takes that wording with its own target, forecast and
    interval. The wording is fixed at registration and is never edited.</p>
  </div>

  {exposure_note(t)}

  <h2>The founding set</h2>
  {lines_table(t, only="founding")}
  <p class="caption">{t["cadence"]}</p>
  <p class="caption">{t["superseded_versions"]}</p>

  {by_horizon(t)}
  </div>
</section>

<section class="band">
  <div class="wrap">
  <h2>Benchmarks</h2>
  <div class="series">{benches}</div>
  </div>
</section>

<section class="band">
  <div class="wrap">
  <h2>Scoring rule</h2>
  <div class="card"><ol class="rules">{rules}</ol></div>
  </div>
</section>

<section class="band">
  <div class="wrap">
  <h2>Provenance</h2>
  <div class="cards c2">
    <div class="card">
      <p class="kicker">Source of truth</p>
      <p>The register file, not this page. {p["note"]}</p>
      <p class="small mono"><a href="{prov_repo}/blob/{p["commit"]}/{p["register"]}">{p["repository"]} · {p["register"]}</a><br>
      commit <a href="{prov_repo}/commit/{p["commit"]}">{p["commit"]}</a><br>
      OSF registration {p["osf_registration"]}</p>
    </div>
    <div class="card tint">
      <p class="kicker">Pre-registration and data</p>
      <p class="small mono"><a href="{prov_repo}/blob/{p["commit"]}/{p["preregistration"]}">{p["preregistration"]}</a></p>
      <ul class="ticks">{sources}</ul>
    </div>
  </div>
  </div>
</section>
</main>'''


# ------------------------------------------------------------------ chrome

def header(active):
    cur = ' aria-current="page"'
    links = "\n      ".join(
        f'<a href="{url(k)}"{cur if k == active else ""}>{label}</a>'
        for f, k, label in NAV)
    return f'''<header class="site">
  <div class="wrap site-bar">
    <a class="brand" href="/">
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
      <span>page built {built} &middot; <a href="/about#privacy">privacy</a></span>
    </div>
  </div>
</footer>'''

# ------------------------------------------------------------------ pages

def intro(tracks):
    rows = ""
    for name, desc in SERIES:
        n = sum(1 for t in tracks if t["series"] == name)
        lines = sum(len(t["lines"]) for t in tracks if t["series"] == name)
        if n:
            count = (f'<a href="/ledger">{n} track, {lines} lines</a>' if n == 1
                     else f'<a href="/ledger">{n} tracks, {lines} lines</a>')
        else:
            count = '<span class="soft">nothing registered yet</span>'
        rows += (f'      <div class="area-row"><h3>{name}</h3>'
                 f'<p>{desc}</p><p class="area-count mono">{count}</p></div>\n')

    return f'''<div class="hero">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <p class="kicker">Foresight not hindsight</p>
        <h1>Forecasts with dates on them, scored in public.</h1>
        <p class="lede">Walkforward Research forecasts British public institutions across five
        areas. Each forecast is published before the outcome is known and scored afterwards against
        the official or market number it set out to beat.</p>
      </div>
      <div class="hero-mark">{HERO_STAIR}</div>
    </div>
  </div>
</div>

<main class="wrap">
<section class="band">
  <div class="section-head">
    <h2>What we forecast</h2>
    <p>Five areas, one method. Anything may enter an area if it can be forecast in advance and
    scored on a fixed date against a number somebody official has already published.</p>
  </div>
  <div class="areas">
{rows}  </div>
</section>

<section class="band">
  <div class="section-head">
    <h2>How it works</h2>
    <p>Three steps, in this order, every time. The order is the whole point: once a forecast is
    registered, there is nowhere left to hide.</p>
  </div>
  <div class="cards c3">
    <div class="card">
      <p class="kicker">First</p>
      <h3>Pick a question with a date on it</h3>
      <p>Questions where a decision turns on a number that does not exist yet, and where an official
      body has already put its own number on the record.</p>
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
      Nothing is edited and nothing is quietly dropped.</p>
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
  <p class="measure">What has been registered so far, and how each line stands, is on
  <a href="/ledger">the ledger</a>. The rules it runs on are set out in the
  <a href="/method">method</a>, and the written work is in <a href="/papers">papers</a>.</p>
</section>
</main>'''


def ledger_page(entries):
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">The ledger</span></div></div>
    <h1>Every forecast, its timestamp, and its mark</h1>
    <p class="lede">Append-only. Every line is registered before the outcome is known and never
    edited afterwards. The ledger opens with the prison headroom track; the rest appear as they
    are registered.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <p class="record-summary mono">{summary(entries)}</p>
  {ledger_table(entries)}
  <p class="caption">Each track opens onto its own lines, their benchmarks and the rule they will be
  scored by. <span class="mono">Registered</span> links to the commit that timestamped it.
  <a href="/method#how-it-works">How the ledger works</a>.</p>
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


def papers():
    data = json.load(open(os.path.join(HERE, "data", "papers.json")))
    items = sorted(data.get("papers", []), key=lambda p: p.get("ref", ""), reverse=True)
    published = [p for p in items if p.get("pdf")]
    forthcoming = [p for p in items if not p.get("pdf")]

    def card(p, live):
        meta = [p["ref"]] if p.get("ref") else []
        if p.get("authors"):
            meta.append(", ".join(p["authors"]))
        if p.get("series"):
            meta.append(p["series"])
        if live:
            if p.get("date"):
                meta.append(fmt(p["date"]))
            if p.get("pages"):
                meta.append(f'{p["pages"]} pages')
        else:
            meta.append(p.get("status", "in preparation"))
        title = (f'<a href="/papers/{p["pdf"]}">{p["title"]}</a>' if live else p["title"])
        foot = []
        if live:
            foot.append(f'<a href="/papers/{p["pdf"]}" class="mono">Download the PDF</a>')
        if p.get("doi"):
            foot.append(f'<a href="https://doi.org/{p["doi"]}" class="mono">doi:{p["doi"]}</a>')
        if p.get("related_track"):
            foot.append(f'<a href="/{p["related_track"]}" class="mono">Related forecasts</a>')
        stamp = ""
        if live and (p.get("version") or p.get("licence")):
            bits = [b for b in (f'Version {p["version"]}' if p.get("version") else None,
                                p.get("licence")) if b]
            stamp = f'<p class="paper-stamp mono">{" &middot; ".join(bits)}</p>'
        links = (f'<p class="paper-link">{" &nbsp;&middot;&nbsp; ".join(foot)}</p>'
                 if foot else "")
        return f'''      <article class="card paper{"" if live else " paper-soon"}">
        <p class="note-date">{" &middot; ".join(meta)}</p>
        <h3>{title}</h3>
        <p>{p["standfirst"]}</p>
        {stamp}{links}
      </article>'''

    body = ""
    if published:
        body += ('<div class="papers">' +
                 "\n".join(card(p, True) for p in published) + '</div>')
    else:
        body += '''<div class="panel">
      <p class="kicker">Nothing published yet</p>
      <p>The first paper is in preparation. Papers appear here as PDFs when they are finished, and
      each one links to the forecasts on the ledger that it rests on.</p>
    </div>'''
    if forthcoming:
        body += ('<h2 class="forthcoming-head">In preparation</h2><div class="papers">' +
                 "\n".join(card(p, False) for p in forthcoming) + '</div>')

    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">Papers</span></div></div>
    <h1>The written work</h1>
    <p class="lede">Papers are published when they are finished, not on a schedule. Each one states
    what was forecast, what happened, and what the method got wrong as well as right.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
{body}
  </div>
</section>
</main>'''


def about():
    return f'''<main>
<div class="page-head">
  <div class="wrap">
    <div class="row"><div><span class="chip">About</span></div></div>
    <h1>What this is</h1>
    <p class="lede">Walkforward Research publishes forecasts about British public institutions
    before the outcome is known, and scores them in public afterwards against the official or
    market forecast each one set out to beat.</p>
  </div>
</div>

<section class="band">
  <div class="wrap">
  <div class="cards c2">
    <div class="card">
      <p class="kicker">Authorship</p>
      <h3>Named on the papers</h3>
      <p>Authors are named on each paper. Where work is joint, the paper says so.</p>
      <p>The work is done in a personal capacity, independently of any employer or client.</p>
    </div>
    <div class="card tint">
      <p class="kicker">Contact</p>
      <h3>Two addresses</h3>
      <p>Enquiries: <span class="mono">enquiries@{DOMAIN}</span><br>
      Press: <span class="mono">press@{DOMAIN}</span></p>
    </div>
  </div>
  </div>
</section>

<section class="band" id="privacy">
  <div class="wrap">
  <h2>Privacy</h2>
  <div class="measure">
    <p>This site is a set of static files. It sets no cookies, has no accounts and no mailing
    list.</p>
    <p>The host counts page views in aggregate so we know roughly how many people read something.
    That count uses no cookies and does not identify anyone.</p>
    <p>If you email <span class="mono">enquiries@{DOMAIN}</span>, your
    message and address are used to reply to you and for nothing else. They are not sold, shared or
    added to any list. Ask and they will be deleted.</p>
    <p class="small">Last updated 6 September 2026.</p>
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
    "papers.html": ("papers", "Papers &mdash; Walkforward Research",
                    "Published papers, each stating what was forecast, what happened, and what the method got wrong as well as right.", papers),
    "about.html": ("about", "About &mdash; Walkforward Research",
                   "What Walkforward Research is, how to reach a person, and what this site does and does not collect.", about),
}


def build():
    os.makedirs(OUT, exist_ok=True)
    entries = load()
    for t in entries:
        PAGES[t["_page"]] = ("track", f'{t["track"]} &mdash; Walkforward Research',
                             f'{t["track"]}: the registered lines, their benchmarks and the rule they are scored by.',
                             (lambda tt: (lambda: track_page(tt)))(t))
    for fname, (key, title, desc, fn) in PAGES.items():
        body = fn(entries) if key in ("ledger", "intro") else fn()
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
    src_papers = os.path.join(HERE, "papers")
    if os.path.isdir(src_papers):
        dst = os.path.join(OUT, "papers")
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src_papers):
            if f.startswith("."):
                continue
            with open(os.path.join(src_papers, f), "rb") as r, open(os.path.join(dst, f), "wb") as w:
                w.write(r.read())
    for asset in ("styles.css", "favicon.svg"):
        src = os.path.join(HERE, asset)
        if os.path.exists(src):
            open(os.path.join(OUT, asset), "w").write(open(src).read())
    print(f"site built — {len(entries)} entries in the ledger" + (" (preview)" if PREVIEW else ""))


if __name__ == "__main__":
    build()

# walkforwardresearch.com — full site

Four pages, generated from the forecast files. No CMS, no framework, no client-side JavaScript.

```
python3 build_site.py              # builds site/         — deploy this
python3 build_site.py --preview    # builds site-preview/ — design only, never deploy
```

- `/` **introduction** — what the business does, the three-step order, the standard, the four series
- `/method` — walk-forward scoring, why backtests are not evidence, how the ledger works, status vocabulary
- `/ledger` — record summary and the full table
- `/papers` — published papers, as PDFs
- `/about` — what this is, standing, contact, privacy

Note the ledger moves from `/` (where the holding page keeps it) to `/ledger` here. Anyone who
bookmarked `/` still lands on the introduction, one click away.

## The rule the build enforces

A **track** appears on the site only once `registered_utc` is set in its file, and the build
**refuses** to publish a track that is registered while `claim_form`, `definition`, `benchmarks`,
`scoring_rule`, `data_sources`, `provenance` or `lines` is blank or still placeholder text. The
method page promises each of those is recorded at registration, so the build makes the promise
structurally true rather than merely stated.

The record summary and the per-track counts are computed from the same files as the tables, so
they can never disagree with them.

Registering: fill the entry, set `registered_utc`, commit, push; then put the commit SHA in
`commit` and push again. The first commit is the timestamp, the second only records where to find it.

## Deploy

Cloudflare Pages from the repo. Build command `python3 build_site.py`, output directory `site`.

`REPO` and `DOMAIN` are set at the top of `build_site.py`.

## Replacing the holding page

The holding page and this site share the mark, the palette, the type, the components and the same
`data/forecasts/` format, so switching over in October is a change of build command, not a rebuild.
The ledger stays at `/` and no URL breaks.

## Still open

- **The register file is the source of truth, and this repo currently restates it by hand.** That
  is the one real weakness: two copies can drift. Next step is to have the build read
  `outputs/forecast_register.csv` from `walkforwardresearch/prisoncap` directly, so the site cannot
  disagree with the register even in principle.
- The track gains three lines a week from 11 September. Hand-maintaining `lines` will not survive
  that for long — see the point above.
- The other three tracks (council shortlist, Budget headroom, energy pass-through) are not yet
  written as track files.
- *A generation from now* is listed as a series with no track yet.
- No licence stated on the downloadable data.
- Keep the council screen's working files in a separate private repo — this one is public and so is
  its history.


## Adding a paper

1. Put the PDF in the `papers/` folder at the repo root. Keep the filename lowercase with hyphens,
   e.g. `moj-projection-scorecard-2026.pdf`. The build copies the whole folder into the site.
2. Add or update the entry in `data/papers.json`:

```json
{
  "id": "moj-projection-scorecard-2026",
  "title": "How good have the MoJ prison population projections been?",
  "standfirst": "One sentence saying what it does.",
  "series": "Public services",
  "date": "2026-09-28",
  "status": "published",
  "pdf": "moj-projection-scorecard-2026.pdf",
  "pages": 7,
  "related_track": "prison-headroom"
}
```

An entry with `"pdf": null` is listed under **In preparation** with no download link. Fill in `pdf`,
`date` and `pages` and it moves up into the published list automatically.

Optional fields: `ref` (e.g. `Paper 2026/01`), `version`, `licence`, `doi` (bare, without the
`https://doi.org/` prefix — the link is built for you) and `related_track` (the `id` of a track
file, which adds a "Related forecasts" link).

The PDF itself is typeset from `paper/paper.html` and rendered with `paper/render.js`. Edit the
HTML, run `node render.js`, and copy the output into `papers/`.

# walkforwardresearch.com — full site

Four pages, generated from the forecast files. No CMS, no framework, no client-side JavaScript.

```
python3 build_site.py              # builds site/         — deploy this
python3 build_site.py --preview    # builds site-preview/ — design only, never deploy
```

- `/` **introduction** — what the business does, the three-step order, the standard, the four series
- `/method` — walk-forward scoring, why backtests are not evidence, how the ledger works, status vocabulary
- `/ledger` — record summary and the full table
- `/notes` — occasional write-ups
- `/about` — what this is, standing, contact, privacy

Note the ledger moves from `/` (where the holding page keeps it) to `/ledger` here. Anyone who
bookmarked `/` still lands on the introduction, one click away.

## The rule the build enforces

An entry appears on the site only once `registered_utc` and `commit` are set in its file. The four
entries in `data/forecasts/` are scheduled, not registered, so `site/` is honestly empty today. The
record summary is computed from the same files as the table, so the two can never disagree.

`--preview` shows the **launch state**: only entries carrying `"launch_entry": true` are filled in.
Prison population carries that flag, so the preview opens the ledger with that single row, which is
how it will actually look. Move the flag, or add it to another entry, to preview a different
opening.

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

- The four claims carry `[date]`, `[x]bn`, `[x]pp`. These are the actual forecasts and need real
  numbers before registration.
- *A generation from now* is listed as a series with no entry yet.
- No licence stated on the downloadable data.
- Keep the council screen's working files in a separate private repo — this one is public and so is
  its history.

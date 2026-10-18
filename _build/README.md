# Site build

Nothing in this folder is published (Jekyll skips folders starting with `_`).
The site itself stays plain static HTML; these scripts only regenerate files
that are then committed.

```bash
# from Retirology_Website/
node _build/build-css.mjs                                     # styles/site.css — first,
../Retirology_App/backend/.venv/bin/python _build/build.py   # pages + sitemap (they link to the CSS by its hash)
```

Both need the app repo checked out next to this one (`../Retirology_App`):
`build.py` imports the app's state tax data and tax engine, and
`build-css.mjs` uses the Tailwind compiler in the app's `frontend/node_modules`.

## What `build.py` writes

- `retirement-taxes/` — the state hub and one page per state, from the app's
  `state_tax_data/*.yaml` and the worked examples in `taxcalc.py` (computed
  with the app's own engines, so the site matches the app).
- `guides/`, `alternatives/` — one page per fragment in `content/guides/` and
  `content/alternatives/` (JSON metadata in the leading `<!-- -->` comment,
  then the article body; `{{root}}` becomes the relative path to the site root).
- The shared header, footer and stylesheet links inside the `<!-- site:… -->`
  markers of the hand-written pages (index, privacy, changelog, download, 404),
  plus the version number on the home page (from `version.json`).
- `sitemap.xml`.

## When to run it

- **Every release:** after bumping `version.json`, run `build.py` (updates the
  home page's version and the sitemap dates).
- **Yearly tax refresh:** after the app's state tax YAMLs change, run
  `build.py` — every state page and example is recomputed. Re-check the
  guides' dollar figures (brackets, FPL, ACA percentages) by hand.
- **After adding or changing Tailwind classes** anywhere: run `build-css.mjs`.
- **Competitor prices** in `content/alternatives/` were checked October 2026;
  re-check them when you touch those pages.

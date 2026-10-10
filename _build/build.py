"""Build the generated pages of retirology.app.

    ../Retirology_App/backend/.venv/bin/python _build/build.py

Writes (all committed, served as static files by GitHub Pages):
  retirement-taxes/        index + one page per state, from the app's 2026
                           state tax data and tax engine (see taxcalc.py)
  guides/                  index + one page per file in content/guides/
  alternatives/            index + one page per file in content/alternatives/
  sitemap.xml

The hand-written pages (index, privacy, changelog, download, 404) are not
generated, but they share the header/footer markup below — keep them in sync
when changing navigation. Jekyll skips folders starting with "_", so nothing
in _build/ is published.
"""

from __future__ import annotations

import glob
import html
import json
import re
from datetime import date
from pathlib import Path

import yaml

import taxcalc
from taxcalc import EXAMPLES, compute, state_tax

SITE_DIR = Path(__file__).resolve().parents[1]
CONTENT = Path(__file__).resolve().parent / "content"
STATE_DATA = taxcalc.APP_BACKEND / "retirology" / "data" / "state_tax_data"
SITE = "https://retirology.app/"
TODAY = date.today()
REVIEWED = TODAY.strftime("%B %Y")
OG_IMAGE = SITE + "assets/og-image.png"

esc = html.escape


# ─────────────────────────────── layout ───────────────────────────────

NAV = [
    ("Features", "index.html#features", "features"),
    ("State taxes", "retirement-taxes/", "taxes"),
    ("Guides", "guides/", "guides"),
    ("Compare", "alternatives/", "compare"),
    ("Pricing", "index.html#pricing", "pricing"),
]

ARROW = ('<svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" '
         'd="M7.21 14.77a.75.75 0 0 1 .02-1.06L11.168 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 '
         '1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z" clip-rule="evenodd"/></svg>')


def header(root: str, active: str = "") -> str:
    links = "\n".join(
        f'        <a href="{root}{href}" class="{"text-slate-900" if key == active else "hover:text-slate-900"}">{label}</a>'
        for label, href, key in NAV
    )
    mobile = "\n".join(
        f'          <a href="{root}{href}" class="block rounded-md px-3 py-2 hover:bg-slate-100">{label}</a>'
        for label, href, _ in NAV
    )
    return f"""  <header class="sticky top-0 z-40 backdrop-blur bg-white/85 border-b border-slate-200">
    <div class="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
      <a href="{root}index.html" class="flex items-center gap-2.5" aria-label="Retirology home">
        <img src="{root}assets/logo.png" alt="" width="32" height="32" class="rounded-full" />
        <span class="font-bold text-lg tracking-tight">Retirology</span>
      </a>
      <nav class="hidden md:flex items-center gap-7 text-sm font-medium text-slate-700" aria-label="Primary">
{links}
      </nav>
      <div class="flex items-center gap-2">
        <details class="md:hidden relative">
          <summary class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700">Menu</summary>
          <nav class="absolute right-0 mt-2 w-48 rounded-xl border border-slate-200 bg-white p-2 text-sm font-medium text-slate-700 shadow-lg" aria-label="Mobile">
{mobile}
          </nav>
        </details>
        <a href="{root}index.html#pricing" class="inline-flex items-center gap-1.5 rounded-lg btn-brand-gradient text-white text-sm font-semibold px-3.5 py-2 transition">
          Buy
          {ARROW}
        </a>
      </div>
    </div>
  </header>"""


def footer(root: str) -> str:
    def col(title, items):
        lis = "\n".join(f'            <li><a href="{root}{h}" class="hover:text-slate-900">{t}</a></li>' for t, h in items)
        return f"""        <div>
          <p class="font-semibold text-slate-900">{title}</p>
          <ul class="mt-3 space-y-2">
{lis}
          </ul>
        </div>"""

    return f"""  <footer class="border-t border-slate-200 bg-white">
    <div class="mx-auto max-w-6xl px-4 sm:px-6 py-12">
      <div class="grid gap-10 sm:grid-cols-2 lg:grid-cols-5 text-sm text-slate-600">
        <div class="lg:col-span-1">
          <a href="{root}index.html" class="flex items-center gap-2.5">
            <img src="{root}assets/logo.png" alt="" width="28" height="28" class="rounded-full" />
            <span class="font-bold tracking-tight text-slate-900">Retirology</span>
          </a>
          <p class="mt-3 leading-relaxed">Retirement and FIRE planning software for your desktop. Buy once, every update free.</p>
        </div>
{col("Product", [("Features", "index.html#features"), ("Pricing", "index.html#pricing"), ("Changelog", "changelog.html"), ("Privacy", "privacy.html")])}
{col("Guides", [("Roth conversion ladder", "guides/roth-conversion-ladder.html"), ("ACA subsidy cliff", "guides/aca-subsidy-cliff.html"), ("Rule of 55 vs. 72(t)", "guides/rule-of-55-vs-72t.html"), ("Monte Carlo success rates", "guides/monte-carlo-success-rate.html"), ("Your FI number", "guides/fi-number.html")])}
{col("State taxes", [("All 50 states + DC", "retirement-taxes/"), ("California", "retirement-taxes/california.html"), ("Florida", "retirement-taxes/florida.html"), ("New York", "retirement-taxes/new-york.html"), ("Texas", "retirement-taxes/texas.html")])}
{col("Compare", [("All alternatives", "alternatives/"), ("ProjectionLab", "alternatives/projectionlab.html"), ("Boldin", "alternatives/boldin.html"), ("MaxiFi Planner", "alternatives/maxifi.html"), ("Contact", "mailto:contact@retirology.app")]).replace(f'href="{root}mailto:', 'href="mailto:')}
      </div>
      <p class="mt-10 pt-6 border-t border-slate-200 text-xs text-slate-500 leading-relaxed max-w-3xl">
        © {TODAY.year} Retirology. Retirology is an educational tool. Nothing in the app or on this site is financial, tax, or legal advice — consult a licensed professional for your specific situation.
      </p>
    </div>
  </footer>"""


def page(path: str, *, title: str, description: str, body: str, active: str = "",
         jsonld: list[dict] | None = None, og_type: str = "article") -> None:
    depth = path.count("/")
    root = "../" * depth
    url = SITE + (path[: -len("index.html")] if path.endswith("index.html") else path)
    ld = "\n".join(
        f'  <script type="application/ld+json">\n{json.dumps(d, indent=2, ensure_ascii=False)}\n  </script>'
        for d in (jsonld or [])
    )
    out = f"""<!doctype html>
<!-- Generated by _build/build.py — edit the sources there, not this file. -->
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#16a34a" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <link rel="canonical" href="{url}" />

  <link rel="icon" type="image/x-icon" href="{root}assets/favicon/favicon.ico" />
  <link rel="icon" type="image/png" sizes="96x96" href="{root}assets/favicon/favicon-96x96.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="{root}assets/favicon/apple-touch-icon.png" />
  <link rel="manifest" href="{root}assets/favicon/site.webmanifest" />

  <meta property="og:type" content="{og_type}" />
  <meta property="og:site_name" content="Retirology" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{OG_IMAGE}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{OG_IMAGE}" />

  <link rel="stylesheet" href="{root}styles/site.css" />
  <link rel="stylesheet" href="{root}styles/custom.css" />
{ld}
</head>
<body class="bg-white text-slate-900">

  <a href="#main" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:bg-white focus:text-slate-900 focus:px-3 focus:py-2 focus:rounded-md focus:shadow">Skip to content</a>

{header(root, active)}

  <main id="main">
{body.replace("{{root}}", root)}
  </main>

{footer(root)}

</body>
</html>
"""
    target = SITE_DIR / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out)
    SITEMAP.append(url)


def breadcrumb_ld(trail: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + href}
            for i, (name, href) in enumerate(trail)
        ],
    }


def faq_ld(faq: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
            for q, a in faq
        ],
    }


def article_ld(title: str, description: str, path: str, published: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "mainEntityOfPage": SITE + path,
        "datePublished": published,
        "dateModified": TODAY.isoformat(),
        "author": {"@type": "Organization", "name": "Retirology", "url": SITE},
        "publisher": {"@type": "Organization", "name": "Retirology", "url": SITE,
                      "logo": {"@type": "ImageObject", "url": SITE + "assets/logo.png"}},
        "image": OG_IMAGE,
    }


def crumbs_html(trail: list[tuple[str, str]]) -> str:
    parts = []
    for i, (name, href) in enumerate(trail):
        if i == len(trail) - 1:
            parts.append(f'<span class="text-slate-700">{esc(name)}</span>')
        else:
            parts.append(f'<a href="{{{{root}}}}{href}" class="hover:text-slate-900">{esc(name)}</a>')
    sep = '<span class="text-slate-400" aria-hidden="true">/</span>'
    return f'<nav class="flex flex-wrap items-center gap-2 text-sm text-slate-500" aria-label="Breadcrumb">{sep.join(parts)}</nav>'


def hero(trail, eyebrow: str, h1: str, lede: str, meta: str = "") -> str:
    meta_html = f'\n        <p class="mt-4 text-sm text-slate-500">{meta}</p>' if meta else ""
    return f"""    <section class="hero-halo">
      <div class="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-14 pb-8">
        {crumbs_html(trail)}
        <p class="mt-8 text-sm font-semibold uppercase tracking-wider text-brand-green">{esc(eyebrow)}</p>
        <h1 class="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight leading-[1.1]">{h1}</h1>
        <p class="mt-5 text-lg sm:text-xl text-slate-600 leading-relaxed">{lede}</p>{meta_html}
      </div>
    </section>"""


def cta(heading: str, text: str) -> str:
    return f"""        <aside class="not-prose mt-14 rounded-2xl gradient-ring gradient-ring-glow bg-white p-6 sm:p-8">
          <p class="text-sm font-semibold uppercase tracking-wider text-brand-green">Run it on your own numbers</p>
          <p class="mt-2 text-2xl font-extrabold tracking-tight text-slate-900">{heading}</p>
          <p class="mt-3 text-slate-600 leading-relaxed">{text}</p>
          <div class="mt-5 flex flex-wrap gap-3">
            <a href="{{{{root}}}}index.html#pricing" class="inline-flex items-center gap-2 rounded-lg btn-brand-gradient text-white font-semibold px-5 py-3 no-underline">Buy Retirology — $19+ once</a>
            <a href="{{{{root}}}}index.html#features" class="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white text-slate-900 font-semibold px-5 py-3 hover:bg-slate-50 no-underline">See what it models</a>
          </div>
          <p class="mt-4 text-sm text-slate-500">macOS, Windows and Linux. No account, no subscription — your data never leaves your computer.</p>
        </aside>"""


def faq_html(faq: list[tuple[str, str]], heading: str = "Common questions") -> str:
    items = "\n".join(
        f"""          <details class="group p-5">
            <summary class="flex items-center justify-between gap-4"><span class="font-semibold text-slate-900">{esc(q)}</span><span class="chev text-slate-500">{ARROW}</span></summary>
            <p class="mt-3 mb-0">{a}</p>
          </details>"""
        for q, a in faq
    )
    return f"""        <h2>{heading}</h2>
        <div class="not-prose divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
{items}
        </div>"""


SITEMAP: list[str] = []


# ─────────────────────────────── states ───────────────────────────────

def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def money(v: float) -> str:
    return f"${v:,.0f}"


def load_states() -> list[dict]:
    states = []
    for p in sorted(glob.glob(str(STATE_DATA / "*.yaml"))):
        d = yaml.safe_load(open(p))
        d["slug"] = slug(d["state"])
        d["bullets"] = state_tax.summarize(d)
        d["examples"] = {e["key"]: compute(e, d["code"]) for e in EXAMPLES}
        states.append(d)
    return sorted(states, key=lambda s: s["state"])


def rate_sentence(d: dict) -> str:
    first = d["bullets"][0]
    name = d["state"]
    if first.startswith("No state income tax"):
        return f"{name} has no state income tax."
    m = re.match(r"Flat ([\d.]+%) income tax", first)
    if m:
        return f"{name} has a flat {m.group(1)} income tax."
    m = re.match(r"Income tax from ([\d.]+%) to ([\d.]+%)", first)
    if m:
        return f"{name}'s income tax rates run from {m.group(1)} to {m.group(2)}."
    return first


def classify(d: dict) -> dict:
    b = d["bullets"][1:]
    ss = [x for x in b if x.startswith("Social Security")]
    retirement = [x for x in b if any(k in x for k in ("401(k)", "IRA", "Retirement income", "Pension income"))]
    extra = [x for x in b if x.startswith("Extra")]
    gains = [x for x in b if "apital gains" in x]
    other = [x for x in b if x not in ss + retirement + extra + gains]
    return {"ss": ss, "retirement": retirement, "extra": extra, "gains": gains, "other": other}


def no_tax(d: dict) -> bool:
    return bool(d.get("no_income_tax"))


def ss_cell(s: dict) -> str:
    if no_tax(s):
        return "No income tax"
    c = classify(s)
    b = c["ss"][0] if c["ss"] else ""
    if "isn't taxed" in b or not b:
        return "Not taxed"
    if "as on your federal return" in b:
        return "Taxed"
    return "Partly exempt"


def state_faq(d: dict) -> list[tuple[str, str]]:
    n = d["state"]
    c = classify(d)
    if no_tax(d):
        nt = f"No. {n} has no state income tax, so Social Security, retirement-account withdrawals, pensions and Roth conversions aren't taxed by the state."
        faq = [
            (f"Does {n} tax Social Security?", f"No. {n} has no state income tax."),
            (f"Does {n} tax 401(k) and IRA withdrawals?", nt),
            (f"Does {n} tax pensions?", f"No. {n} has no state income tax."),
            (f"Does {n} tax Roth conversions?", f"No. {n} has no state income tax. Federal income tax still applies to a conversion."),
        ]
        if c["gains"]:
            faq.append((f"Does {n} tax capital gains?", " ".join(c["gains"]) + " Most retirees fall well under that threshold."))
        return faq

    ss = c["ss"][0] if c["ss"] else "Social Security isn't taxed."
    ss_answer = ("No. " + ss) if "isn't taxed" in ss else ss

    def lead(bullets: list[str]) -> str:
        text = " ".join(bullets)
        if all("fully exempt" in x and "income up to" not in x for x in bullets):
            m = re.search(r"from age ([\d½]+)", text)
            return (f"Not from age {m.group(1)} — before then, yes. " if m else "No. ") + text
        return "Partly. " + text

    ret_plan = [x for x in c["retirement"] if any(k in x for k in ("401(k)", "IRA", "Retirement income"))]
    ret_pension = [x for x in c["retirement"] if "ension" in x]
    conv = [x for x in c["retirement"] if "Roth conversion" in x]
    taxed = "Yes, at the state's regular income tax rates."
    extra = (" Also: " + " ".join(x[0].lower() + x[1:] for x in c["extra"])) if c["extra"] else ""
    return [
        (f"Does {n} tax Social Security?", ss_answer),
        (f"Does {n} tax 401(k) and IRA withdrawals?",
         (lead(ret_plan) if ret_plan else f"{taxed} {n} has no special exclusion for retirement-account withdrawals.") + extra),
        (f"Does {n} tax pensions?",
         lead(ret_pension) if ret_pension else f"{taxed} {n} has no special pension exclusion."),
        (f"Does {n} tax Roth conversions?",
         lead(conv) + ("" if all("fully exempt" in x for x in conv) else " Anything above that is taxed like other income.")
         if conv else f"Yes. A Roth conversion counts as income in {n} in the year you convert, taxed at the state's regular rates. Qualified Roth withdrawals later aren't taxed."),
        (f"What is {n}'s income tax rate in 2026?", rate_sentence(d)),
    ]


def brackets_html(d: dict) -> str:
    br = d.get("brackets") or {}
    single, mfj = br.get("single") or [], br.get("mfj") or []
    if len(single) <= 1 and len(mfj) <= 1:
        return ""

    def rows(brs):
        out, lo = [], 0
        for upper, rate in brs:
            if upper is None:
                out.append((f"Over {money(lo)}", rate))
            else:
                out.append((f"{money(lo)} – {money(upper)}" if lo else f"Up to {money(upper)}", rate))
                lo = upper
        return out

    s, m = rows(single), rows(mfj)
    n = max(len(s), len(m))
    trs = "\n".join(
        "            <tr>"
        + (f"<td>{s[i][0]}</td><td class=\"num\">{s[i][1] * 100:g}%</td>" if i < len(s) else "<td></td><td></td>")
        + (f"<td>{m[i][0]}</td><td class=\"num\">{m[i][1] * 100:g}%</td>" if i < len(m) else "<td></td><td></td>")
        + "</tr>"
        for i in range(n)
    )
    indexed = " Brackets are adjusted for inflation each year." if d.get("indexed") else ""
    return f"""        <h2>{d['state']} income tax brackets (2026)</h2>
        <p>Rates apply to {d['state']} taxable income, after the state's deductions and the retirement breaks above.{indexed}</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Single</th><th class="num">Rate</th><th>Married filing jointly</th><th class="num">Rate</th></tr></thead>
            <tbody>
{trs}
            </tbody>
          </table>
        </div>"""


def examples_html(d: dict, ranks: dict) -> str:
    n = d["state"]
    rows = []
    for e in EXAMPLES:
        r = d["examples"][e["key"]]
        rows.append(
            f"            <tr><td><span class=\"font-semibold text-slate-900\">{e['title']}</span><br><span class=\"text-sm\">{e['describe'][0].upper() + e['describe'][1:]}</span></td>"
            f"<td class=\"num\">{money(r['total_income'])}</td><td class=\"num font-semibold text-slate-900\">{money(r['state_tax'])}</td>"
            f"<td class=\"num\">{r['rate'] * 100:.1f}%</td></tr>"
        )
    rank, tied = ranks[d["code"]]
    couple = d["examples"]["couple67"]["state_tax"]
    if couple == 0:
        rank_text = f"That couple would owe nothing in {n} — one of {tied} states (counting DC) where they'd pay $0."
    else:
        rank_text = f"For the retired couple, {n} ranks {ordinal(rank)} lowest of the 50 states and DC."
    return f"""        <h2>What retirees actually pay in {n}: three examples</h2>
        <p>Calculated with Retirology's tax engine under 2026 law, using each state's standard deduction, its retirement breaks and the 2026 federal rules for how much Social Security is taxable. {rank_text}</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Household</th><th class="num">Total income</th><th class="num">{n} tax</th><th class="num">Share</th></tr></thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
        <p class="text-sm text-slate-500">State income tax only — before local taxes, property tax relief and credits not listed above. Federal income tax is extra and the same in every state.</p>"""


def ordinal(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def state_page(d: dict, states: list[dict], ranks: dict) -> None:
    n = d["state"]
    path = f"retirement-taxes/{d['slug']}.html"
    c = classify(d)
    faq = state_faq(d)
    couple = d["examples"]["couple67"]
    title = f"How {n} Taxes Retirement Income (2026) | Retirology"
    first = d["bullets"][0].rstrip(".")
    rate_short = "no income tax" if no_tax(d) else first[0].lower() + first[1:]
    ss_short = {"Not taxed": "Social Security isn't taxed", "Partly exempt": "Social Security is partly exempt",
                "Taxed": "Social Security is taxed"}.get(ss_cell(d), "")
    description = (f"{n} retirement taxes for 2026: {rate_short}" + (f"; {ss_short}" if ss_short else "")
                   + ". How it treats IRAs, pensions and Roth conversions, with examples.")
    lede = (f"{rate_sentence(d)} Here's how {n} treats Social Security, retirement-account withdrawals, pensions and "
            f"Roth conversions in 2026 — and what that means in dollars: a retired couple, both 67, with "
            f"{money(couple['total_income'])} of income pays "
            + (f"<strong class=\"text-slate-900\">nothing</strong> in {n} income tax." if couple["state_tax"] == 0 else
               f"about <strong class=\"text-slate-900\">{money(couple['state_tax'])}</strong> in {n} income tax."))

    rules = "\n".join(f"          <li>{esc(b)}</li>" for b in d["bullets"])
    notes = d.get("notes") or ""
    notes_html = ""
    if notes and not no_tax(d) or (no_tax(d) and c["gains"]):
        notes_html = f"""        <h2>Details and limits</h2>
        <p>{esc(notes)}</p>"""
    locs = d.get("localities") or []
    loc_html = ""
    if locs:
        items = "\n".join(f"          <li>{esc(l['name'])}</li>" for l in locs)
        loc_html = f"""        <h2>Local income taxes</h2>
        <p>Some places in {n} add a local income tax. Retirology models these when you pick your locality:</p>
        <ul>
{items}
        </ul>"""
    srcs = "\n".join(
        f'          <li><a href="{esc(s)}" rel="noopener">{esc(re.sub(r"^https?://(www\.)?", "", s).split("/")[0])}</a></li>'
        for s in d.get("sources") or []
    )
    others = "\n".join(
        f'          <a href="{s["slug"]}.html" class="rounded-md border border-slate-200 px-2.5 py-1.5 hover:border-slate-400 hover:text-slate-900">{s["state"]}</a>'
        for s in states if s["code"] != d["code"]
    )
    trail = [("Home", ""), ("Retirement taxes by state", "retirement-taxes/"), (n, path)]
    body = f"""{hero(trail, "Retirement taxes by state", f"How {esc(n)} taxes retirement income in 2026", lede,
                 f"Updated {REVIEWED} · 2026 tax year")}

    <section class="pb-16">
      <div class="mx-auto max-w-3xl px-4 sm:px-6 prose-rt">
        <div class="not-prose rounded-xl border border-slate-200 bg-slate-50 p-5 sm:p-6">
          <p class="text-sm font-semibold uppercase tracking-wider text-slate-500">{esc(n)} at a glance</p>
          <ul class="mt-3 space-y-2 text-slate-700">
{rules}
          </ul>
        </div>

{faq_html(faq, f"{esc(n)} retirement tax questions")}

{examples_html(d, ranks)}

{brackets_html(d)}

{notes_html}

{loc_html}

{cta(f"See your own {esc(n)} tax, year by year",
     f"Retirology applies {esc(n)}'s rules to every year of your retirement — the age-based breaks, Social Security, Roth conversions and capital gains — alongside federal tax, ACA subsidies and Medicare IRMAA. Move states in one click to compare.")}

        <h2>Sources</h2>
        <p>Rates and rules for the 2026 tax year, from Retirology's state tax data (reviewed {REVIEWED}):</p>
        <ul>
{srcs}
        </ul>
        <p class="text-sm text-slate-500">This page explains state tax rules in general terms. It isn't tax advice — check your state's official instructions or a tax professional for your situation.</p>

        <h2>Other states</h2>
        <div class="not-prose flex flex-wrap gap-2 text-sm text-slate-600">
{others}
        </div>
      </div>
    </section>"""
    body = re.sub(r"\n{3,}", "\n\n", body)
    page(path, title=title, description=description, body=body, active="taxes",
         jsonld=[article_ld(f"How {n} taxes retirement income in 2026", description, path, "2026-10-10"),
                 faq_ld(faq), breadcrumb_ld(trail)])


def state_hub(states: list[dict], ranks: dict) -> None:
    path = "retirement-taxes/index.html"
    none = [s for s in states if no_tax(s)]
    ss_free = [s for s in states if no_tax(s) or any(b.startswith("Social Security isn't taxed") for b in s["bullets"])]
    zero_couple = [s for s in states if s["examples"]["couple67"]["state_tax"] == 0]

    cell_ss = ss_cell

    def cell_ret(s):
        if no_tax(s):
            return "—"
        c = classify(s)
        r = c["retirement"]
        if not r:
            return "None" + (" (senior break only)" if c["extra"] else "")
        covers_iras = any(k in x for x in r for k in ("IRA", "Retirement income"))
        full = all("fully exempt" in x and "income up to" not in x for x in r)
        if full and covers_iras:
            m = re.search(r"from age ([\d½]+)", " ".join(r))
            return "Full exclusion" + (f" from {m.group(1)}" if m else "")
        return "Partial exclusion"

    rows = "\n".join(
        f'            <tr data-tax="{s["examples"]["couple67"]["state_tax"]}" data-name="{s["state"]}">'
        f'<td><a href="{s["slug"]}.html">{s["state"]}</a></td>'
        f'<td>{"None" if no_tax(s) else esc(s["bullets"][0].rstrip(".").replace(" income tax", ""))}</td>'
        f'<td>{cell_ss(s)}</td><td>{cell_ret(s)}</td>'
        f'<td class="num font-semibold text-slate-900">{money(s["examples"]["couple67"]["state_tax"])}</td></tr>'
        for s in states
    )
    cheapest = sorted((s for s in states if not no_tax(s)), key=lambda s: s["examples"]["couple67"]["state_tax"])
    priciest = sorted(states, key=lambda s: -s["examples"]["couple67"]["state_tax"])[:5]
    faq = [
        ("Which states don't tax retirement income?",
         f"{len(none)} states have no income tax at all: {', '.join(s['state'] for s in none)}. "
         f"Several income-tax states also exempt most retirement income — for the example couple below, "
         f"{len(zero_couple) - len(none)} more ({', '.join(s['state'] for s in zero_couple if not no_tax(s))}) collect nothing."),
        ("Which states tax Social Security in 2026?",
         f"{51 - len(ss_free)} states can tax some Social Security in 2026: "
         + ", ".join(s["state"] for s in states if s not in ss_free)
         + ". Most of them exempt it below an income limit or from a certain age."),
        ("Which states tax retirees the most?",
         "For a retired couple with $98,000 of income (half Social Security), the highest state income tax bills are in "
         + ", ".join(f"{s['state']} ({money(s['examples']['couple67']['state_tax'])})" for s in priciest) + "."),
    ]
    trail = [("Home", ""), ("Retirement taxes by state", path)]
    lede = ("How all 50 states and DC tax Social Security, 401(k) and IRA withdrawals, pensions and Roth conversions "
            "in 2026 — with what a typical retired couple actually pays in each.")
    body = f"""{hero(trail, "2026 state tax guide", "How every state taxes retirement income", lede,
                 f"Updated {REVIEWED} · 2026 tax year · {len(states)} jurisdictions")}

    <section class="pb-16">
      <div class="mx-auto max-w-5xl px-4 sm:px-6 prose-rt">
        <div class="not-prose grid sm:grid-cols-3 gap-4">
          <div class="rounded-xl border border-slate-200 bg-white p-5"><p class="text-4xl font-extrabold tracking-tight text-slate-900">{len(none)}</p><p class="mt-1 text-sm text-slate-600">states with no income tax</p></div>
          <div class="rounded-xl border border-slate-200 bg-white p-5"><p class="text-4xl font-extrabold tracking-tight text-slate-900">{len(ss_free)}</p><p class="mt-1 text-sm text-slate-600">states (incl. DC) that don't tax Social Security</p></div>
          <div class="rounded-xl border border-slate-200 bg-white p-5"><p class="text-4xl font-extrabold tracking-tight text-slate-900">{len(zero_couple)}</p><p class="mt-1 text-sm text-slate-600">where our example couple pays $0</p></div>
        </div>

        <h2>Every state, side by side</h2>
        <p>The last column is the state income tax for a retired couple, both 67, with $48,000 of Social Security, $40,000 drawn from IRAs and 401(k)s, and $10,000 of qualified dividends — $98,000 in all. Calculated with Retirology's tax engine under 2026 law. Click a column to sort; click a state for its full rules and more examples.</p>
        <div class="table-wrap">
          <table id="states">
            <thead><tr><th><button type="button" data-sort="name">State</button></th><th>Income tax</th><th>Social Security</th><th>Retirement income break</th><th class="num"><button type="button" data-sort="tax">Couple pays</button></th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
        <p class="text-sm text-slate-500">State income tax only, before local taxes. "Partial exclusion" means a capped amount, an age requirement, or an income limit — see each state's page.</p>

        <h2>Lowest-tax income-tax states for retirees</h2>
        <p>Among states that do have an income tax, these charged the example couple the least: {", ".join(f'<a href="{s["slug"]}.html">{s["state"]}</a> ({money(s["examples"]["couple67"]["state_tax"])})' for s in cheapest[:8])}.</p>

        <h2>Why the same retiree pays such different amounts</h2>
        <p>States don't just differ in rates. What matters most for retirees is which income each state counts:</p>
        <ul>
          <li><strong>Social Security.</strong> Most states don't tax it at all. A handful tax it only above an income limit or before a certain age.</li>
          <li><strong>Retirement-account withdrawals and pensions.</strong> Many states exclude some or all of it, often only from age 55, 59½, 62 or 65 — so an early retiree can pay far more than a 67-year-old with the same income.</li>
          <li><strong>Roth conversions.</strong> A conversion is income in the year you make it. States that exclude "retirement income" sometimes include conversions in that break, and sometimes don't.</li>
          <li><strong>Capital gains.</strong> Most states tax gains like wages; a few exclude part of them or cap the rate.</li>
        </ul>
        <p>That's why the right state can be worth thousands a year — and why the answer depends on your age and the mix of your income, not just the headline rate.</p>

{faq_html(faq, "Questions about state retirement taxes")}

{cta("Compare states with your own plan",
     "Retirology applies your state's 2026 rules to every year of your retirement — exclusions by age, Social Security, Roth conversions and capital gains — together with federal tax, ACA subsidies and IRMAA. Switch states to see the lifetime difference.")}

        <p class="text-sm text-slate-500 mt-10">General information about 2026 state tax rules, not tax advice. Each state page lists its sources.</p>
      </div>
    </section>
    <script>
      // Sort the state table by name or by tax (no tracking, no libraries).
      (function () {{
        var tb = document.querySelector('#states tbody'); var dir = {{}};
        document.querySelectorAll('#states [data-sort]').forEach(function (b) {{
          b.addEventListener('click', function () {{
            var k = b.dataset.sort; dir[k] = !dir[k];
            Array.from(tb.rows).sort(function (x, y) {{
              var a = k === 'tax' ? +x.dataset.tax : x.dataset.name, c = k === 'tax' ? +y.dataset.tax : y.dataset.name;
              return (a > c ? 1 : a < c ? -1 : 0) * (dir[k] ? 1 : -1);
            }}).forEach(function (r) {{ tb.appendChild(r); }});
          }});
        }});
      }})();
    </script>"""
    page(path, title="How Every State Taxes Retirement Income in 2026 (All 50 + DC) | Retirology",
         description=("Does your state tax Social Security, IRA withdrawals, pensions or Roth conversions? A 2026 guide to all 50 "
                      "states and DC, with what a typical retired couple pays in each."),
         body=body, active="taxes",
         jsonld=[article_ld("How every state taxes retirement income in 2026", lede, path, "2026-10-10"),
                 faq_ld(faq), breadcrumb_ld(trail)])


def build_states() -> None:
    states = load_states()
    taxes = sorted(s["examples"]["couple67"]["state_tax"] for s in states)
    ranks = {}
    for s in states:
        t = s["examples"]["couple67"]["state_tax"]
        ranks[s["code"]] = (taxes.index(t) + 1, taxes.count(t))
    for s in states:
        state_page(s, states, ranks)
    state_hub(states, ranks)


# ─────────────────────── guides & alternatives ───────────────────────

def read_fragment(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    m = re.match(r"\s*<!--(.*?)-->\s*(.*)", text, re.S)
    return json.loads(m.group(1)), m.group(2)


def build_section(folder: str, section_name: str, active: str, hub_title: str, hub_h1: str,
                  hub_lede: str, hub_description: str, eyebrow: str) -> None:
    items = []
    for f in sorted((CONTENT / folder).glob("*.html")):
        meta, frag = read_fragment(f)
        meta["slug"] = f.stem
        items.append((meta, frag))
    items.sort(key=lambda x: x[0].get("order", 99))
    for meta, frag in items:
        path = f"{folder}/{meta['slug']}.html"
        trail = [("Home", ""), (section_name, f"{folder}/"), (meta["short"], path)]
        faq = [tuple(x) for x in meta.get("faq", [])]
        related = "\n".join(
            f'          <li><a href="{m["slug"]}.html">{esc(m["h1"])}</a></li>'
            for m, _ in items if m["slug"] != meta["slug"]
        )
        body = f"""{hero(trail, meta.get("eyebrow", eyebrow), meta["h1"], meta["lede"], f"Updated {REVIEWED}")}

    <section class="pb-16">
      <div class="mx-auto max-w-3xl px-4 sm:px-6 prose-rt">
{frag.strip()}

{faq_html(faq) if faq else ""}

{cta(meta.get("cta_heading", "Model this for your own plan"), meta.get("cta_text", "Retirology runs your whole plan year by year — taxes, Roth conversions, ACA subsidies, Social Security and Monte Carlo — on your own computer."))}

        <h2>Keep reading</h2>
        <ul>
{related}
          <li><a href="{{{{root}}}}retirement-taxes/">How every state taxes retirement income</a></li>
        </ul>
      </div>
    </section>"""
        ld = [article_ld(meta["h1"], meta["description"], path, meta.get("published", "2026-10-10")), breadcrumb_ld(trail)]
        if faq:
            ld.append(faq_ld(faq))
        page(path, title=meta["title"], description=meta["description"], body=body, active=active, jsonld=ld)

    cards = "\n".join(
        f"""          <a href="{m['slug']}.html" class="block rounded-xl border border-slate-200 bg-white p-6 hover:border-slate-400 transition no-underline">
            <p class="text-lg font-bold tracking-tight text-slate-900">{esc(m['h1'])}</p>
            <p class="mt-2 text-slate-600 leading-relaxed">{esc(m['card'])}</p>
          </a>"""
        for m, _ in items
    )
    path = f"{folder}/index.html"
    trail = [("Home", ""), (section_name, f"{folder}/")]
    body = f"""{hero(trail, eyebrow, hub_h1, hub_lede)}

    <section class="pb-16">
      <div class="mx-auto max-w-4xl px-4 sm:px-6">
        <div class="grid sm:grid-cols-2 gap-4">
{cards}
        </div>
      </div>
    </section>"""
    page(path, title=hub_title, description=hub_description, body=body, active=active,
         jsonld=[breadcrumb_ld(trail)], og_type="website")


# ──────────────────────── hand-written pages ────────────────────────

STATIC_PAGES = {"index.html": "", "privacy.html": "", "changelog.html": "",
                "download.html": "", "404.html": "/"}  # 404 is served at any depth


def sync_static_pages() -> None:
    """Fill the <!-- site:… --> regions of the hand-written pages with the
    shared stylesheet links, header and footer."""
    for name, root in STATIC_PAGES.items():
        p = SITE_DIR / name
        s = p.read_text()
        parts = {
            "css": (f'  <link rel="stylesheet" href="{root}styles/site.css" />\n'
                    f'  <link rel="stylesheet" href="{root}styles/custom.css" />'),
            "header": header(root),
            "footer": footer(root),
        }
        if name == "index.html":
            # Version shown in the hero and the structured data follows version.json.
            version = json.loads((SITE_DIR / "version.json").read_text())["version"]
            s = re.sub(r'"softwareVersion": "[^"]*"', f'"softwareVersion": "{version}"', s)
            s = re.sub(r"Version \d+\.\d+\.\d+", f"Version {version}", s)
        for key, html_ in parts.items():
            s, n = re.subn(rf"(  <!-- site:{key} -->\n).*?(  <!-- /site:{key} -->)",
                           lambda m: m.group(1) + html_ + "\n" + m.group(2), s, flags=re.S)
            assert n == 1, (name, key)
        p.write_text(s)


# ─────────────────────────────── sitemap ───────────────────────────────

def build_sitemap() -> None:
    static = [SITE, SITE + "privacy.html", SITE + "changelog.html"]
    urls = static + [u for u in SITEMAP if u not in static]
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY.isoformat()}</lastmod>\n  </url>" for u in urls
    )
    (SITE_DIR / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n"
    )


if __name__ == "__main__":
    build_states()
    build_section(
        "guides", "Guides", "guides",
        hub_title="Early Retirement & FIRE Planning Guides | Retirology",
        hub_h1="Guides to planning an early retirement",
        hub_lede="Plain-English explanations of the moves that matter most when you retire early: getting at retirement money before 59½, keeping health insurance affordable, and knowing how much is enough.",
        hub_description="Plain-English guides to Roth conversion ladders, the ACA subsidy cliff, the Rule of 55 and 72(t), Monte Carlo success rates and your FI number.",
        eyebrow="Guides",
    )
    build_section(
        "alternatives", "Compare", "compare",
        hub_title="Retirology vs. ProjectionLab, Boldin & Other Planners",
        hub_h1="How Retirology compares",
        hub_lede="Honest side-by-sides with the retirement planners and budgeting apps people usually weigh it against — what each costs, where your data lives, and when the other tool is the better pick.",
        hub_description="Retirology compared with ProjectionLab, Boldin, MaxiFi, Pralana, Empower, Monarch, YNAB and free FIRE calculators: pricing, privacy and features.",
        eyebrow="Compare",
    )
    sync_static_pages()
    build_sitemap()
    print(f"built {len(SITEMAP)} pages + sitemap")

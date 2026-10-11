# Builds the static website in site/ from the files in data/clean.
# Every page is plain HTML with one shared stylesheet and one small script for
# the search box, so it can be served by Cloudflare Pages without a build step.
import csv
import html
import json
import re
from collections import defaultdict

DATA_DATE = "8 October 2026"
FILINGS_TO = "31 March 2026"
REPO = "https://github.com/t4zc4t/market-study"

checks = defaultdict(dict)
for r in csv.DictReader(open("data/clean/checks.csv")):
    checks[r["symbol"]][int(r["check"])] = r
scores = {r["symbol"]: r for r in csv.DictReader(open("data/clean/scores.csv"))}
universe = {r["symbol"]: r for r in csv.DictReader(open("data/clean/universe.csv"))}
lists = json.load(open("data/raw/nse_filing_lists.json"))
xidx = list(csv.DictReader(open("data/raw/xbrl/index.csv")))
shp_idx = {r["symbol"]: r["file"] for r in csv.DictReader(open("data/raw/shareholding/index.csv"))}

THRESH = {
    1: "Well outside above −1.78, mildly outside above −2.22",
    2: "Well outside below 0.5, mildly outside below 0.8",
    3: "Well outside above 10%, mildly outside above 5%",
    4: "Well outside if up more than 50%, mildly outside if up 25% to 50%",
    5: "Well outside if up more than 50%, mildly outside if up 25% to 50%",
    6: "Well outside above 30%, mildly outside above 15%",
    7: "Well outside above 50%, mildly outside above 25%",
    8: "Well outside above 20%, mildly outside above 10%",
    9: "Well outside above 25%, mildly outside above 10%",
    10: "Well outside above 20 points a year, mildly outside above 10 points",
    11: "Well outside above 25%, mildly outside above 10%",
    12: "Well outside if down more than 10 points, mildly outside if down 5 to 10 points",
    13: "Well outside if yes",
    14: "Well outside for a qualified, adverse or disclaimer opinion, mildly outside for an emphasis of matter",
    15: "Well outside above 25%, mildly outside above 10%",
    16: "Well outside for two or more, mildly outside for one",
}
LABEL = {"no flag": "Within range", "mild": "Mildly outside", "strong": "Well outside", "not scored": "Not scored"}
CLS = {"no flag": "r0", "mild": "r1", "strong": "r2", "not scored": "rn"}
GROUPS = [("earnings", "Earnings quality", range(1, 7)), ("balance sheet", "Balance sheet", range(7, 11)),
          ("governance", "Governance", range(11, 17))]

def slug(sym):
    return re.sub(r"[^a-z0-9]+", "-", sym.lower()).strip("-")

def ar_url(sym):
    ar = lists[sym]["ar"]
    ar = ar.get("data", ar) if isinstance(ar, dict) else ar
    fy = [a for a in ar if a["fromYr"] == "2025" and a["toYr"] == "2026"]
    fy.sort(key=lambda a: a.get("broadcast_dttm") or "", reverse=True)
    return fy[0]["fileName"] if fy else None

def xbrl_url(sym):
    b = "C" if scores[sym]["basis"] == "consolidated" else "S"
    f = [r["file"] for r in xidx if r["symbol"] == sym and r["fy"] == "2026" and r["basis"] == b]
    return "https://nsearchives.nseindia.com/corporate/xbrl/" + f[0] if f else None

def source_link(sym, row):
    src = row["source"]
    m = re.search(r"annual report p(\d+)", src)
    if m and ar_url(sym):
        return f'<a href="{ar_url(sym)}#page={m.group(1)}">FY2026 annual report, PDF page {m.group(1)}</a>'
    if src.startswith("NSE results XBRL"):
        b = "C" if scores[sym]["basis"] == "consolidated" else "S"
        yrs = sorted((r["fy"], r["file"]) for r in xidx if r["symbol"] == sym and r["basis"] == b)
        links = ", ".join(f'<a href="https://nsearchives.nseindia.com/corporate/xbrl/{f}">FY{fy}</a>' for fy, f in yrs)
        return f"Results filed with NSE (XBRL): {links}"
    if src == "shareholding patterns":
        return f'<a href="https://www.nseindia.com/get-quotes/equity?symbol={html.escape(sym)}">Quarterly shareholding patterns on NSE</a>'
    if src.startswith("shareholding pattern ") and sym in shp_idx:
        return f'<a href="https://nsearchives.nseindia.com/corporate/xbrl/{shp_idx[sym]}">Shareholding pattern, 31 March 2026 (XBRL)</a>'
    if src == "shareholding patterns":
        return f'<a href="https://www.nseindia.com/get-quotes/equity?symbol={html.escape(sym)}">Quarterly shareholding patterns on NSE</a>'
    return html.escape(src) + f' (<a href="https://www.nseindia.com/get-quotes/equity?symbol={html.escape(sym)}">NSE filings</a>)'

def page(title, body, depth=0, desc="", band=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc or 'An educational study that runs sixteen fixed checks on public filings of 24 Nifty Smallcap 100 companies. Not investment advice.')}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc or 'An educational study that runs sixteen fixed checks on public filings of 24 Nifty Smallcap 100 companies. Not investment advice.')}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0D2136">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<div class="notice">Educational project, not investment advice. <a href="{up}disclaimer.html">Read the disclaimer</a></div>
<header class="band">
  <div class="wrap top">
    <a class="home" href="{up}index.html">Market Study</a>
    <nav><a href="{up}index.html">Companies</a><a href="{up}method.html">How it works</a><a href="{up}validation.html">Validation</a><a href="{up}disclaimer.html">Disclaimer</a></nav>
  </div>
  {band}
</header>
<main class="wrap">
{body}
</main>
<footer>
  <div class="wrap">
  <p>Market Study is an independent educational project. It is not investment advice or a recommendation to buy, sell or hold any security, and it is not research by a SEBI registered research analyst or investment adviser. The author holds no position in any company covered. Results are mechanical outputs of fixed checks on public filings and are not a statement about the conduct of any company or person. Not affiliated with NSE, BSE, SEBI or any company named. Data downloaded on {DATA_DATE}, covering filings up to {FILINGS_TO}, and may contain errors. <a href="{up}disclaimer.html">Full disclaimer</a>. <a href="{REPO}/issues">Report an error or request a review</a>.</p>
  </div>
</footer>
</body>
</html>
"""

def cell(r, no, big=False):
    name = CHECK_NAMES[no]
    return f'<span class="cell {CLS[r]}{" big" if big else ""}" title="{no}. {html.escape(name)}: {LABEL[r].lower()}">{no if big else ""}</span>'

CHECK_NAMES = {}
for no in range(1, 17):
    CHECK_NAMES[no] = checks["AARTIIND"][no]["name"].split(" (")[0].split(", FY")[0].split(", Mar")[0].split(", average")[0]

# Company pages
for sym, s in scores.items():
    C = checks[sym]
    name = s["company"]
    cells = "".join(cell(C[i]["result"], i, True) + ('<span class="sep"></span>' if i in (6, 10) else "") for i in range(1, 17))
    band = f"""<div class="wrap hero co">
  <p class="crumb"><a href="../index.html">All companies</a></p>
  <h1>{html.escape(name)}</h1>
  <p class="meta">{html.escape(s['industry'])}, NSE symbol {html.escape(sym)}, {s['basis']} figures</p>
  <div class="cohead">
    <div class="num"><span class="big">{s['indicator_score'] or '–'}</span><span class="of">{'indicator score out of 100' if s['indicator_score'] else 'too few checks for a score'}</span></div>
    <div class="cells">{cells}</div>
  </div>
  <p class="sub">Earnings quality {s['earnings_score']}, balance sheet {s['balance_sheet_score']}, governance {s['governance_score']}. {s['checks_with_data']} of 16 checks had data.</p>
</div>"""
    body = ['<p class="lede">A higher score only means more of this company\'s figures sit outside ranges the checks treat as typical, often for ordinary business reasons. It is not a judgement on the company. Every value below links to the filing it came from.</p>']
    if s["data_notes"]:
        body.append(f'<p class="note">Data note: {html.escape(s["data_notes"])}</p>')
    for gkey, gname, nos in GROUPS:
        body.append(f"<section class='grp'><h2>{gname}</h2><div class='checks'>")
        for no in nos:
            r = C[no]
            note = r["note"][:1].upper() + r["note"][1:] if r["note"] else ""
            body.append(f"""<article class="chk {CLS[r['result']]}">
  <div class="chk-top"><span class="no">{no}</span><h3>{html.escape(r['name'])}</h3><span class="res">{LABEL[r['result']]}</span></div>
  <p class="val">{html.escape(r['shown']) or '—'}</p>
  <p class="th">{THRESH[no]}</p>
  {f'<p class="nt">{html.escape(note)}</p>' if note else ''}
  <p class="src">{source_link(sym, r)}</p>
</article>""")
        body.append("</div></section>")
    body.append(f"""<section class="grp"><h2>Altman Z score</h2><div class="zbox"><span class="z">{s['altman_z']}</span>
<p>Range {s['z_range']}. This looks at financial strain rather than accounting quality, so it is shown separately and not added into the indicator score. It uses the emerging markets version of the formula, set out on the <a href="../method.html">how it works</a> page.</p></div></section>""")
    order = sorted(scores, key=lambda k: scores[k]["company"])
    i = order.index(sym)
    prv, nxt = order[i - 1], order[(i + 1) % len(order)]
    body.append(f'''<nav class="pager"><a href="{slug(prv)}.html">Previous: {html.escape(scores[prv]['company'])}</a><a href="../index.html">All companies</a><a href="{slug(nxt)}.html">Next: {html.escape(scores[nxt]['company'])}</a></nav>''')
    open(f"site/c/{slug(sym)}.html", "w").write(page(f"{name} | Market Study", "\n".join(body), 1, band=band,
        desc=f"Results of sixteen fixed checks on public filings of {name}, with links to every source. Educational, not investment advice."))

# Index page: alphabetical matrix, filters, no ranking
rows = []
for sym, s in sorted(scores.items(), key=lambda kv: kv[1]["company"]):
    C = checks[sym]
    strip = "".join(cell(C[i]["result"], i) + ('<span class="sep"></span>' if i in (6, 10) else "") for i in range(1, 17))
    flagged = " ".join(str(i) for i in range(1, 17) if C[i]["result"] in ("mild", "strong"))
    nout = sum(1 for i in range(1, 17) if C[i]["result"] in ("mild", "strong"))
    rows.append(f"""<li style="--d:{len(rows)*25}" data-name="{html.escape(s['company'].lower())} {sym.lower()}" data-ind="{html.escape(s['industry'])}" data-band="{s['band']}" data-checks=" {flagged} ">
<a href="c/{slug(sym)}.html"><span class="co-name">{html.escape(s['company'].replace(' Ltd.', ''))}<small>{html.escape(s['industry'])}</small></span>
<span class="strip" role="img" aria-label="{nout} of 16 checks outside the typical range">{strip}</span><span class="sc">{s['indicator_score'] or '<em>incomplete</em>'}</span></a></li>""")
inds = sorted({s["industry"] for s in scores.values()})
bands = ["0-24", "25-49", "50-74", "75-100", "incomplete"]
check_opts = "".join(f'<option value="{i}">{i}. {html.escape(CHECK_NAMES[i])}</option>' for i in range(1, 17))
key = "".join(f'<li><span class="kno">{i}</span>{html.escape(CHECK_NAMES[i])}</li>' for i in range(1, 17))
heads = "".join(f'<span class="hcell">{i}</span>' + ('<span class="sep"></span>' if i in (6, 10) else "") for i in range(1, 17))
band = f"""<div class="wrap hero">
  <h1>Sixteen checks on the filings of 24 smallcap companies</h1>
  <p class="lede">Each company's annual results, shareholding patterns, announcements and annual report run through the same fixed accounting and governance checks. Every square below is one check, and every number behind it links to the filing it came from.</p>
  <p class="small">The 24 were drawn at random, within each industry, from the non financial Nifty Smallcap 100 companies listed before April 2024. Listed alphabetically, never ranked.</p>
</div>"""
index = f"""<form class="filters" onsubmit="return false">
  <label>Search<input id="q" type="search" placeholder="Company or symbol"></label>
  <label>Industry<select id="ind"><option value="">All industries</option>{''.join(f'<option>{html.escape(i)}</option>' for i in inds)}</select></label>
  <label>Score band<select id="band"><option value="">All bands</option>{''.join(f'<option>{b}</option>' for b in bands)}</select></label>
  <label>Outside range on<select id="chk"><option value="">Any check</option>{check_opts}</select></label>
</form>
<p class="count small" id="count" aria-live="polite">Showing all 24 companies</p>
<div class="matrix">
  <div class="mhead"><span class="co-name">Company</span><span class="strip groups"><span class="g g1">Earnings</span><span class="sep"></span><span class="g g2">Balance sheet</span><span class="sep"></span><span class="g g3">Governance</span></span><span class="sc">Score</span></div>
  <div class="mhead nums"><span class="co-name"></span><span class="strip">{heads}</span><span class="sc"></span></div>
  <ul class="list" id="list">
{''.join(rows)}
  </ul>
  <p id="none" class="small" hidden>No company matches these filters. Clear a filter to see more.</p>
</div>
<div class="legend"><span><span class="cell r0"></span>Within range</span><span><span class="cell r1"></span>Mildly outside</span><span><span class="cell r2"></span>Well outside</span><span><span class="cell rn"></span>Not scored</span></div>
<section class="keysec"><h2>The sixteen checks</h2><ol class="key">{key}</ol><p class="small">Thresholds and formulas for each one are on the <a href="method.html">how it works</a> page.</p></section>
<script>
const f=['q','ind','band','chk'].map(id=>document.getElementById(id));
function run(){{const q=f[0].value.trim().toLowerCase();let n=0;
for(const li of document.querySelectorAll('#list li')){{
const ok=(!q||li.dataset.name.includes(q))&&(!f[1].value||li.dataset.ind===f[1].value)&&(!f[2].value||li.dataset.band===f[2].value)&&(!f[3].value||li.dataset.checks.includes(' '+f[3].value+' '));
li.hidden=!ok;if(ok)n++}}
document.getElementById('none').hidden=n>0;
document.getElementById('count').textContent=n===24?'Showing all 24 companies':'Showing '+n+' of 24 companies'}}
f.forEach(e=>e.addEventListener('input',run));
</script>"""
open("site/index.html", "w").write(page("Market Study | Sixteen checks on 24 smallcap filings", index, band=band))

# Method, validation and disclaimer pages come from markdown-ish text kept in site_text/
def md(text):
    out, para = [], []
    for line in text.split("\n"):
        if line.startswith("# "):
            continue
        if line.startswith("## ") or line.startswith("### "):
            if para: out.append("<p>" + " ".join(para) + "</p>"); para = []
            lvl = 2 if line.startswith("## ") else 3
            out.append(f"<h{lvl}>{html.escape(line.lstrip('#').strip())}</h{lvl}>")
        elif not line.strip():
            if para: out.append("<p>" + " ".join(para) + "</p>"); para = []
        else:
            para.append(html.escape(line.strip()))
    if para: out.append("<p>" + " ".join(para) + "</p>")
    return "\n".join(out)

method = "<p class=\"note\">This page is the project's scope and method file as written. Where it says no flag, mild and strong, the company pages show those results as within range, mildly outside and well outside.</p>\n" + md(open("scope&method.md").read())
open("site/method.html", "w").write(page("How it works | Market Study", f'<article class="prose">{method}</article>', band='<div class="wrap hero"><h1>How it works</h1><p class="lede">The full scope and method file, with every check, threshold and edge case, written before any data was collected.</p></div>'))

vrows = list(csv.DictReader(open("validation/gensol_checks.csv")))
vbody = "".join(f"""<article class="chk {CLS[r['result']]}"><div class="chk-top"><span class="no">{r['check']}</span><h3>{html.escape(r['name'])}</h3><span class="res">{LABEL[r['result']]}</span></div><p class="val">{html.escape(r['shown'])}</p></article>""" for r in vrows)
val = open("site_text/validation.txt").read()
vcells = "".join(cell(r["result"], int(r["check"]), True) + ('<span class="sep"></span>' if r["check"] in ("6", "10") else "") for r in vrows)
open("site/validation.html", "w").write(page("Validation | Market Study",
    f'<article class="prose">{md(val)}</article><section class="grp"><h2>Check by check, as of the FY2024 annual report</h2><div class="checks">{vbody}</div></section>',
    band=f'<div class="wrap hero co"><h1>Checking the method on Gensol Engineering</h1><div class="cohead"><div class="num"><span class="big">50.0</span><span class="of">as of the FY2024 accounts, 14 of 16 checks scored</span></div><div class="cells">{vcells}</div></div></div>'))
open("site/disclaimer.html", "w").write(page("Disclaimer | Market Study", f'<article class="prose">{md(open("site_text/disclaimer.txt").read())}</article>', band='<div class="wrap hero"><h1>Disclaimer</h1><p class="lede">Please read this before using anything on this site.</p></div>'))
open("site/404.html", "w").write(page("Page not found | Market Study", '<p class="lede">That page doesn\'t exist. <a href="index.html">Go to the list of companies</a>.</p>', band='<div class="wrap hero"><h1>Page not found</h1></div>'))
print("built", len(scores), "company pages")

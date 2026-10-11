# Pulls promoter holding, promoter pledging and the announcements about auditor
# and key managerial changes out of the NSE filing lists into data/clean.
import csv
import json
import re

RAW = "data/raw/nse_filing_lists.json"
d = json.load(open(RAW))

# Promoter and promoter group holding from each quarterly shareholding filing.
with open("data/clean/promoter_holding.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["symbol", "as_of", "promoter_pct", "source"])
    for sym, o in d.items():
        for x in o["shp"] or []:
            w.writerow([sym, x["date"], x["pr_and_prgrp"], x.get("xbrl") or ""])

# Latest pledge disclosure. percPromoterShares is the share of promoter holding
# that is pledged, percTotShares the same shares as a share of all shares.
with open("data/clean/promoter_pledge.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["symbol", "pledged_pct_of_promoter_holding",
                "pledged_pct_of_total_shares", "promoter_shares_pledged",
                "source_broadcast"])
    for sym, o in d.items():
        p = o["pledge"]
        p = (p.get("data") if isinstance(p, dict) else p) or []
        if not p:
            w.writerow([sym, "", "", "", ""])
            continue
        x = p[0]
        clean = lambda v: (str(v).strip() if v not in (None, "None") else "")
        w.writerow([sym, clean(x.get("percPromoterShares")),
                    clean(x.get("percTotShares")), clean(x.get("totPromoterShares")),
                    clean(x.get("broadcastDt"))])

# Announcements that can show an auditor change or a CFO or company secretary
# leaving. These still get read by hand before any check uses them.
CATS = re.compile(r"auditor|resignation|cessation|company secretary|"
                  r"key managerial|change in management", re.I)
with open("data/clean/governance_announcements.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["symbol", "date", "category", "text", "attachment"])
    n = 0
    for sym, o in d.items():
        for a in o["ann"]:
            if CATS.search(a["desc"] or ""):
                w.writerow([sym, a["dt"], a["desc"], " ".join((a["text"] or "").split()), a["file"]])
                n += 1
print(f"{n} announcements kept for reading")

# Builds the list of companies the checks run on, from the Nifty Smallcap 100
# list and NSE's equity list (for listing dates).
import csv
import random
from collections import defaultdict
from datetime import datetime

INDEX_FILE = "data/raw/ind_niftysmallcap100list.csv"
NSE_FILE = "data/raw/nse_equity_list.csv"
OUT_FILE = "data/clean/universe.csv"

# Listed before this date means FY2024, FY2025 and FY2026 annual results were
# all filed as a listed company, which is the three years the trend checks need.
CUTOFF = datetime(2024, 4, 1)

# The checks run on a sample of 24 of the eligible companies. The sample is
# drawn at random within each industry, in proportion to how many eligible
# companies that industry has, so no company is picked by hand. The seed is
# the date the index list was downloaded, so anyone can redo the same draw.
SAMPLE_SIZE = 24
SEED = 20261007

# NSE's date is only the NSE listing. These were listed on BSE long before.
EARLIER_BSE_LISTING = {
    "FORCEMOT": "listed on BSE for decades, NSE listing only in 2024",
}

with open(NSE_FILE, newline="") as f:
    nse = {r["SYMBOL"].strip(): r for r in csv.DictReader(f, skipinitialspace=True)}

rows = []
with open(INDEX_FILE, newline="") as f:
    for r in csv.DictReader(f):
        sym = r["Symbol"].strip()
        listed = datetime.strptime(nse[sym]["DATE OF LISTING"].strip(), "%d-%b-%Y")
        if r["Industry"] == "Financial Services":
            keep, reason = "no", "financial services company"
        elif listed >= CUTOFF and sym not in EARLIER_BSE_LISTING:
            keep, reason = "no", "fewer than three years of listed annual filings"
        else:
            keep, reason = "yes", EARLIER_BSE_LISTING.get(sym, "")
        rows.append({
            "symbol": sym,
            "company": r["Company Name"],
            "industry": r["Industry"],
            "isin": r["ISIN Code"],
            "nse_listing_date": listed.strftime("%Y-%m-%d"),
            "included": keep,
            "note": reason,
        })

# Proportional allocation by industry, largest remainder for the leftovers.
eligible = [r for r in rows if r["included"] == "yes"]
by_ind = defaultdict(list)
for r in eligible:
    by_ind[r["industry"]].append(r)
quota = {i: SAMPLE_SIZE * len(v) / len(eligible) for i, v in by_ind.items()}
take = {i: int(q) for i, q in quota.items()}
left = SAMPLE_SIZE - sum(take.values())
for i in sorted(quota, key=lambda i: (-(quota[i] - take[i]), i))[:left]:
    take[i] += 1

rng = random.Random(SEED)
picked = set()
for i in sorted(by_ind):
    syms = sorted(r["symbol"] for r in by_ind[i])
    picked.update(rng.sample(syms, take[i]))
for r in rows:
    r["in_sample"] = "yes" if r["symbol"] in picked else "no"

with open(OUT_FILE, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

kept = [r for r in rows if r["included"] == "yes"]
print(f"{len(rows)} in the index, {len(kept)} kept")
for reason in sorted({r["note"] for r in rows if r["included"] == "no"}):
    n = sum(1 for r in rows if r["note"] == reason)
    print(f"  dropped, {reason}: {n}")
print(f"{len(picked)} in the sample")

# Runs the 16 checks and the Altman Z score described in scope&method.md and
# writes data/clean/checks.csv (one row per company and check) and
# data/clean/scores.csv (one row per company).
import csv
import re
from collections import defaultdict

UNIT = {"lakh": 1e5, "crore": 1e7, "million": 1e6}
STUDY_START, STUDY_END = 2022, 2026

fin = defaultdict(dict)
for r in csv.DictReader(open("data/clean/financials.csv")):
    row = {}
    for k, v in r.items():
        try:
            row[k] = float(v)
        except ValueError:
            row[k] = v
    fin[r["symbol"]][int(r["fy"])] = row

# Company-years where the XBRL a company filed with NSE doesn't hold together.
# The fields listed are blanked so no check uses them, and the note goes on
# the company page.
DATA_ISSUES = {
    ("SYRMA", 2023): (
        ["CostOfMaterialsConsumed", "PurchasesOfStockInTrade",
         "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade",
         "EmployeeBenefitExpense", "FinanceCosts", "DepreciationDepletionAndAmortisationExpense",
         "OtherExpenses", "Expenses", "ProfitBeforeTax", "ProfitLossForPeriod",
         "CashFlowsFromUsedInOperatingActivities", "OtherIncome"],
        "In the FY2023 results XBRL the full year costs are smaller than the fourth quarter alone and full year profit is "
        "larger than 70% of revenue, so FY2023 profit, cost and cash flow figures are not used."),
    ("KIRLOSENG", 2023): (
        ["TradeReceivablesCurrent", "TradeReceivablesNoncurrent"],
        "In the FY2023 and FY2024 results XBRL the lending subsidiary's loans are tagged as trade receivables "
        "(from FY2025 they are tagged as loans), so receivables for those years are not used."),
    ("KIRLOSENG", 2024): (["TradeReceivablesCurrent", "TradeReceivablesNoncurrent"], ""),
}
for (sym, fy), (fields, _) in DATA_ISSUES.items():
    for k in fields:
        fin[sym][fy][k] = ""

ar = defaultdict(dict)
for r in csv.DictReader(open("data/clean/annual_report_items.csv")):
    v = float(r["value"]) * UNIT[r["unit"]] if r["value"] != "" else None
    ar[r["symbol"]][r["item"]] = (v, r["pdf_page"], r["note"])

gov = {r["symbol"]: r for r in csv.DictReader(open("data/clean/governance_review.csv"))}
universe = {r["symbol"]: r for r in csv.DictReader(open("data/clean/universe.csv")) if r["in_sample"] == "yes"}

holding = defaultdict(dict)
for r in csv.DictReader(open("data/clean/promoter_holding.csv")):
    holding[r["symbol"]][r["as_of"].upper()] = float(r["promoter_pct"])

# Promoter shares pledged or otherwise encumbered, from the 31 March 2026
# shareholding pattern XBRL.
encumbered = {}
PROM = "ShareholdingOfPromoterAndPromoterGroup_ContextI"
for r in csv.DictReader(open("data/raw/shareholding/index.csv")):
    x = open("data/raw/shareholding/" + r["file"], encoding="utf-8").read()
    def g(tag):
        m = re.search(r'<[\w-]+:%s\b[^>]*contextRef="%s"[^>]*>([^<]*)<' % (tag, PROM), x)
        return float(m.group(1)) if m and m.group(1).strip() else None
    held = g("NumberOfShares") or g("NumberOfFullyPaidUpEquityShares")
    enc = g("NumberOfSharesEncumbered") or 0.0
    other = g("NumberOfSharesEncumberedUnderOtherEncumbrances") or 0.0
    encumbered[r["symbol"]] = (held, enc, other, r["file"])

# XBRL loans, used to rule out check 8 when total loans are small.
loans = {}
idx = list(csv.DictReader(open("data/raw/xbrl/index.csv")))
for sym in fin:
    b = "C" if fin[sym][2026]["basis"] == "consolidated" else "S"
    f = [i["file"] for i in idx if i["symbol"] == sym and i["fy"] == "2026" and i["basis"] == b][0]
    x = open("data/raw/xbrl/" + f, encoding="utf-8").read()
    tot = 0.0
    for t in ("LoansNoncurrent", "LoansCurrent"):
        m = re.search(r'<[\w-]+:%s\b[^>]*contextRef="OneI"[^>]*>([^<]*)<' % t, x)
        tot += float(m.group(1)) if m else 0.0
    loans[sym] = (tot, f)


def n(d, k):
    v = d.get(k, "")
    return v if isinstance(v, float) else 0.0


def have(d, *keys):
    return all(isinstance(d.get(k), float) for k in keys)


def band(value, mild, strong, higher_is_worse=True):
    if value is None:
        return None
    if higher_is_worse:
        return 2 if value > strong else 1 if value > mild else 0
    return 2 if value < strong else 1 if value < mild else 0


def receivables(d):
    return n(d, "TradeReceivablesCurrent") + n(d, "TradeReceivablesNoncurrent")


def cogs(d):
    return (n(d, "CostOfMaterialsConsumed") + n(d, "PurchasesOfStockInTrade")
            + n(d, "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade"))


def borrowings(d):
    return n(d, "BorrowingsNoncurrent") + n(d, "BorrowingsCurrent")


def mscore(t, p):
    sales_t, sales_p = t["RevenueFromOperations"], p["RevenueFromOperations"]
    dsri = (receivables(t) / sales_t) / (receivables(p) / sales_p) if receivables(p) else 1.0
    gm_t = (sales_t - cogs(t)) / sales_t
    gm_p = (sales_p - cogs(p)) / sales_p
    gmi = gm_p / gm_t if gm_t else 1.0
    def aq(d):
        return 1 - (n(d, "CurrentAssets") + n(d, "PropertyPlantAndEquipment")
                    + n(d, "NoncurrentInvestments") + n(d, "CurrentInvestments")) / d["Assets"]
    aqi = aq(t) / aq(p) if aq(p) else 1.0
    sgi = sales_t / sales_p
    def dep(d):
        dd = n(d, "DepreciationDepletionAndAmortisationExpense")
        return dd / (dd + n(d, "PropertyPlantAndEquipment"))
    depi = dep(p) / dep(t) if dep(t) else 1.0
    def sga(d):
        return (n(d, "EmployeeBenefitExpense") + n(d, "OtherExpenses")) / d["RevenueFromOperations"]
    sgai = sga(t) / sga(p)
    def lev(d):
        return (n(d, "CurrentLiabilities") + n(d, "BorrowingsNoncurrent")) / d["Assets"]
    lvgi = lev(t) / lev(p)
    tata = (t["ProfitLossForPeriod"] - t["CashFlowsFromUsedInOperatingActivities"]) / t["Assets"]
    return (-4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
            + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)


BS = ("Assets", "CurrentAssets", "CurrentLiabilities")
CHECKS = []   # rows for checks.csv
SCORES = []

for sym in sorted(fin):
    F = fin[sym]
    years = sorted(F)
    out = {}

    def put(no, group, name, value, shown, result, source, note=""):
        out[no] = result
        CHECKS.append({"symbol": sym, "check": no, "group": group, "name": name,
                       "value": "" if value is None else round(value, 4), "shown": shown,
                       "result": {None: "not scored", 0: "no flag", 1: "mild", 2: "strong"}[result],
                       "source": source, "note": note})

    # 1 M-score, latest year
    ms = {}
    for y in years:
        need = BS + ("EmployeeBenefitExpense", "OtherExpenses", "TradeReceivablesCurrent", "ProfitLossForPeriod")
        if y - 1 in F and have(F[y], *need) and have(F[y - 1], *need):
            ms[y] = mscore(F[y], F[y - 1])
    v = ms.get(2026)
    r = None if v is None else (2 if v > -1.78 else 1 if v > -2.22 else 0)
    put(1, "earnings", "Beneish M-score (FY2026)", v,
        "" if v is None else f"{v:.2f}", r, "NSE results XBRL",
        "earlier years: " + ", ".join(f"FY{y} {ms[y]:.2f}" for y in sorted(ms) if y != 2026))

    # 2 Cash flow from operations against net profit, all years
    ys = [y for y in years if have(F[y], "ProfitLossForPeriod", "CashFlowsFromUsedInOperatingActivities")]
    pat = sum(F[y]["ProfitLossForPeriod"] for y in ys)
    cfo = sum(F[y]["CashFlowsFromUsedInOperatingActivities"] for y in ys)
    v = cfo / pat if pat > 0 else None
    put(2, "earnings", f"Operating cash flow / net profit, FY{ys[0]}-FY2026", v,
        "" if v is None else f"{v:.2f}", band(v, 0.8, 0.5, False), "NSE results XBRL",
        "" if pat > 0 else "total net profit over the years is not positive")

    # 3 Accruals ratio, average of the last three years
    acc = []
    for y in (2024, 2025, 2026):
        if y in F and y - 1 in F and have(F[y], "Assets") and have(F[y - 1], "Assets"):
            avg_ta = (F[y]["Assets"] + F[y - 1]["Assets"]) / 2
            acc.append((F[y]["ProfitLossForPeriod"] - F[y]["CashFlowsFromUsedInOperatingActivities"]) / avg_ta)
    v = sum(acc) / len(acc) if len(acc) == 3 else None
    put(3, "earnings", "Accruals ratio, average FY2024-FY2026", v,
        "" if v is None else f"{v*100:.1f}%", band(v, 0.05, 0.10), "NSE results XBRL")

    # 4 and 5 Receivable days and inventory days, FY2026 against FY2023
    def days(y, kind):
        d = F.get(y)
        if not d or not have(d, "Assets"):
            return None
        if kind == "rec":
            if not have(d, "TradeReceivablesCurrent"):
                return None
            return receivables(d) / d["RevenueFromOperations"] * 365
        c = cogs(d)
        return n(d, "Inventories") / c * 365 if c > 0 else None
    for no, kind, label in ((4, "rec", "Receivable days"), (5, "inv", "Inventory days")):
        a, b = days(2023, kind), days(2026, kind)
        skip = kind == "inv" and 2026 in F and n(F[2026], "Inventories") < 0.01 * F[2026]["Assets"]
        if skip:
            put(no, "earnings", f"{label}, FY2023 to FY2026", None, "", None, "NSE results XBRL",
                "inventory is under 1% of total assets so the check is skipped")
            continue
        v = (b / a - 1) if a and b is not None else None
        shown = "" if v is None else f"{a:.0f} to {b:.0f} days ({v*100:+.0f}%)"
        put(no, "earnings", f"{label}, FY2023 to FY2026", v, shown, band(v, 0.25, 0.50), "NSE results XBRL",
            "" if a else ("FY2023 figure not usable, see the data notes" if 2023 in F and have(F[2023], "Assets") else "no FY2023 balance sheet in the NSE results files"))

    # 6 Other income as a share of profit before tax, FY2024-FY2026
    oi = sum(F[y]["OtherIncome"] for y in (2024, 2025, 2026) if y in F)
    pbt = sum(F[y]["ProfitBeforeTax"] for y in (2024, 2025, 2026) if y in F)
    ok = all(y in F for y in (2024, 2025, 2026)) and pbt > 0
    v = oi / pbt if ok else None
    put(6, "earnings", "Other income / profit before tax, FY2024-FY2026", v,
        "" if v is None else f"{v*100:.1f}%", band(v, 0.15, 0.30), "NSE results XBRL")

    eq = F[2026]["Equity"]

    # 7 Contingent liabilities against net worth
    c = ar[sym].get("contingent_liabilities")
    v = c[0] / eq if c and c[0] is not None else None
    put(7, "balance sheet", "Contingent liabilities / net worth (31 Mar 2026)", v,
        "" if v is None else f"{v*100:.1f}%", band(v, 0.25, 0.50), f"annual report p{c[1]}" if c else "", c[2] if c else "")

    # 8 Loans to related parties against net worth
    tot, lf = loans[sym]
    rp = ar[sym].get("related_party_loans")
    if tot / eq < 0.10 and not rp:
        put(8, "balance sheet", "Loans to related parties / net worth (31 Mar 2026)", None,
            f"all loans {tot/eq*100:.1f}% of net worth", 0, "NSE results XBRL",
            "total loans on the balance sheet are under 10% of net worth, so the related party part can't reach the mild level")
    else:
        v = rp[0] / eq
        put(8, "balance sheet", "Loans to related parties / net worth (31 Mar 2026)", v,
            f"{v*100:.1f}%", band(v, 0.10, 0.20), f"annual report p{rp[1]}", rp[2])

    # 9 Capital work in progress older than three years
    ct, co = ar[sym]["cwip_total"], ar[sym]["cwip_over_3y"]
    v = co[0] / ct[0] if ct[0] else 0.0
    put(9, "balance sheet", "Capital work in progress older than 3 years (31 Mar 2026)", v,
        f"{v*100:.1f}%", band(v, 0.10, 0.25), f"annual report p{ct[1]}" if ct[1] else "annual report", ct[2])

    # 10 Borrowings growth against revenue growth, FY2023 to FY2026
    if 2023 in F and have(F[2023], "Assets"):
        b0, b1 = borrowings(F[2023]), borrowings(F[2026])
        r0, r1 = F[2023]["RevenueFromOperations"], F[2026]["RevenueFromOperations"]
        rev_g = (r1 / r0) ** (1 / 3) - 1
        if b1 < 0.05 * F[2026]["Assets"]:
            put(10, "balance sheet", "Borrowings growth minus revenue growth, FY2023-FY2026", None,
                f"borrowings {b1/F[2026]['Assets']*100:.1f}% of assets", 0, "NSE results XBRL",
                "borrowings are under 5% of total assets at 31 Mar 2026")
        elif b0 <= 0:
            put(10, "balance sheet", "Borrowings growth minus revenue growth, FY2023-FY2026", None,
                "no borrowings in FY2023", 2, "NSE results XBRL",
                "borrowings went from nil to over 5% of total assets")
        else:
            v = ((b1 / b0) ** (1 / 3) - 1) - rev_g
            put(10, "balance sheet", "Borrowings growth minus revenue growth, FY2023-FY2026", v,
                f"{v*100:+.1f} points a year", band(v, 0.10, 0.20), "NSE results XBRL")
    else:
        put(10, "balance sheet", "Borrowings growth minus revenue growth, FY2023-FY2026", None, "", None,
            "NSE results XBRL", "no FY2023 balance sheet in the NSE results files")

    # 11 Promoter shares pledged or encumbered
    held, enc, other, sf = encumbered[sym]
    if not held:
        put(11, "governance", "Promoter shares pledged or encumbered (31 Mar 2026)", None, "no promoter", None,
            f"shareholding pattern {sf}", "the company has no promoter group")
    else:
        v = enc / held
        note = "" if not enc else (f"of which {other/held*100:.1f}% is shown as other encumbrance rather than pledge" if other else "")
        put(11, "governance", "Promoter shares pledged or encumbered (31 Mar 2026)", v, f"{v*100:.1f}%",
            band(v, 0.10, 0.25), f"shareholding pattern {sf}", note)

    # 12 Change in promoter holding
    h = holding[sym]
    a, b = h.get("31-MAR-2022"), h.get("31-MAR-2026")
    if sym == "REDINGTON":
        put(12, "governance", "Change in promoter holding, Mar 2022 to Mar 2026", None, "no promoter", None,
            "shareholding patterns", "the company has no promoter group")
    elif a is None:
        put(12, "governance", "Change in promoter holding, Mar 2022 to Mar 2026", None, "", None,
            "shareholding patterns", "no shareholding filing on NSE for 31 Mar 2022")
    else:
        v = b - a
        put(12, "governance", "Change in promoter holding, Mar 2022 to Mar 2026", v,
            f"{a:.2f}% to {b:.2f}% ({v:+.2f} points)", 2 if v < -10 else 1 if v < -5 else 0, "shareholding patterns")

    g = gov[sym]
    put(13, "governance", "Statutory auditor resigned before the end of its term, FY2022-FY2026",
        None, g["auditor_resigned_midterm"], 2 if g["auditor_resigned_midterm"] == "yes" else 0,
        "NSE announcements" + (f" ({g['auditor_source']})" if g["auditor_source"] else ""), g["auditor_note"])

    # 14 Audit opinion: qualified etc. from the XBRL declarations, emphasis of matter from the FY2026 report
    decl = [F[y].get("DeclarationOfUnmodifiedOpinionOrStatementOnImpactOfAuditQualification", "") for y in years]
    modified = any(isinstance(d, str) and "impact" in d.lower() for d in decl)
    eom = g["eom_fy2026"] == "yes"
    put(14, "governance", "Audit opinion (qualified FY2023-FY2026, emphasis of matter FY2026)", None,
        "modified opinion" if modified else ("emphasis of matter" if eom else "unmodified"),
        2 if modified else 1 if eom else 0,
        f"annual report p{g['eom_page']}" if eom else "NSE results XBRL", g["eom_note"])

    # 15 Related party trade against revenue
    t = ar[sym].get("related_party_trade")
    v = t[0] / F[2026]["RevenueFromOperations"] if t and t[0] is not None else None
    put(15, "governance", "Related party sales and purchases / revenue (FY2026)", v,
        "" if v is None else f"{v*100:.1f}%", band(v, 0.10, 0.25), f"annual report p{t[1]}" if t else "", t[2] if t else "")

    # 16 CFO and company secretary resignations
    k = int(g["kmp_resignations"])
    put(16, "governance", "CFO and company secretary resignations, FY2022-FY2026", k, str(k),
        2 if k >= 2 else 1 if k == 1 else 0,
        "NSE announcements" + (f" ({g['kmp_source']})" if g["kmp_source"] else ""), g["kmp_note"])

    # Group and overall scores
    groups = {"earnings": range(1, 7), "balance sheet": range(7, 11), "governance": range(11, 17)}
    gs = {}
    for gname, nos in groups.items():
        vals = [out[i] for i in nos if out[i] is not None]
        gs[gname] = 100 * sum(vals) / (2 * len(vals)) if vals else None
    scored = sum(1 for v in out.values() if v is not None)
    overall = sum(v for v in gs.values() if v is not None) / sum(1 for v in gs.values() if v is not None)

    # Altman Z'' score (emerging market version), latest year
    d = F[2026]
    ta = d["Assets"]
    x1 = (d["CurrentAssets"] - d["CurrentLiabilities"]) / ta
    x2 = n(d, "OtherEquity") / ta
    x3 = (d["ProfitBeforeTax"] + d["FinanceCosts"]) / ta
    x4 = d["Equity"] / d["Liabilities"]
    z = 3.25 + 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4

    notes = " ".join(v[1] for k, v in DATA_ISSUES.items() if k[0] == sym and v[1])
    SCORES.append({
        "symbol": sym, "company": universe[sym]["company"], "industry": universe[sym]["industry"],
        "basis": d["basis"], "checks_with_data": scored,
        "earnings_score": round(gs["earnings"], 1), "balance_sheet_score": round(gs["balance sheet"], 1),
        "governance_score": round(gs["governance"], 1),
        "indicator_score": round(overall, 1) if scored >= 12 else "",
        "band": ("incomplete" if scored < 12 else "0-24" if overall < 25 else "25-49" if overall < 50 else "50-74" if overall < 75 else "75-100"),
        "altman_z": round(z, 2),
        "z_range": "above 5.85" if z > 5.85 else "4.35 to 5.85" if z >= 4.35 else "below 4.35",
        "data_notes": notes,
    })

with open("data/clean/checks.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=CHECKS[0].keys()); w.writeheader(); w.writerows(CHECKS)
with open("data/clean/scores.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=SCORES[0].keys()); w.writeheader(); w.writerows(SCORES)
print(len(CHECKS), "check rows,", len(SCORES), "companies")

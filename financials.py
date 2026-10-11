# Reads the results XBRL files companies filed with NSE and pulls the full year
# numbers the checks need into one table, data/clean/financials.csv.
#
# In these files the context FourD holds the twelve months to 31 March, OneI the
# balance sheet on 31 March, and PY_I (newer files only) the balance sheet a year
# earlier. Old files label FourD with the quarter's dates by mistake, so the
# DateOfStartOfReportingPeriod value is used to confirm it's a full year.
import csv
import re
from collections import defaultdict

XBRL_DIR = "data/raw/xbrl"
OUT_FILE = "data/clean/financials.csv"

YEAR_FIELDS = [
    "RevenueFromOperations", "OtherIncome", "CostOfMaterialsConsumed",
    "PurchasesOfStockInTrade",
    "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade",
    "EmployeeBenefitExpense", "FinanceCosts",
    "DepreciationDepletionAndAmortisationExpense", "OtherExpenses", "Expenses",
    "ProfitBeforeTax", "ProfitLossForPeriod",
    "CashFlowsFromUsedInOperatingActivities",
]
BALANCE_FIELDS = [
    "Assets", "CurrentAssets", "PropertyPlantAndEquipment",
    "CapitalWorkInProgress", "TradeReceivablesCurrent",
    "TradeReceivablesNoncurrent", "Inventories", "NoncurrentInvestments",
    "CurrentInvestments", "CashAndCashEquivalents", "BorrowingsNoncurrent",
    "BorrowingsCurrent", "CurrentLiabilities", "Liabilities",
    "EquityShareCapital", "OtherEquity", "Equity",
]
TEXT_FIELDS = ["DeclarationOfUnmodifiedOpinionOrStatementOnImpactOfAuditQualification"]


def facts(path):
    x = open(path, encoding="utf-8").read()
    out = defaultdict(dict)
    for name, ctx, val in re.findall(
            r'<[\w-]+:(\w+)\b[^>]*?contextRef="([^"]+)"[^>]*>([^<]*)<', x):
        out[ctx][name] = val.strip()
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


index = list(csv.DictReader(open(f"{XBRL_DIR}/index.csv")))
by_sym = defaultdict(list)
for r in index:
    by_sym[r["symbol"]].append(r)

rows = []
for sym, files in sorted(by_sym.items()):
    years = {r["fy"] for r in files}
    cons_years = {r["fy"] for r in files if r["basis"] == "C"}
    basis = "C" if cons_years == years else "S"
    data = defaultdict(dict)
    src = defaultdict(dict)
    for r in sorted((r for r in files if r["basis"] == basis), key=lambda r: r["fy"]):
        fy = int(r["fy"])
        f = facts(f"{XBRL_DIR}/{r['file']}")
        four = f.get("FourD", {})
        if four.get("DateOfStartOfReportingPeriod", "").endswith("-04-01"):
            for k in YEAR_FIELDS:
                if num(four.get(k)) is not None:
                    data[fy][k] = num(four[k])
                    src[fy][k] = r["file"]
        for k in TEXT_FIELDS:
            v = f.get("OneD", {}).get(k) or four.get(k)
            if v:
                data[fy][k] = v
                src[fy][k] = r["file"]
        # The year's own file wins for its balance sheet; the next year's
        # comparative only fills gaps.
        for ctx, year in (("OneI", fy), ("PY_I", fy - 1)):
            for k in BALANCE_FIELDS:
                v = num(f.get(ctx, {}).get(k))
                if v is not None and (k not in data[year] or ctx == "OneI"):
                    data[year][k] = v
                    src[year][k] = r["file"]
    for fy in sorted(data):
        if not 2022 <= fy <= 2026:
            continue
        row = {"symbol": sym, "fy": fy, "basis": "consolidated" if basis == "C" else "standalone"}
        for k in YEAR_FIELDS + BALANCE_FIELDS + TEXT_FIELDS:
            row[k] = data[fy].get(k, "")
        row["source_files"] = " ".join(sorted(set(src[fy].values())))
        rows.append(row)

with open(OUT_FILE, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} company years written")

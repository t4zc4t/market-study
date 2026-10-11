# Runs the same checks as checks.py on Gensol Engineering as of its FY2024
# annual report, the last full year of accounts before SEBI's interim order of
# 15 April 2025. Figures are typed in from the report (gensol_inputs.csv) because
# NSE only holds Gensol's results from FY2024. Gensol moved to NSE's main board
# in 2023, so there is one comparison year (FY2023) instead of three.
import csv

d = {r["item"]: r for r in csv.DictReader(open("validation/gensol_inputs.csv"))}
def v(item, col="fy2024"):
    x = d[item][col]
    return float(x) if x not in ("", None) else None

def mscore():
    def rec(c): return v("trade_receivables", c)
    def rev(c): return v("revenue", c)
    def cogs(c): return v("cost_of_materials", c) + v("purchases_stock_in_trade", c) + v("change_in_inventories", c)
    def aq(c): return 1 - (v("current_assets", c) + v("ppe", c) + v("investments", c)) / v("total_assets", c)
    def dep(c): return v("depreciation", c) / (v("depreciation", c) + v("ppe", c))
    def sga(c): return (v("employee_cost", c) + v("other_expenses", c)) / rev(c)
    def lev(c): return (v("current_liabilities", c) + v("borrowings_noncurrent", c)) / v("total_assets", c)
    t, p = "fy2024", "fy2023"
    dsri = (rec(t) / rev(t)) / (rec(p) / rev(p))
    gmi = ((rev(p) - cogs(p)) / rev(p)) / ((rev(t) - cogs(t)) / rev(t))
    aqi = aq(t) / aq(p)
    sgi = rev(t) / rev(p)
    depi = dep(p) / dep(t)
    sgai = sga(t) / sga(p)
    lvgi = lev(t) / lev(p)
    tata = (v("net_profit") - v("operating_cash_flow")) / v("total_assets")
    m = (-4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
         + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
    return m, dict(DSRI=dsri, GMI=gmi, AQI=aqi, SGI=sgi, DEPI=depi, SGAI=sgai, LVGI=lvgi, TATA=tata)

def band(x, mild, strong, higher=True):
    if x is None: return "not scored"
    if higher: return "strong" if x > strong else "mild" if x > mild else "no flag"
    return "strong" if x < strong else "mild" if x < mild else "no flag"

rows = []
m, parts = mscore()
rows.append((1, "earnings", "Beneish M-score (FY2024)", f"{m:.2f}", "strong" if m > -1.78 else "mild" if m > -2.22 else "no flag"))
cfo = v("operating_cash_flow") + v("operating_cash_flow", "fy2023")
pat = v("net_profit") + v("net_profit", "fy2023")
rows.append((2, "earnings", "Operating cash flow / net profit, FY2023-FY2024", f"{cfo/pat:.2f}", band(cfo / pat, 0.8, 0.5, False)))
acc24 = (v("net_profit") - v("operating_cash_flow")) / ((v("total_assets") + v("total_assets", "fy2023")) / 2)
acc23 = (v("net_profit", "fy2023") - v("operating_cash_flow", "fy2023")) / ((v("total_assets", "fy2023") + v("total_assets", "fy2022_open")) / 2)
acc = (acc24 + acc23) / 2
rows.append((3, "earnings", "Accruals ratio, average FY2023-FY2024", f"{acc*100:.1f}% (FY2024 alone {acc24*100:.1f}%)", band(acc, 0.05, 0.10)))
rd23 = v("trade_receivables", "fy2023") / v("revenue", "fy2023") * 365
rd24 = v("trade_receivables") / v("revenue") * 365
rows.append((4, "earnings", "Receivable days, FY2023 to FY2024", f"{rd23:.0f} to {rd24:.0f} days ({(rd24/rd23-1)*100:+.0f}%)", band(rd24 / rd23 - 1, 0.25, 0.50)))
inv_share = v("inventories") / v("total_assets")
rows.append((5, "earnings", "Inventory days", f"inventory {inv_share*100:.1f}% of assets", "not scored"))
oi = v("other_income") + v("other_income", "fy2023")
pbt = v("profit_before_tax") + v("profit_before_tax", "fy2023")
rows.append((6, "earnings", "Other income / profit before tax, FY2023-FY2024", f"{oi/pbt*100:.1f}%", band(oi / pbt, 0.15, 0.30)))
eq = v("total_equity")
rows.append((7, "balance sheet", "Contingent liabilities / net worth (31 Mar 2024)", f"{v('contingent_liabilities')/eq*100:.1f}%", band(v("contingent_liabilities") / eq, 0.25, 0.50)))
rows.append((8, "balance sheet", "Loans to related parties / net worth (31 Mar 2024)", f"{v('related_party_loans')/eq*100:.1f}%", band(v("related_party_loans") / eq, 0.10, 0.20)))
rows.append((9, "balance sheet", "Capital work in progress older than 3 years", f"{v('cwip_over_3y')/v('cwip_total')*100:.1f}%", band(v("cwip_over_3y") / v("cwip_total"), 0.10, 0.25)))
b0 = v("borrowings_noncurrent", "fy2023") + v("borrowings_current", "fy2023")
b1 = v("borrowings_noncurrent") + v("borrowings_current")
diff = (b1 / b0 - 1) - (v("revenue") / v("revenue", "fy2023") - 1)
rows.append((10, "balance sheet", "Borrowings growth minus revenue growth, FY2023-FY2024", f"{diff*100:+.1f} points", band(diff, 0.10, 0.20)))
pl = v("promoter_pledged_pct") / 100
rows.append((11, "governance", "Promoter shares pledged or encumbered (31 Mar 2024)", f"{pl*100:.1f}%", band(pl, 0.10, 0.25)))
rows.append((12, "governance", "Change in promoter holding", "no NSE filing before 2023", "not scored"))
rows.append((13, "governance", "Statutory auditor resigned before the end of its term", "no", "no flag"))
rows.append((14, "governance", "Audit opinion (FY2024)", "unmodified, no emphasis of matter", "no flag"))
rt = v("related_party_trade") / v("revenue")
rows.append((15, "governance", "Related party sales and purchases / revenue (FY2024)", f"{rt*100:.1f}%", band(rt, 0.10, 0.25)))
rows.append((16, "governance", "CFO and company secretary resignations up to 31 Mar 2024", "0", "no flag"))

pts = {"no flag": 0, "mild": 1, "strong": 2}
groups = {}
for no, g, *_ , r in rows:
    if r != "not scored":
        groups.setdefault(g, []).append(pts[r])
gs = {g: 100 * sum(x) / (2 * len(x)) for g, x in groups.items()}
overall = sum(gs.values()) / len(gs)
scored = sum(1 for r in rows if r[-1] != "not scored")

with open("validation/gensol_checks.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["check", "group", "name", "shown", "result"])
    w.writerows(rows)
for r in rows: print(r)
print("M-score parts:", {k: round(x, 2) for k, x in parts.items()})
print("group scores:", {k: round(x, 1) for k, x in gs.items()}, "overall", round(overall, 1), "checks with data", scored)

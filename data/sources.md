# Data sources

| File | Source | Downloaded |
|---|---|---|
| raw/ind_niftysmallcap100list.csv | Nifty Smallcap 100 constituents, https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap100list.csv | 7 Oct 2026 |
| raw/nse_equity_list.csv | NSE list of listed equities with listing dates, https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv | 7 Oct 2026 |
| raw/nse_filing_lists.json | NSE lists of each sample company's annual results, integrated filings, shareholding patterns, pledge disclosures, annual reports and announcements since April 2021, from nseindia.com | 8 Oct 2026 |
| raw/xbrl/ | The results XBRL files those lists point to, from nsearchives.nseindia.com/corporate/xbrl, one per company, year and basis (index.csv lists them) | 8 Oct 2026 |
| raw/annual_reports/ | FY2026 annual reports of the 24 sample companies, from nsearchives.nseindia.com/annual_reports, kept under their NSE file names. Not in the repo because of size (286 MB), the links are in nse_filing_lists.json. For Gallantt Ispat NSE has two FY2026 reports, I use the later one filed on 20 Sep 2026 | 8 Oct 2026 |
| raw/shareholding/ | Shareholding pattern XBRL for 31 March 2026 of the 24 sample companies, from nsearchives.nseindia.com/corporate/xbrl (index.csv lists them) | 8 Oct 2026 |
| raw/announcements/ (not in the repo, about 38 MB) | 25 announcement PDFs about auditor appointments, auditor resignations and management changes, from nsearchives.nseindia.com/corporate | 8 Oct 2026 |
| raw/validation/gensol/ | Gensol Engineering FY2023 and FY2024 annual reports (not in the repo because of size), FY2024 results XBRL and 31 March 2024 shareholding pattern from nsearchives.nseindia.com, its NSE filing lists, and SEBI confirmatory order WTM/KV/CFID/CFID-SEC2/31565/2025-26 (July 2025) from sebi.gov.in | 11 Oct 2026 |

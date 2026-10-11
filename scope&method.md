# Scope and method

This is an educational project. It runs a fixed set of accounting and governance checks over public filings of listed Indian companies and shows the results as plain indicator scores. It is not investment advice, I am not registered with SEBI as a research analyst, and nothing here says any company or person has done anything wrong. A high score only means some numbers sit outside the range the checks treat as typical, and there are often normal business reasons for that.

I wrote this file before collecting any data, so the checks and thresholds below are fixed in advance and not adjusted after seeing which companies score high. The wording of checks 7, 8 and 15 was made more exact while reading the annual reports, before any scores were worked out.

## Which companies

I use the Nifty Smallcap 100, taking the constituent list NSE publishes on the day I download it and keeping that list fixed for the whole project. The download date goes into the data folder with the list.

Every company NSE puts under Financial Services is dropped, which covers banks, NBFCs, housing finance companies, brokers, wealth managers and market infrastructure firms. Checks like the M-score and cash flow against profit don't mean much for a lender's balance sheet, and using NSE's own grouping means I'm not picking which ones count. Companies listed after 31 March 2024 are dropped too, because they haven't filed three years of annual results as a listed company and most checks need a trend. The listing date comes from NSE's equity list, and where a company was listed on BSE long before NSE I use the earlier date.

From the list downloaded on 7 October 2026 this drops 21 financial companies and 15 recent listings, leaving 64.

To keep the work manageable I run the checks on a sample of 24 of those 64. The sample is drawn at random within each industry, in proportion to how many of the 64 sit in that industry, so I don't pick any company by hand. The random seed is fixed in universe.py, so anyone running it gets the same 24. The full list, with the reason for each dropped company and which ones are in the sample, is in data/clean/universe.csv.

## Years and numbers

The study covers FY2022 to FY2026. The results files companies filed for FY2022 don't include a balance sheet, only profit and loss and cash flow, so the checks that need balance sheet numbers run from FY2023 to FY2026 and the rest use all five years. I use consolidated figures, not standalone, because a lot of what these checks look for, like loans to related parties or debt, can sit in subsidiaries. If a company has no subsidiaries I use standalone and mark it.

## Data sources

I only use official filings.

1. The annual financial results companies file with NSE and BSE under SEBI's listing rules, for the profit and loss, balance sheet and cash flow numbers.
2. Quarterly shareholding pattern filings on NSE and BSE, for promoter holding and promoter shares pledged.
3. Annual reports from the exchange or company website, for the auditor's report, related party transactions, contingent liabilities, the ageing of capital work in progress and other notes.
4. Corporate announcements on NSE and BSE, where auditor changes and resignations of key managerial people have to be disclosed.
5. Published SEBI orders and court documents, only for the validation part.

Every number on the website links back to the filing it came from. The annual report items are read by hand, so that part is slower and I note the page number for each one.

## The checks

Each check gives one of three results, no flag, mild or strong. The thresholds are starting points I picked from the accounting literature and common analyst practice, they are written out here so anyone can redo the work or argue with them.

### Earnings quality

1. Beneish M-score, the eight variable version from Beneish (1999), worked out for each year from FY2024 since it needs the previous year's balance sheet. Strong if above -1.78 in the latest year, mild if between -2.22 and -1.78.
2. Cash flow from operations against net profit, added up over the five years. Strong if the ratio is below 0.5, mild if between 0.5 and 0.8. Companies with a loss over the five years in total are marked separately instead of scored.
3. Accruals ratio, which is net profit minus operating cash flow, divided by average total assets, averaged over the last three years. Strong above 10 percent, mild between 5 and 10 percent.
4. Receivable days in FY2026 against FY2023. Strong if up more than 50 percent, mild if up 25 to 50 percent.
5. Inventory days in FY2026 against FY2023, same thresholds as receivable days. Service companies with almost no inventory skip this check.
6. Other income as a share of profit before tax, averaged over three years. Strong above 30 percent, mild between 15 and 30 percent.

### Balance sheet

7. Contingent liabilities not provided for, against net worth, in the latest year. Strong above 50 percent, mild between 25 and 50 percent. I count claims and tax demands the company disputes and guarantees it gave for other entities' borrowings. I leave out bank guarantees, letters of credit, performance bonds and customs bonds a company takes out for its own business, because some companies list these and some don't, and for contractors and shipbuilders they are just part of normal work.
8. Loans to related parties against net worth. Strong above 20 percent, mild between 10 and 20 percent. If a company's total loans on the balance sheet are under 10 percent of net worth, the related party part can't reach the mild level, so the check is marked no flag without reading the report. For the rest I take the related party loans from the annual report.
9. Capital work in progress that has been pending for more than three years, as a share of total capital work in progress, from the ageing table companies have had to disclose since FY2022. Strong above 25 percent, mild between 10 and 25 percent.
10. Growth of total borrowings against growth of revenue, as yearly growth rates from FY2023 to FY2026. Strong if borrowings grew more than 20 percentage points a year faster, mild if 10 to 20 points faster.

### Governance

11. Share of promoter holding pledged or otherwise encumbered, from the shareholding pattern for 31 March 2026. Strong above 25 percent, mild between 10 and 25 percent. I use the shareholding pattern rather than NSE's separate pledge feed because the feed has no date on it and for at least one company it didn't match the shareholding pattern. Encumbrance other than a pledge is counted too, and the company page shows the split.
12. Change in promoter holding from FY2022 to FY2026. Strong if it fell more than 10 percentage points, mild if it fell 5 to 10 points.
13. Auditor changes. Strong if an auditor resigned before finishing its term, no flag for a normal rotation at the end of a term.
14. The auditor's opinion. Strong if any year from FY2023 has a qualified, adverse or disclaimer opinion, taken from the declaration filed with the results. Mild if the FY2026 auditor's report has an emphasis of matter paragraph, since FY2026 is the only annual report I read.
15. Related party transactions as a share of revenue in the latest year. Strong above 25 percent, mild between 10 and 25 percent. I count sales and purchases of goods and services with related parties outside the group, as listed in the related party note. Pay to KMPs, dividends, interest, loans, investments, rent, reimbursements, CSR and purchases of assets are left out. A company that sells most of its output to its parent will show a high number here for plain business reasons, and its page says so.
16. Resignations of the CFO or company secretary from April 2021 to March 2026. Strong for two or more, mild for one. Retirements and exits without a stated resignation are not counted, and nor are exits at subsidiaries. I find these from NSE announcements, so an exit that was only mentioned inside a board meeting outcome may be missed.

### Altman Z score, kept separate

I also work out the Altman Z score, using the Z'' version made for non manufacturers and emerging markets. It measures financial stress, not accounting quality, so it is shown next to the indicator score and not added into it.

## Details and edge cases

These are the exact formulas and the rules for odd cases, so the scores can be rebuilt from the data files with checks.py.

The M-score uses the standard eight ratios. Selling, general and admin cost is taken as employee cost plus other expenses, cost of goods is materials plus purchases plus the change in inventories, and leverage is current liabilities plus long term borrowings over total assets.

Receivable days use revenue. Inventory days use cost of goods, and the check is skipped when inventory is under 1 percent of total assets.

For check 10, if borrowings at 31 March 2026 are under 5 percent of total assets the check is no flag, and if a company had no borrowings in FY2023 but now has more than 5 percent of assets, it is strong.

Check 12 needs a shareholding filing for 31 March 2022, so companies listed after that date aren't scored on it.

The Altman Z score uses the version for emerging markets: 3.25 plus 6.56 times working capital, 3.26 times other equity (standing in for retained earnings), 6.72 times profit before interest and tax and 1.05 times book equity over total liabilities, with working capital, other equity and operating profit all divided by total assets. Results are shown in three ranges, above 5.85, 4.35 to 5.85 and below 4.35.

## Data problems found

Where a company's own XBRL filing doesn't hold together, those figures are left out and the company page says so. So far that is Syrma SGS for FY2023, where the full year costs in the results XBRL are smaller than the fourth quarter alone, and Kirloskar Oil Engines for FY2023 and FY2024, where the lending subsidiary's loans are tagged as trade receivables.

## Scoring

No flag counts 0, mild counts 1 and strong counts 2. Each of the three groups gets a score out of 100, which is its points divided by the most it could get, and the overall indicator score is the plain average of the three groups. I kept the weights equal so the result doesn't depend on me deciding which group matters more.

If a check can't be worked out for a company because the data isn't there, it is left out of that company's maximum, not counted as zero. Each company page shows how many of the sixteen checks had data, and companies with fewer than twelve get the label incomplete instead of a score band.

The score bands are just 0 to 24, 25 to 49, 50 to 74 and 75 to 100, without names.

## Validation

Before publishing the live scores I ran the same checks on Gensol Engineering, using its FY2024 annual report, which was the last full year of accounts before SEBI's interim order of 15 April 2025. SEBI's confirmatory order of July 2025 (WTM/KV/CFID/CFID-SEC2/31565/2025-26) records prima facie findings of falsified lender letters given to rating agencies and diversion of company funds by the promoters and related entities, and says a detailed investigation and forensic audit were still going on. These are prima facie findings, not final ones, and the validation page says that.

Gensol moved to NSE's main board in 2023, so the run has one comparison year, FY2023, instead of the longer window the main screen uses. The formulas and thresholds are the same. Its figures are typed in from the FY2024 annual report with page numbers in validation/gensol_inputs.csv, and validation/gensol.py works out the checks.

More validation cases can be added later, only for listed non financial companies where SEBI or a court has published findings, and only after reading those orders.

## What gets published

The repo is public. The README has the findings at the level of patterns, like how scores are spread across sectors, which checks show up most often and how the validation cases came out. It does not list or rank the highest scoring companies.

The website is a lookup tool hosted on Cloudflare Pages. You can search and filter by sector, score band and check, and each company has a page with every check, its value, the threshold and a link to the source filing. There's also a methodology page, the validation page and a full disclaimer page. There is no leaderboard or list of highest scores, and every page footer carries a short disclaimer and the date of the data.

## Words used

On the site and in the repo I use words like indicator, score, ratio, check, threshold and outside the typical range. I don't use words that suggest wrongdoing or tell anyone to buy, sell or avoid a stock, and the site calls the results indicator scores, not red flags.

## Corrections

If any figure is wrong, anyone can open a GitHub issue. I check it against the filing, fix it and log the change in a corrections file with the date.

## Updates

This is a snapshot, not a live feed. I refresh the data by hand when new annual filings are out, and the data date changes with it.

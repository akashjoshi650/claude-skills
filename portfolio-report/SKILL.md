---
name: portfolio-report
description: Monthly report on an Indian stock and mutual fund portfolio, emailed to the user's Gmail. Asks for or updates holdings, monthly SIP, one-time lump sum and stocks; fetches latest NSE/BSE prices and AMFI NAVs plus news on each holding; analyses gains, allocation and concentration; projects the corpus under three return scenarios; and estimates how many years until retirement for several monthly withdrawal amounts. Built to run on the 3rd of every month as a scheduled task. Use when someone wants a portfolio review, a monthly investment report, SIP or retirement projections, or "when can I retire" numbers for Indian investments.
---

# Monthly Portfolio Report (India)

Turns a stocks + mutual funds portfolio into an email report: what it's worth today, what moved, news that
matters, where it could be in 5-30 years, and when the user could retire at different monthly withdrawals.

`SKILL` = the folder this file is in. Scripts are in `SKILL/scripts/` and need only Python 3.9+ (standard library); the PDF step also needs a Chromium-based browser.

If `SKILL/scripts/` is missing (the skill was saved without its files), get them from
https://github.com/akashjoshi650/claude-skills/tree/main/portfolio-report, or do the same steps by hand: prices by
web search, and the projections with the formulas in step 4 in a short Python snippet.

| step | who | output |
|---|---|---|
| 1. load or ask for the portfolio | you (Claude) | `portfolio.json` |
| 2. latest prices and NAVs | `fetch_prices.py` (AMFI + Yahoo), web search for gaps | `prices.json` |
| 3. news on each holding | you, with web search | `news.json` |
| 4. numbers, projections, retirement | `report.py` | `report.html`, `summary.json` |
| 5. commentary | you, from `summary.json` + news | `commentary.md`, re-run step 4 |
| 6. this month's money plan | you, from the mix and the user's budget | `plan.json` |
| 7. designed PDF (and a redacted one for sharing) | `make_pdf.py` | `report.pdf`, `report-redacted.pdf` |
| 8. email it | Gmail connector | email in the user's inbox |

## Ground rules
- **Not financial advice.** The report carries a disclaimer; keep it. In commentary, describe and explain (what
  moved, what is concentrated, what the news says); don't tell the user to buy or sell a specific security.
- **The portfolio is private.** Keep `portfolio.json` and `history.json` in a private folder of the user's choosing
  (default: `~/portfolio-report/`), never in a public repo, and never paste holdings into web searches beyond the
  stock or fund name.
- Send email **only to the address the user gave** (`email` in `portfolio.json`).

## 1. The portfolio
If `portfolio.json` exists, read it. Otherwise build it with the user, starting from `SKILL/example/portfolio.json`.
Ask, in one message:
1. Mutual funds: fund name (Direct/Regular, Growth/IDCW), units held, amount invested, monthly SIP into it.
   Units and invested amounts are on the CAS statement (CAMS/KFintech) or the app they invest through.
2. Stocks: NSE/BSE symbol, quantity, average buy price (from the broker's holdings page).
3. Total monthly SIP, and whether it steps up each year (e.g. 10%).
4. Any one-time money to invest this month (lump sum).
5. Other assets to include, if they want (EPF, PPF, FDs, gold): name and current value.
6. Age, the email to send the report to, and the monthly withdrawals they want retirement numbers for
   (default: ₹50k, ₹1L, ₹1.5L, ₹2L a month, in today's rupees).

Every month (when run by hand) ask only what changes: **"Same SIP? Any one-time amount this month? Any stocks
or funds bought or sold?"** Update `portfolio.json`, and set `lump_sum_this_month` back to 0 after the report.
On a scheduled run nobody is there to answer: use the file as is, and the email footer reminds the user to
send changes before the 3rd.

Fund matching: give each fund its `amfi_code` (scheme code) when you can; the fetcher also tries ISIN and the
exact AMFI scheme name. If a fund shows up as missing, search AMFI/mfapi for its code and add it.

## 2. Prices
```
python SKILL/scripts/fetch_prices.py <dir>/portfolio.json <dir>/prices.json
```
NAVs come from AMFI's official daily file (`portal.amfiindia.com/spages/NAVAll.txt`); stock prices from Yahoo
Finance's free chart endpoint (`SYMBOL.NS`, or `.BO` for `"exchange": "BSE"`). That endpoint is unofficial and
can break or rate-limit. For anything listed under `missing`, look up the latest price with web search (NSE/BSE
page, Moneycontrol, Value Research) and add it to `prices.json` by hand with `"source": "web search"`.
If a price still can't be found, the holding is left out and the report says so.

## 3. News
For each stock and each fund's AMC/category, run one web search for news from the last month
("<company> news" / "<fund name> news"). Keep 1-2 items per holding that actually matter (results, guidance,
regulatory action, management change, big order wins, fund manager change, SEBI action), skip noise and
price-target chatter. Write `news.json`:
```json
[{"holding": "TCS", "headline": "...", "source": "Economic Times", "date": "2026-12-01", "url": "https://...",
  "note": "one line: why it matters for this holding"}]
```
Only include links you actually opened or that search returned; never invent a URL.

## 4. Numbers
```
python SKILL/scripts/report.py <dir>/portfolio.json <dir>/prices.json --out <dir>/out/<YYYY-MM> --news <dir>/news.json --no-history-update
```
It prints the totals and base-case retirement years. What it computes:
- value, invested, gain per holding; weight; allocation buckets; 1-month change for stocks; change since the
  last report (from `history.json`);
- flags: one stock over 10%, one fund over 35%, a holding down 20%+ from cost, more than 7 funds, stocks over
  40% of the portfolio, under 10% debt at 40+;
- projections at 1-30 years under conservative / base / optimistic returns (default 8 / 11 / 13%), in rupees then
  and in today's rupees;
- for each monthly withdrawal: the first year the corpus can pay it, rising with inflation (default 6%), for
  `years_in_retirement` (default 35) while earning `post_retirement_return_pct` (default 7.5%).
All assumptions live in `portfolio.json` → `assumptions`; tell the user they can change them.

## 5. Commentary
Read `out/<YYYY-MM>/summary.json` and the news, then write `commentary.md`: 4-8 short lines in plain English,
`- ` for bullets. Cover the month's change and what drove it, anything in the flags worth acting on (as a thing
to look at, not an instruction), the news that matters, and one line on the retirement picture
(e.g. "At ₹1L a month you're about 26 years away in the base case; raising the SIP by ₹5k would bring that
closer" only if you checked it by re-running with the new SIP). Then run step 4 again with
`--commentary <dir>/commentary.md` and **without** `--no-history-update`, so this month is saved to history.

Open `report.html` (or screenshot it) and check it before sending: no missing holdings you didn't expect,
totals that look right against last month.

## 6. This month's money plan
The user tells you this month's new money (one-time amount, stock budget). Write `plan.json` saying where it could go:
```json
{"summary": "one paragraph: the imbalance and the idea",
 "items": [{"holding": "NIFTYBEES (Nifty 50 ETF)", "kind": "ETF, from the stock budget", "bucket": "Large",
            "amount": 4080, "units": 14, "price": 291.40, "why": "one or two sentences"}],
 "target_mix": {"Large": 50, "Mid": 30, "Small": 20},
 "target_note": "where the target comes from; say it's a rule of thumb the user can change",
 "hold_off": [{"holding": "...", "why": "..."}]}
```
Buckets: Large, Flexi/Multi, Mid, Small, Debt, Gold/Silver, Other. How to decide:
- Rebalance with new money toward the target mix; never suggest selling just to rebalance (tax, exit loads).
- Prefer what the user already holds, then broad low-cost index funds/ETFs. Don't pick individual stocks for them;
  if they want stocks, explain the trade-off and let them choose.
- Use whole units for ETFs/stocks at the latest price and keep the total within the budget.
- Before any of this: if they have no emergency fund (about 6 months of expenses), say that comes first.
- It's a rules-based idea, not advice. The PDF says so; keep that line.

## 7. Designed PDF
```
python SKILL/scripts/make_pdf.py <dir>/out/<YYYY-MM> --plan <dir>/plan.json --news <dir>/news.json --commentary <dir>/commentary.md --name "<first name>"
python SKILL/scripts/make_pdf.py <dir>/out/<YYYY-MM> --plan <dir>/plan.json --news <dir>/news.json --commentary <dir>/commentary.md --redact
```
Four A4 pages: cover with headline numbers, commentary and a mix donut; holdings bars and news; the money plan
with before/after/target mix bars; projection chart and retirement table. `--redact` hides every rupee amount
except the withdrawal options, for posting on LinkedIn etc. Uses Playwright if present, else headless
Chrome/Edge; otherwise open the `-print.html` and Print to PDF. Look at the pages before sending.

## 8. Email
Use the Gmail connector. Attach `report.pdf` (base64) and use `report.html` as the body. Subject: `Portfolio report, <Month YYYY>: <value> (<change since last>)`. Body: the
contents of `report.html` as the HTML body (it uses inline styles only, so Gmail keeps the layout).
- If the connector has a send tool, send it to the `email` in `portfolio.json`.
- If it can only create drafts (some Gmail connectors can't send), create the draft and tell the user it's
  waiting in Drafts. *(Which Gmail tools exist depends on the connector the user has; check its tool list.)*
- No Gmail connector at all: tell the user, attach/link `report.html`, and suggest connecting Gmail.

Then set `lump_sum_this_month` to 0 in `portfolio.json`.

## Running it on the 3rd of every month
See `SKILL/references/scheduling.md`. Never create a schedule without the user's OK.

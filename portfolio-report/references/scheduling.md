# Running the report on the 3rd of every month

The skill runs fine unattended: a scheduled run uses `portfolio.json` as it is, fetches prices and news,
writes the report, and emails it. Nothing is asked, so changes (new SIP amount, a lump sum, stocks bought or
sold) have to be in `portfolio.json` before the 3rd.

**Ask the user before creating any schedule**, and confirm the time and the email address with them.

## What a scheduled run needs
1. **The skill** installed where the run happens (see the repo README).
2. **The portfolio file** somewhere the run can read and write: a *private* GitHub repo (e.g.
   `<user>/portfolio-private` holding `portfolio.json` and `history.json`), or a folder on the user's computer if
   the schedule runs there. Never this public skills repo. The run should commit the updated `history.json` back,
   so next month's "change since last report" works.
3. **The Gmail connector** enabled for the scheduled run, plus web search for news.
4. **Network access** to `portal.amfiindia.com` and `query1.finance.yahoo.com` (cloud environments with a
   restricted network policy may block them; then the run falls back to web search for prices, which is slower
   and less exact).

## Time
3rd of every month, 9:00 AM IST = **03:30 UTC** → cron `30 3 3 * *` (UTC) or `0 9 3 * *` (Asia/Kolkata).
9 AM IST uses the previous trading day's closing prices and the previous evening's NAVs, which is what a
monthly report should show. If the 3rd is a market holiday that's still fine.

## Ways to set it up
*(These depend on the Claude product the user has; the names below may have changed, so check the current docs.)*
- **Claude Code on the web / Claude app**: ask Claude to create a scheduled task (a "routine" / trigger) with the
  cron above, pointing at the private portfolio repo, with the Gmail connector attached. Prompt to schedule:
  > Run the portfolio-report skill on portfolio.json in this repo. Fetch prices and news, write the report and
  > commentary, email it to the address in portfolio.json via Gmail, then commit the updated history.json and
  > reset lump_sum_this_month to 0.
- **Claude Code on the user's own computer**: a cron job / Windows Task Scheduler entry that runs
  `claude -p "<the prompt above>"` in the portfolio folder at 09:00 on the 3rd. The computer must be on.

## A reminder before the run (optional)
A second schedule on the 1st that emails "Your portfolio report runs on the 3rd. Any SIP change, lump sum or
trades this month? Reply in your Claude project" helps keep `portfolio.json` current.

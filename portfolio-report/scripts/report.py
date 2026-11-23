"""Build the monthly portfolio report: holdings analysis, projections, and years to retirement.

    python report.py portfolio.json prices.json --out <dir> [--news news.json] [--commentary commentary.md]
                     [--history history.json] [--no-history-update]

Writes <dir>/report.html (email-safe HTML, inline styles) and <dir>/summary.json (all the numbers, for Claude
to read and write commentary from). Standard library only.

The math (all monthly compounding, figures in rupees):
- Projection: today's value + the one-time lump sum grow at the scenario return; the monthly SIP is added every
  month and steps up once a year by sip_step_up_pct.
- Retirement: for each monthly withdrawal W (in today's rupees) we find the first month t where the projected
  corpus can pay W, grown by inflation to month t and then every month after, for years_in_retirement years while
  the rest of the corpus earns post_retirement_return_pct. That corpus is the present value of a growing annuity.
"""
import argparse
import html
import json
import os
from datetime import date, datetime

DEFAULTS = {
    'inflation_pct': 6.0,
    'returns_pct': {'conservative': 8.0, 'base': 11.0, 'optimistic': 13.0},
    'post_retirement_return_pct': 7.5,
    'years_in_retirement': 35,
    'sip_step_up_pct': 0.0,
    'max_years': 50,
}
PROJECTION_YEARS = [1, 3, 5, 10, 15, 20, 25, 30]
DISCLAIMER = ('This report is generated automatically for personal tracking. It is not financial, investment, '
              'or tax advice. Prices may be delayed or wrong, projections assume steady returns that real markets '
              'never give, and past returns do not predict future ones. Check figures with your broker/RTA '
              'statements and talk to a SEBI-registered investment adviser before acting on anything here.')


# ---------- money formatting ----------

def inr(x, decimals=0):
    """Indian digit grouping: 12,34,56,789."""
    if x is None:
        return '-'
    neg = x < 0
    x = abs(x)
    s = f'{x:.{decimals}f}'
    whole, _, frac = s.partition('.')
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ','.join(groups + [tail])
    return ('-' if neg else '') + '₹' + whole + ('.' + frac if frac else '')


def short_inr(x):
    """₹1.25 Cr / ₹45.3 L / ₹12,000."""
    if x is None:
        return '-'
    a = abs(x)
    if a >= 1e7:
        return f'{"-" if x < 0 else ""}₹{a / 1e7:.2f} Cr'
    if a >= 1e5:
        return f'{"-" if x < 0 else ""}₹{a / 1e5:.1f} L'
    return inr(x)


def pct(x, decimals=1, sign=True):
    if x is None:
        return '-'
    return f'{x:+.{decimals}f}%' if sign else f'{x:.{decimals}f}%'


# ---------- math ----------

def monthly_rate(annual_pct):
    return (1 + annual_pct / 100) ** (1 / 12) - 1


def project(start, sip, annual_pct, months, step_up_pct=0.0):
    """Corpus path, one value per month end (index 0 = today)."""
    r = monthly_rate(annual_pct)
    path = [start]
    c, s = start, sip
    for m in range(1, months + 1):
        c = c * (1 + r) + s
        path.append(c)
        if m % 12 == 0:
            s *= 1 + step_up_pct / 100
    return path


def annuity_factor(inflation_pct, post_return_pct, years):
    """Corpus needed per ₹1 of first monthly withdrawal, withdrawals growing with inflation, paid at month start."""
    g, r = monthly_rate(inflation_pct), monthly_rate(post_return_pct)
    q = (1 + g) / (1 + r)
    n = years * 12
    if abs(q - 1) < 1e-12:
        return float(n)
    return (1 - q ** n) / (1 - q)


def retirement_table(path, withdrawals, a, age=None):
    f = annuity_factor(a['inflation_pct'], a['post_retirement_return_pct'], a['years_in_retirement'])
    infl_m = monthly_rate(a['inflation_pct'])
    rows = []
    for w in withdrawals:
        hit = None
        for t, corpus in enumerate(path):
            need = w * (1 + infl_m) ** t * f
            if corpus >= need:
                hit = (t, corpus, need)
                break
        if hit is None:
            rows.append({'withdrawal': w, 'months': None})
            continue
        t, corpus, need = hit
        rows.append({
            'withdrawal': w,
            'months': t,
            'years': round(t / 12, 1),
            'age': round(age + t / 12, 1) if age else None,
            'corpus_needed': need,
            'corpus_needed_today_rupees': need / (1 + infl_m) ** t,
            'withdrawal_then': w * (1 + infl_m) ** t,
        })
    return rows


# ---------- portfolio ----------

def value_holdings(pf, prices):
    rows, missing = [], []
    for f in pf.get('mutual_funds', []):
        p = prices.get('mf', {}).get(f['name'])
        if not p:
            missing.append(f['name'])
            continue
        val = f['units'] * p['nav']
        rows.append({'kind': 'Mutual fund', 'name': f['name'], 'category': f.get('category', 'Equity'),
                     'qty': f['units'], 'price': p['nav'], 'price_date': p.get('date'), 'value': val,
                     'invested': f.get('invested'), 'sip': f.get('monthly_sip', 0), 'source': p.get('source')})
    for s in pf.get('stocks', []):
        p = prices.get('stocks', {}).get(s['symbol'])
        if not p:
            missing.append(s['symbol'])
            continue
        invested = s.get('invested', s['qty'] * s['avg_price'] if s.get('avg_price') else None)
        rows.append({'kind': 'Stock', 'name': s.get('name', s['symbol']), 'symbol': s['symbol'],
                     'category': s.get('sector', 'Stock'), 'qty': s['qty'], 'price': p['price'],
                     'price_date': (p.get('time') or '')[:10], 'value': s['qty'] * p['price'],
                     'invested': invested, 'sip': 0, 'source': p.get('source'),
                     'day_chg_pct': (p['price'] / p['prev_close'] - 1) * 100 if p.get('prev_close') else None,
                     'month_chg_pct': (p['price'] / p['month_ago'] - 1) * 100 if p.get('month_ago') else None})
    for o in pf.get('other_assets', []):
        rows.append({'kind': 'Other', 'name': o['name'], 'category': o.get('category', 'Other'), 'qty': None,
                     'price': None, 'value': o['value'], 'invested': o.get('invested'), 'sip': 0,
                     'source': 'you'})
    total = sum(r['value'] for r in rows)
    for r in rows:
        r['weight'] = r['value'] / total * 100 if total else 0
        if r.get('invested'):
            r['gain'] = r['value'] - r['invested']
            r['gain_pct'] = r['gain'] / r['invested'] * 100
    return rows, total, missing


def flags(rows, total, pf):
    out = []
    stocks = [r for r in rows if r['kind'] == 'Stock']
    funds = [r for r in rows if r['kind'] == 'Mutual fund']
    for r in rows:
        if r['kind'] == 'Stock' and r['weight'] > 10:
            out.append(f"{r['name']} is {r['weight']:.0f}% of the portfolio: one stock above 10% is concentrated.")
        if r['kind'] == 'Mutual fund' and r['weight'] > 35:
            out.append(f"{r['name']} is {r['weight']:.0f}% of the portfolio: a lot riding on one fund.")
        if r.get('gain_pct') is not None and r['gain_pct'] < -20:
            out.append(f"{r['name']} is down {abs(r['gain_pct']):.0f}% from cost: worth checking whether the reason you bought it still holds.")
    if len(funds) > 7:
        out.append(f'{len(funds)} mutual funds: beyond 5-7 funds the holdings usually overlap heavily.')
    stock_share = sum(r['weight'] for r in stocks)
    if stock_share > 40:
        out.append(f'Direct stocks are {stock_share:.0f}% of the portfolio, more than most people can research well.')
    debt = sum(r['weight'] for r in rows if 'debt' in str(r['category']).lower())
    age = pf.get('age')
    if age and age >= 40 and debt < 10:
        out.append(f'Only {debt:.0f}% in debt/fixed income at age {age}: consider whether that matches the risk you can take.')
    return out


def allocation(rows):
    alloc = {}
    for r in rows:
        key = r['kind'] if r['kind'] == 'Stock' else f"{r['kind']}: {r['category']}"
        alloc[key] = alloc.get(key, 0) + r['weight']
    return sorted(alloc.items(), key=lambda kv: -kv[1])


# ---------- HTML ----------

CSS_TD = 'padding:6px 8px;border-bottom:1px solid #e5e7eb;font-size:13px;'
CSS_TH = 'padding:6px 8px;border-bottom:2px solid #111827;font-size:12px;text-align:left;color:#374151;'


def esc(x):
    return html.escape(str(x))


def table(headers, rows, right=()):
    h = ''.join(f'<th style="{CSS_TH}{"text-align:right;" if i in right else ""}">{esc(c)}</th>'
                for i, c in enumerate(headers))
    body = ''
    for row in rows:
        body += '<tr>' + ''.join(
            f'<td style="{CSS_TD}{"text-align:right;white-space:nowrap;" if i in right else ""}">{c}</td>'
            for i, c in enumerate(row)) + '</tr>'
    return (f'<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin:8px 0 20px;">'
            f'<tr>{h}</tr>{body}</table>')


def color(x, text):
    if x is None:
        return esc(text)
    return f'<span style="color:{"#047857" if x >= 0 else "#b91c1c"};">{esc(text)}</span>'


def h2(t):
    return f'<h2 style="font-size:17px;margin:28px 0 6px;color:#111827;">{esc(t)}</h2>'


def commentary_html(text):
    out, items = [], []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(('- ', '* ')):
            items.append(f'<li style="margin:4px 0;">{esc(line[2:])}</li>')
            continue
        if items:
            out.append('<ul style="padding-left:20px;margin:6px 0;">' + ''.join(items) + '</ul>')
            items = []
        if line.startswith('#'):
            out.append(f'<p style="font-weight:600;margin:14px 0 4px;">{esc(line.lstrip("#").strip())}</p>')
        elif line:
            out.append(f'<p style="margin:6px 0;line-height:1.5;">{esc(line)}</p>')
    if items:
        out.append('<ul style="padding-left:20px;margin:6px 0;">' + ''.join(items) + '</ul>')
    return ''.join(out)


def build_html(s, news, commentary):
    a = s['assumptions']
    parts = [f'<div style="font-family:Arial,Helvetica,sans-serif;max-width:760px;margin:0 auto;color:#1f2937;">',
             f'<h1 style="font-size:22px;margin:0 0 4px;">Portfolio report, {esc(s["report_month"])}</h1>',
             f'<p style="margin:0 0 16px;color:#6b7280;font-size:13px;">Prices as of {esc(s["prices_fetched_at"][:16].replace("T", " "))} IST</p>']

    # headline numbers
    tiles = [('Portfolio value', short_inr(s['total_value'])),
             ('Invested', short_inr(s['total_invested'])),
             ('Gain', f"{short_inr(s['total_gain'])} ({pct(s['total_gain_pct'])})" if s['total_gain'] is not None else '-'),
             ('Since last report', f"{short_inr(s['change_since_last'])}" if s['change_since_last'] is not None else 'first report')]
    parts.append('<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;"><tr>' + ''.join(
        f'<td style="padding:10px;border:1px solid #e5e7eb;width:25%;vertical-align:top;">'
        f'<div style="font-size:11px;color:#6b7280;text-transform:uppercase;">{esc(k)}</div>'
        f'<div style="font-size:17px;font-weight:700;margin-top:4px;">{esc(v)}</div></td>' for k, v in tiles) + '</tr></table>')
    step = f' (steps up {a["sip_step_up_pct"]:g}% a year)' if a['sip_step_up_pct'] else ''
    parts.append(f'<p style="font-size:13px;color:#374151;">Monthly SIP: <b>{inr(s["monthly_sip"])}</b>{step}. '
                 f'One-time money to invest this month: <b>{inr(s["lump_sum"])}</b>.</p>')

    if commentary:
        parts.append(h2('What stands out this month'))
        parts.append(commentary_html(commentary))

    if s['flags']:
        parts.append(h2('Things to look at'))
        parts.append('<ul style="padding-left:20px;margin:6px 0;">' +
                     ''.join(f'<li style="margin:4px 0;font-size:13px;">{esc(f)}</li>' for f in s['flags']) + '</ul>')

    # holdings
    parts.append(h2('Holdings'))
    rows = []
    for r in sorted(s['holdings'], key=lambda r: -r['value']):
        extra = ''
        if r.get('month_chg_pct') is not None:
            extra = f'<br><span style="font-size:11px;color:#6b7280;">1M {pct(r["month_chg_pct"])}</span>'
        rows.append([f'{esc(r["name"])}<br><span style="font-size:11px;color:#6b7280;">{esc(r["kind"])} · {esc(r["category"])}</span>',
                     (f'{r["price"]:,.2f}' if r.get('price') else '-') + extra,
                     inr(r['value']), pct(r['weight'], sign=False),
                     inr(r['invested']) if r.get('invested') else '-',
                     color(r.get('gain'), f'{inr(r.get("gain"))} ({pct(r.get("gain_pct"))})') if r.get('gain') is not None else '-'])
    parts.append(table(['Holding', 'Price / NAV', 'Value', 'Weight', 'Invested', 'Gain'], rows, right=(1, 2, 3, 4, 5)))
    if s['missing_prices']:
        parts.append(f'<p style="font-size:12px;color:#b91c1c;">No price found for: {esc(", ".join(s["missing_prices"]))}. '
                     f'These are left out of every total and projection.</p>')

    parts.append(h2('Allocation'))
    parts.append(table(['Bucket', 'Share'], [[esc(k), pct(v, sign=False)] for k, v in s['allocation']], right=(1,)))

    # news
    if news:
        parts.append(h2('News about your holdings'))
        for n in news:
            link = f'<a href="{esc(n["url"])}" style="color:#1d4ed8;">{esc(n.get("headline", n["url"]))}</a>' if n.get('url') else esc(n.get('headline', ''))
            meta = ' · '.join(x for x in [n.get('holding'), n.get('source'), n.get('date')] if x)
            note = f'<br><span style="font-size:12px;">{esc(n["note"])}</span>' if n.get('note') else ''
            parts.append(f'<p style="margin:8px 0;font-size:13px;line-height:1.4;">{link}<br>'
                         f'<span style="font-size:11px;color:#6b7280;">{esc(meta)}</span>{note}</p>')

    # projections
    parts.append(h2('Where the portfolio could be'))
    parts.append(f'<p style="font-size:12px;color:#6b7280;margin:0;">Starts from today\'s value plus the one-time '
                 f'{inr(s["lump_sum"])}, adds the SIP every month. "Today\'s money" removes {a["inflation_pct"]:g}% inflation.</p>')
    names = list(a['returns_pct'])
    rows = []
    for y in PROJECTION_YEARS:
        row = [f'{y} yr' + ('s' if y > 1 else '')]
        for n in names:
            v = s['projections'][n][str(y)]
            row.append(f'{short_inr(v["nominal"])}<br><span style="font-size:11px;color:#6b7280;">{short_inr(v["today_rupees"])} today</span>')
        rows.append(row)
    parts.append(table(['In'] + [f'{n.title()} ({a["returns_pct"][n]:g}%/yr)' for n in names], rows,
                       right=tuple(range(1, len(names) + 1))))

    # retirement
    parts.append(h2('When could you retire?'))
    parts.append(f'<p style="font-size:12px;color:#6b7280;margin:0;">First year the corpus could pay this monthly amount '
                 f'(in today\'s rupees, rising {a["inflation_pct"]:g}% a year) for {a["years_in_retirement"]} years, '
                 f'while the remaining money earns {a["post_retirement_return_pct"]:g}% a year. You keep investing the SIP until then.</p>')
    rows = []
    for i, w in enumerate(s['withdrawals']):
        row = [f'{inr(w)}/month']
        for n in names:
            r = s['retirement'][n][i]
            if r['months'] is None:
                row.append(f'not within {a["max_years"]} yrs')
            else:
                when = f'{r["years"]:g} yrs' + (f' (age {r["age"]:.0f})' if r.get('age') else '')
                row.append(f'{when}<br><span style="font-size:11px;color:#6b7280;">needs {short_inr(r["corpus_needed"])}</span>')
        rows.append(row)
    parts.append(table(['Withdrawal'] + [n.title() for n in names], rows, right=tuple(range(1, len(names) + 1))))

    parts.append(h2('Assumptions'))
    parts.append('<ul style="padding-left:20px;font-size:12px;color:#374151;">' + ''.join(
        f'<li>{esc(t)}</li>' for t in [
            f'Returns: {", ".join(f"{n} {v:g}%" for n, v in a["returns_pct"].items())} a year on the whole portfolio, every year, no taxes or exit loads.',
            f'Inflation {a["inflation_pct"]:g}% a year. Return after retirement {a["post_retirement_return_pct"]:g}% a year, money lasting {a["years_in_retirement"]} years.',
            'The one-time amount is assumed invested today. Units, quantities and invested amounts come from what you gave me, not from your CAS or demat statement.',
        ]) + '</ul>')

    parts.append(f'<p style="font-size:11px;color:#6b7280;border-top:1px solid #e5e7eb;padding-top:10px;margin-top:24px;line-height:1.5;">'
                 f'<b>Not financial advice.</b> {esc(DISCLAIMER)}</p>')
    parts.append('<p style="font-size:11px;color:#6b7280;">To change your SIP, add a one-time amount, or update holdings, '
                 'tell Claude before the 3rd and the next report will use it.</p></div>')
    return '\n'.join(parts)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('portfolio')
    ap.add_argument('prices')
    ap.add_argument('--out', required=True)
    ap.add_argument('--news')
    ap.add_argument('--commentary')
    ap.add_argument('--history', help='JSON list of past snapshots; default: history.json next to the portfolio')
    ap.add_argument('--no-history-update', action='store_true', help='do not append this run to the history')
    a = ap.parse_args()

    pf = json.load(open(a.portfolio, encoding='utf-8'))
    prices = json.load(open(a.prices, encoding='utf-8'))
    asm = {**DEFAULTS, **pf.get('assumptions', {})}
    asm['returns_pct'] = pf.get('assumptions', {}).get('returns_pct') or DEFAULTS['returns_pct']
    if 'sip_step_up_pct' in pf:
        asm['sip_step_up_pct'] = pf['sip_step_up_pct']

    rows, total, missing = value_holdings(pf, prices)
    invested_rows = [r for r in rows if r.get('invested')]
    total_invested = sum(r['invested'] for r in invested_rows) if invested_rows else None
    gain = sum(r['value'] for r in invested_rows) - total_invested if invested_rows else None

    sip = pf.get('monthly_sip')
    if sip is None:
        sip = sum(f.get('monthly_sip', 0) for f in pf.get('mutual_funds', []))
    lump = pf.get('lump_sum_this_month', 0) or 0
    withdrawals = pf.get('monthly_withdrawals') or [50000, 100000, 150000, 200000]

    months = asm['max_years'] * 12
    infl_m = monthly_rate(asm['inflation_pct'])
    projections, retirement = {}, {}
    for name, r in asm['returns_pct'].items():
        path = project(total + lump, sip, r, months, asm['sip_step_up_pct'])
        projections[name] = {str(y): {'nominal': path[y * 12], 'today_rupees': path[y * 12] / (1 + infl_m) ** (y * 12)}
                             for y in PROJECTION_YEARS}
        retirement[name] = retirement_table(path, withdrawals, asm, pf.get('age'))

    hist_path = a.history or os.path.join(os.path.dirname(os.path.abspath(a.portfolio)), 'history.json')
    history = json.load(open(hist_path, encoding='utf-8')) if os.path.exists(hist_path) else []
    last = history[-1] if history else None

    fetched = prices.get('fetched_at') or datetime.now().isoformat()
    summary = {
        'report_month': datetime.fromisoformat(fetched[:19]).strftime('%B %Y'),
        'prices_fetched_at': fetched,
        'total_value': total, 'total_invested': total_invested, 'total_gain': gain,
        'total_gain_pct': gain / total_invested * 100 if gain is not None and total_invested else None,
        'change_since_last': total - last['total_value'] if last else None,
        'last_report_date': last['date'] if last else None,
        'monthly_sip': sip, 'lump_sum': lump, 'withdrawals': withdrawals,
        'holdings': rows, 'allocation': allocation(rows), 'flags': flags(rows, total, pf),
        'missing_prices': missing, 'assumptions': asm,
        'projections': projections, 'retirement': retirement,
    }

    news = json.load(open(a.news, encoding='utf-8')) if a.news else []
    commentary = open(a.commentary, encoding='utf-8').read() if a.commentary else ''
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'report.html'), 'w', encoding='utf-8') as f:
        f.write(build_html(summary, news, commentary))
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    if not a.no_history_update:
        history.append({'date': date.today().isoformat(), 'total_value': round(total, 2),
                        'total_invested': total_invested, 'monthly_sip': sip, 'lump_sum': lump})
        with open(hist_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)

    print(f'value {inr(total)} | invested {inr(total_invested)} | gain {inr(gain)} | missing {len(missing)}')
    base = list(asm['returns_pct'])[len(asm['returns_pct']) // 2]
    for r in retirement[base]:
        print(f"  {inr(r['withdrawal'])}/month ({base}): " +
              (f"{r['years']} yrs, needs {short_inr(r['corpus_needed'])}" if r['months'] is not None else 'not reached'))
    print(f'wrote {a.out}/report.html and summary.json')


if __name__ == '__main__':
    main()

"""Render the monthly report as a designed, print-ready PDF (A4) with charts.

    python make_pdf.py <out_dir> [--plan plan.json] [--news news.json] [--commentary commentary.md]
                       [--redact] [--name "Akash"]

Reads <out_dir>/summary.json (written by report.py) and writes <out_dir>/report-print.html and
<out_dir>/report.pdf. Charts are inline SVG, so the HTML has no outside dependencies.

PDF engine: Playwright (Python or Node) if installed, otherwise Chrome/Chromium/Edge headless --print-to-pdf.
If none is found, open report-print.html in a browser and Print -> Save as PDF.

--redact hides every rupee amount (keeps percentages, weights, years) for sharing on social media.
"""
import argparse
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import inr, short_inr, pct, DISCLAIMER  # noqa: E402

INK = '#0f1b2d'
MUTED = '#5b6474'
LINE = '#e6e8ee'
PAPER = '#fbfaf7'
BUCKET_COLORS = {'Large': '#1f3a8a', 'Flexi/Multi': '#6d28d9', 'Mid': '#0f8a7e', 'Small': '#e2621b',
                 'Debt': '#64748b', 'Gold/Silver': '#c99a2e', 'Other': '#a3aab8'}
BUCKET_ORDER = list(BUCKET_COLORS)
SCEN_COLORS = {'conservative': '#94a3b8', 'base': '#1f3a8a', 'optimistic': '#0f8a7e'}


def esc(x):
    return html.escape(str(x))


def bucket(r):
    if r.get('cap'):
        return r['cap']
    t = f"{r.get('category', '')} {r.get('name', '')}".lower()
    if 'small' in t:
        return 'Small'
    if 'mid' in t:
        return 'Mid'
    if 'flexi' in t or 'multi' in t:
        return 'Flexi/Multi'
    if 'debt' in t or 'ppf' in t or 'epf' in t or ' rd' in t or 'fd' in t or 'liquid' in t:
        return 'Debt'
    if 'gold' in t or 'silver' in t:
        return 'Gold/Silver'
    if any(k in t for k in ('large', 'nifty 50', 'next 50', 'bank', 'bluechip', 'index', 'sensex')):
        return 'Large'
    return 'Other'


def mix(values):
    total = sum(values.values()) or 1
    return {k: v / total * 100 for k, v in values.items() if v > 0}


# ---------- SVG charts ----------

def donut(shares, size=190, hole=0.62, center_top='', center_bottom=''):
    r = size / 2
    ri = r * hole
    parts, a0 = [], -math.pi / 2
    for k in BUCKET_ORDER:
        if k not in shares:
            continue
        frac = shares[k] / 100
        a1 = a0 + frac * 2 * math.pi
        large = 1 if a1 - a0 > math.pi else 0
        if frac >= 0.9999:
            parts.append(f'<circle cx="{r}" cy="{r}" r="{(r + ri) / 2}" fill="none" stroke="{BUCKET_COLORS[k]}" stroke-width="{r - ri}"/>')
        else:
            p = (f'M{r + r * math.cos(a0):.2f},{r + r * math.sin(a0):.2f} '
                 f'A{r},{r} 0 {large} 1 {r + r * math.cos(a1):.2f},{r + r * math.sin(a1):.2f} '
                 f'L{r + ri * math.cos(a1):.2f},{r + ri * math.sin(a1):.2f} '
                 f'A{ri},{ri} 0 {large} 0 {r + ri * math.cos(a0):.2f},{r + ri * math.sin(a0):.2f} Z')
            parts.append(f'<path d="{p}" fill="{BUCKET_COLORS[k]}" stroke="{PAPER}" stroke-width="2"/>')
        a0 = a1
    parts.append(f'<text x="{r}" y="{r - 4}" text-anchor="middle" font-size="22" font-weight="700" fill="{INK}">{esc(center_top)}</text>')
    parts.append(f'<text x="{r}" y="{r + 16}" text-anchor="middle" font-size="10" fill="{MUTED}" letter-spacing="1">{esc(center_bottom)}</text>')
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(parts)}</svg>'


def stacked_bar(shares, width=460, height=16):
    x, out = 0, []
    for k in BUCKET_ORDER:
        if k in shares:
            w = shares[k] / 100 * width
            out.append(f'<rect x="{x:.1f}" y="0" width="{max(w - 1.5, 0):.1f}" height="{height}" rx="3" fill="{BUCKET_COLORS[k]}"/>')
            if w > 34:
                out.append(f'<text x="{x + w / 2:.1f}" y="{height - 4}" text-anchor="middle" font-size="9.5" font-weight="600" fill="#fff">{shares[k]:.0f}%</text>')
            x += w
    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(out)}</svg>'


def projection_chart(s, redact, width=640, height=250):
    names = list(s['assumptions']['returns_pct'])
    years = [0] + [int(y) for y in s['projections'][names[0]]]
    start = s['total_value'] + s['lump_sum']
    series = {n: [start] + [s['projections'][n][str(y)]['nominal'] for y in years[1:]] for n in names}
    vmax = max(max(v) for v in series.values())
    # nice max
    mag = 10 ** int(math.log10(vmax))
    top = math.ceil(vmax / mag) * mag
    L, R, T, B = 58, 118, 14, 30
    pw, ph = width - L - R, height - T - B
    X = lambda y: L + y / years[-1] * pw  # noqa: E731
    Y = lambda v: T + ph - v / top * ph  # noqa: E731
    g = []
    for i in range(5):
        v = top * i / 4
        g.append(f'<line x1="{L}" x2="{L + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{LINE}"/>')
        lab = '₹ ••' if redact and i else short_inr(v).replace('₹0', '0')
        g.append(f'<text x="{L - 8}" y="{Y(v) + 3:.1f}" text-anchor="end" font-size="9.5" fill="{MUTED}">{esc(lab)}</text>')
    for y in years:
        if y in (0, 5, 10, 15, 20, 25, 30):
            g.append(f'<text x="{X(y):.1f}" y="{T + ph + 18}" text-anchor="middle" font-size="9.5" fill="{MUTED}">{"Now" if y == 0 else f"{y}y"}</text>')
    base = names[len(names) // 2]
    # band between conservative and optimistic
    lo, hi = series[names[0]], series[names[-1]]
    band = ' '.join(f'{X(y):.1f},{Y(v):.1f}' for y, v in zip(years, hi)) + ' ' + \
           ' '.join(f'{X(y):.1f},{Y(v):.1f}' for y, v in reversed(list(zip(years, lo))))
    g.append(f'<polygon points="{band}" fill="{SCEN_COLORS["base"]}" opacity="0.07"/>')
    for n in names:
        pts = ' '.join(f'{X(y):.1f},{Y(v):.1f}' for y, v in zip(years, series[n]))
        c = SCEN_COLORS.get(n, INK)
        w = 2.6 if n == base else 1.6
        dash = '' if n == base else ' stroke-dasharray="4 3"'
        g.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{w}"{dash} stroke-linejoin="round"/>')
        endv = series[n][-1]
        lab = f'{n.title()} {"₹ ••" if redact else short_inr(endv)}'
        g.append(f'<circle cx="{X(years[-1]):.1f}" cy="{Y(endv):.1f}" r="3" fill="{c}"/>')
        g.append(f'<text x="{X(years[-1]) + 7:.1f}" y="{Y(endv) + 3:.1f}" font-size="9.5" font-weight="600" fill="{c}">{esc(lab)}</text>')
    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(g)}</svg>'


def holding_bars(rows, width=640):
    rows = sorted(rows, key=lambda r: -r['value'])
    bh, gap, L = 22, 8, 230
    h = len(rows) * (bh + gap)
    maxw = max(r['weight'] for r in rows) or 1
    g = []
    for i, r in enumerate(rows):
        y = i * (bh + gap)
        b = bucket(r)
        w = r['weight'] / maxw * (width - L - 110)
        name = r['name'] if len(r['name']) <= 36 else r['name'][:34] + '…'
        g.append(f'<text x="0" y="{y + 15}" font-size="10.5" fill="{INK}">{esc(name)}</text>')
        g.append(f'<rect x="{L}" y="{y + 3}" width="{max(w, 2):.1f}" height="{bh - 6}" rx="3" fill="{BUCKET_COLORS[b]}"/>')
        g.append(f'<text x="{L + w + 6:.1f}" y="{y + 15}" font-size="10" font-weight="600" fill="{INK}">{r["weight"]:.1f}%</text>')
        if r.get('gain_pct') is not None:
            c = '#0f7a4a' if r['gain_pct'] >= 0 else '#b42318'
            g.append(f'<text x="{width}" y="{y + 15}" text-anchor="end" font-size="10" fill="{c}">{pct(r["gain_pct"])}</text>')
    return f'<svg width="{width}" height="{h}" viewBox="0 0 {width} {h}">{"".join(g)}</svg>'


# ---------- page ----------

CSS = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: {PAPER}; color: {INK}; font-family: Inter, "Segoe UI", system-ui, -apple-system, sans-serif;
       font-size: 11px; line-height: 1.5; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 210mm; min-height: 297mm; padding: 16mm 15mm 14mm; position: relative; page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
.serif {{ font-family: "Charter", "Bitstream Charter", Georgia, "DejaVu Serif", serif; }}
.cover {{ background: {INK}; color: #fff; margin: -16mm -15mm 0; padding: 16mm 15mm 12mm; }}
.eyebrow {{ font-size: 9px; letter-spacing: 2.2px; text-transform: uppercase; color: #9fb0c8; font-weight: 600; }}
h1 {{ font-size: 34px; line-height: 1.1; margin: 8px 0 6px; font-weight: 700; }}
h2 {{ font-size: 19px; margin: 0 0 4px; font-weight: 700; }}
.sub {{ color: #c7d2e2; font-size: 11.5px; }}
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 18px; }}
.kpi {{ border-top: 2px solid #34507a; padding-top: 8px; }}
.kpi .l {{ font-size: 8.5px; letter-spacing: 1.6px; text-transform: uppercase; color: #9fb0c8; }}
.kpi .v {{ font-size: 21px; font-weight: 700; margin-top: 2px; }}
.kpi .d {{ font-size: 10px; color: #8fe0c2; }}
.section {{ margin-top: 20px; }}
.kicker {{ font-size: 8.5px; letter-spacing: 2px; text-transform: uppercase; color: {MUTED}; font-weight: 600; margin-bottom: 3px; }}
.lead {{ font-size: 13px; line-height: 1.55; margin: 6px 0 10px; }}
.note {{ color: {MUTED}; font-size: 9.5px; }}
.grid2 {{ display: grid; grid-template-columns: 200px 1fr; gap: 22px; align-items: center; }}
.legend div {{ display: flex; align-items: center; gap: 8px; margin: 5px 0; font-size: 11px; }}
.sw {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
.legend .p {{ margin-left: auto; font-weight: 600; }}
ul.clean {{ padding: 0; margin: 6px 0; list-style: none; }}
ul.clean li {{ padding: 7px 0 7px 16px; border-bottom: 1px solid {LINE}; position: relative; font-size: 11px; }}
ul.clean li:before {{ content: ""; position: absolute; left: 0; top: 13px; width: 6px; height: 6px; border-radius: 50%; background: #0f8a7e; }}
.flag {{ background: #fff7ed; border-left: 3px solid #e2621b; padding: 8px 10px; margin: 6px 0; font-size: 10.5px; border-radius: 0 6px 6px 0; }}
.cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
.card {{ background: #fff; border: 1px solid {LINE}; border-radius: 10px; padding: 12px 13px; break-inside: avoid; }}
.card .amt {{ font-size: 20px; font-weight: 700; }}
.card .h {{ font-size: 11.5px; font-weight: 600; margin-top: 1px; }}
.card .m {{ font-size: 9.5px; color: {MUTED}; margin-bottom: 6px; }}
.card p {{ margin: 0; font-size: 10.3px; }}
.pill {{ display: inline-block; font-size: 8.5px; font-weight: 600; padding: 2px 7px; border-radius: 99px; color: #fff; letter-spacing: .4px; }}
.mixrow {{ display: grid; grid-template-columns: 70px 1fr; align-items: center; gap: 10px; margin: 6px 0; font-size: 10px; color: {MUTED}; }}
table.t {{ width: 100%; border-collapse: collapse; font-size: 10.5px; }}
table.t th {{ text-align: left; font-size: 8.5px; letter-spacing: 1.4px; text-transform: uppercase; color: {MUTED}; font-weight: 600; padding: 6px 6px; border-bottom: 1.5px solid {INK}; }}
table.t td {{ padding: 7px 6px; border-bottom: 1px solid {LINE}; vertical-align: top; }}
table.t td.r, table.t th.r {{ text-align: right; white-space: nowrap; }}
.yr {{ font-size: 15px; font-weight: 700; }}
.na {{ color: #a3aab8; }}
.news {{ padding: 8px 0; border-bottom: 1px solid {LINE}; }}
.news a {{ color: {INK}; font-weight: 600; text-decoration: none; }}
.foot {{ position: absolute; bottom: 9mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between;
         font-size: 8.5px; color: {MUTED}; border-top: 1px solid {LINE}; padding-top: 6px; }}
.disc {{ background: #f1f3f7; border-radius: 8px; padding: 10px 12px; font-size: 9px; color: {MUTED}; margin-top: 16px; }}
.banner {{ background: #fde68a; color: #713f12; font-size: 9.5px; padding: 6px 10px; border-radius: 6px; margin-bottom: 10px; display: inline-block; }}
"""


def commentary_blocks(text):
    lead, bullets = [], []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(('- ', '* ')):
            bullets.append(line[2:])
        elif line and not line.startswith('#'):
            lead.append(line)
    return ' '.join(lead), bullets


def build(s, plan, news, commentary, redact, who):
    money = (lambda x: '₹ ••••') if redact else inr
    smoney = (lambda x: '₹ ••') if redact else short_inr
    a = s['assumptions']
    names = list(a['returns_pct'])
    base = names[len(names) // 2]
    rows = s['holdings']
    by_bucket = {}
    for r in rows:
        by_bucket[bucket(r)] = by_bucket.get(bucket(r), 0) + r['value']
    now_mix = mix(by_bucket)
    month = s['report_month']
    foot = lambda n: f'<div class="foot"><span>Portfolio report · {esc(month)}</span><span>Not financial advice · page {n}</span></div>'  # noqa: E731

    # ---------- page 1 ----------
    gain = s['total_gain']
    p1 = ['<div class="page"><div class="cover">',
          f'<div class="eyebrow">Monthly portfolio report{" · " + esc(who) if who else ""}</div>',
          f'<h1 class="serif">{esc(month)}</h1>',
          f'<div class="sub">Prices as of {esc(s["prices_fetched_at"][:10])} · {len(rows)} holdings · '
          f'{money(s["monthly_sip"])} invested every month</div>',
          '<div class="kpis">',
          f'<div class="kpi"><div class="l">Portfolio value</div><div class="v">{smoney(s["total_value"])}</div></div>',
          f'<div class="kpi"><div class="l">Invested</div><div class="v">{smoney(s["total_invested"])}</div></div>',
          f'<div class="kpi"><div class="l">Gain</div><div class="v">{pct(s["total_gain_pct"])}</div>'
          f'<div class="d">{smoney(gain) if gain is not None else ""}</div></div>',
          f'<div class="kpi"><div class="l">Since last report</div><div class="v">'
          f'{smoney(s["change_since_last"]) if s["change_since_last"] is not None else "First"}</div></div>',
          '</div></div>']
    if redact:
        p1.insert(1, '')
        p1.append('<div class="section"><span class="banner">Amounts hidden for sharing. Percentages, mix and timelines are from a real run.</span></div>')
    lead, bullets = commentary_blocks(commentary or '')
    if redact:
        lead = re.sub(r'₹[\d,.]+\s?(?:lakh|L|Cr|k)?', '₹ ••', lead)
        bullets = [re.sub(r'₹[\d,.]+\s?(?:lakh|L|Cr|k)?(?!\s?(?:a month of retirement|/month))', '₹ ••', b) for b in bullets]
    p1.append('<div class="section"><div class="kicker">The month in brief</div>')
    if lead:
        p1.append(f'<p class="lead serif">{esc(lead)}</p>')
    if bullets:
        p1.append('<ul class="clean">' + ''.join(f'<li>{esc(b)}</li>' for b in bullets) + '</ul>')
    p1.append('</div>')
    p1.append('<div class="section"><div class="kicker">Where your money sits</div><h2 class="serif">Mix by market size</h2>'
              '<div class="grid2">' + donut(now_mix, center_top=f'{len(rows)}', center_bottom='HOLDINGS') +
              '<div class="legend">' + ''.join(
                  f'<div><span class="sw" style="background:{BUCKET_COLORS[k]}"></span>{esc(k)} cap'
                  f'{"" if k in ("Large", "Mid", "Small") else ""}<span class="p">{now_mix[k]:.1f}%</span></div>'
                  for k in BUCKET_ORDER if k in now_mix) + '</div></div></div>')
    if s['flags']:
        p1.append('<div class="section">' + ''.join(f'<div class="flag">{esc(f)}</div>' for f in s['flags']) + '</div>')
    p1.append(foot(1) + '</div>')

    # ---------- page 2: holdings + plan ----------
    p2 = ['<div class="page"><div class="kicker">Holdings</div><h2 class="serif">Weight of each holding, and its return so far</h2>',
          '<div style="margin-top:10px">' + holding_bars(rows) + '</div>',
          '<table class="t" style="margin-top:12px"><tr><th>Holding</th><th class="r">Value</th><th class="r">Invested</th><th class="r">Gain</th></tr>' +
          ''.join(f'<tr><td>{esc(r["name"])}<div class="note">{esc(r["kind"])} · {esc(r["category"])}</div></td>'
                  f'<td class="r">{money(r["value"])}</td><td class="r">{money(r.get("invested")) if r.get("invested") else "-"}</td>'
                  f'<td class="r" style="color:{"#0f7a4a" if (r.get("gain") or 0) >= 0 else "#b42318"}">'
                  f'{pct(r.get("gain_pct")) if r.get("gain") is not None else "-"}</td></tr>'
                  for r in sorted(rows, key=lambda r: -r['value'])) + '</table>']
    if news:
        p2.append('<div class="section"><div class="kicker">In the news</div>' + ''.join(
            f'<div class="news"><a href="{esc(it.get("url", "#"))}">{esc(it.get("headline", ""))}</a>'
            f'<div class="note">{esc(" · ".join(x for x in [it.get("holding"), it.get("source"), it.get("date")] if x))}</div>'
            f'{"<div>" + esc(it["note"]) + "</div>" if it.get("note") else ""}</div>' for it in news) + '</div>')
    p2.append(foot(2) + '</div>')

    pages = [''.join(p1), ''.join(p2)]

    if plan:
        after = dict(by_bucket)
        for it in plan.get('items', []):
            after[it.get('bucket', 'Other')] = after.get(it.get('bucket', 'Other'), 0) + it['amount']
        after_mix = mix(after)
        target = plan.get('target_mix', {})
        total_new = sum(it['amount'] for it in plan.get('items', []))
        p3 = ['<div class="page"><div class="kicker">This month\'s money</div>',
              f'<h2 class="serif">Where the new {money(total_new)} could go</h2>']
        if plan.get('summary'):
            p3.append(f'<p class="lead serif">{esc(plan["summary"])}</p>')
        p3.append('<div class="cards">')
        for it in plan.get('items', []):
            b = it.get('bucket', 'Other')
            units = f'{it["units"]} units at ~₹{it["price"]:,.2f}' if it.get('units') else it.get('how', '')
            p3.append(f'<div class="card"><span class="pill" style="background:{BUCKET_COLORS.get(b, INK)}">{esc(b.upper())} CAP</span>'
                      f'<div class="amt" style="margin-top:6px">{money(it["amount"])}</div>'
                      f'<div class="h">{esc(it["holding"])}</div><div class="m">{esc(it.get("kind", ""))}'
                      f'{" · " + esc(units) if units and not redact else ""}</div><p>{esc(it["why"])}</p></div>')
        p3.append('</div>')
        p3.append('<div class="section"><div class="kicker">How the mix moves</div>')
        p3.append(f'<div class="mixrow"><span>Today</span>{stacked_bar(now_mix)}</div>')
        p3.append(f'<div class="mixrow"><span>After</span>{stacked_bar(after_mix)}</div>')
        if target:
            p3.append(f'<div class="mixrow"><span>Target</span>{stacked_bar(mix(target))}</div>')
        if plan.get('target_note'):
            p3.append(f'<p class="note">{esc(plan["target_note"])}</p>')
        p3.append('</div>')
        if plan.get('hold_off'):
            p3.append('<div class="section"><div class="kicker">Hold off adding to</div><ul class="clean">' +
                      ''.join(f'<li><b>{esc(h["holding"])}</b>: {esc(h["why"])}</li>' for h in plan['hold_off']) + '</ul></div>')
        p3.append('<p class="note" style="margin-top:10px">This is a rules-based rebalancing idea built from your own holdings and a target mix, '
                  'not a recommendation to buy any security. Check it against your goals, emergency fund and taxes first.</p>')
        p3.append(foot(3) + '</div>')
        pages.append(''.join(p3))

    # ---------- future page ----------
    n = len(pages) + 1
    p4 = ['<div class="page"><div class="kicker">The long view</div><h2 class="serif">Where the portfolio could be</h2>',
          f'<p class="note">Today\'s value plus this month\'s one-time money, with {money(s["monthly_sip"])} added every month'
          f'{" and raised " + format(a["sip_step_up_pct"], "g") + "% a year" if a["sip_step_up_pct"] else ""}. '
          f'Shaded band: {a["returns_pct"][names[0]]:g}% to {a["returns_pct"][names[-1]]:g}% a year.</p>',
          projection_chart(s, redact),
          '<div class="section"><div class="kicker">Financial freedom</div><h2 class="serif">When could you retire?</h2>',
          f'<p class="note">First year your money could pay this monthly amount in today\'s rupees, rising {a["inflation_pct"]:g}% a year, '
          f'for {a["years_in_retirement"]} years while the rest earns {a["post_retirement_return_pct"]:g}%.</p>',
          '<table class="t"><tr><th>Monthly income</th>' + ''.join(f'<th class="r">{esc(x.title())} · {a["returns_pct"][x]:g}%</th>' for x in names) + '</tr>']
    for i, w in enumerate(s['withdrawals']):
        cells = []
        for x in names:
            r = s['retirement'][x][i]
            if r['months'] is None:
                cells.append(f'<td class="r na">beyond {a["max_years"]} yrs</td>')
            else:
                age = f' · age {r["age"]:.0f}' if r.get('age') else ''
                cells.append(f'<td class="r"><span class="yr">{r["years"]:.0f}</span> yrs{age}'
                             f'<div class="note">needs {smoney(r["corpus_needed"])}</div></td>')
        p4.append(f'<tr><td><b>{inr(w)}</b> /month</td>{"".join(cells)}</tr>')
    p4.append('</table></div>')
    p4.append(f'<div class="disc"><b>Not financial advice.</b> {esc(DISCLAIMER)} Assumptions: '
              f'{", ".join(f"{x} {v:g}%" for x, v in a["returns_pct"].items())} a year on everything, inflation {a["inflation_pct"]:g}%, '
              'no taxes or exit loads.</div>')
    p4.append(foot(n) + '</div>')
    pages.append(''.join(p4))

    body = ''.join(pages)
    if redact:  # catch amounts inside free text (plan reasons, notes); keep the withdrawal options
        body = re.sub(r'₹[\d,]+(?:\.\d+)?(?:\s?(?:lakh|L|Cr|k)\b)?(?!</b> /month|/month| a month of retirement|[\d,])', '₹ ••', body)
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>Portfolio report {esc(month)}</title>'
            f'<style>{CSS}</style></head><body>{body}</body></html>')


def to_pdf(html_path, pdf_path):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto('file://' + os.path.abspath(html_path))
            pg.pdf(path=pdf_path, format='A4', print_background=True, prefer_css_page_size=True)
            b.close()
        return 'playwright (python)'
    except Exception:
        pass
    if shutil.which('node'):
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              "await p.goto('file://'+process.argv[1]);await p.pdf({path:process.argv[2],format:'A4',printBackground:true,"
              "preferCSSPageSize:true});await b.close();})().catch(e=>{console.error(e);process.exit(1)});")
        r = subprocess.run(['node', '-e', js, os.path.abspath(html_path), os.path.abspath(pdf_path)], capture_output=True)
        if r.returncode == 0:
            return 'playwright (node)'
    for exe in ('chromium', 'chromium-browser', 'google-chrome', 'chrome', 'msedge',
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        path = shutil.which(exe) or (exe if os.path.exists(exe) else None)
        if path:
            r = subprocess.run([path, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                                f'--print-to-pdf={os.path.abspath(pdf_path)}', 'file://' + os.path.abspath(html_path)],
                               capture_output=True)
            if r.returncode == 0 and os.path.exists(pdf_path):
                return os.path.basename(path)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out_dir')
    ap.add_argument('--plan')
    ap.add_argument('--news')
    ap.add_argument('--commentary')
    ap.add_argument('--redact', action='store_true')
    ap.add_argument('--name', default='')
    ap.add_argument('--pdf-name', default=None)
    a = ap.parse_args()
    s = json.load(open(os.path.join(a.out_dir, 'summary.json'), encoding='utf-8'))
    plan = json.load(open(a.plan, encoding='utf-8')) if a.plan else None
    news = json.load(open(a.news, encoding='utf-8')) if a.news else []
    commentary = open(a.commentary, encoding='utf-8').read() if a.commentary else ''
    stem = a.pdf_name or ('report-redacted' if a.redact else 'report')
    html_path = os.path.join(a.out_dir, stem + '-print.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(build(s, plan, news, commentary, a.redact, a.name))
    pdf_path = os.path.join(a.out_dir, stem + '.pdf')
    engine = to_pdf(html_path, pdf_path)
    if engine:
        print(f'wrote {pdf_path} (via {engine})')
    else:
        print(f'wrote {html_path}; no PDF engine found: open it in a browser and Print -> Save as PDF')


if __name__ == '__main__':
    main()

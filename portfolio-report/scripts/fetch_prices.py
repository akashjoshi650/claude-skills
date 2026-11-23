"""Fetch the latest prices for an Indian stock + mutual fund portfolio.

Mutual funds: AMFI's official daily NAV file (every scheme, one download).
Stocks: Yahoo Finance chart endpoint (unofficial, free, no key), NSE as `SYMBOL.NS`, BSE as `SYMBOL.BO`.

Standard library only. Anything that can't be fetched is listed under "missing" in the output, so Claude can
look it up by web search and fill it in by hand (with "source": "web search").

    python fetch_prices.py portfolio.json prices.json
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

AMFI_URL = 'https://portal.amfiindia.com/spages/NAVAll.txt'
YAHOO_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d'
UA = {'User-Agent': 'Mozilla/5.0 (portfolio-report skill)'}
IST = timezone(timedelta(hours=5, minutes=30))


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def yahoo_symbol(stock):
    sym = stock['symbol'].strip().upper()
    if '.' in sym:  # already has a suffix
        return sym
    return sym + ('.BO' if stock.get('exchange', 'NSE').upper() == 'BSE' else '.NS')


def parse_amfi(text):
    """Map scheme code -> {name, nav, date}. Lines: code;isin1;isin2;name;nav;date"""
    navs = {}
    for line in text.splitlines():
        parts = line.split(';')
        if len(parts) < 6 or not parts[0].strip().isdigit():
            continue
        try:
            nav = float(parts[4])
        except ValueError:
            continue  # "N.A." for suspended schemes
        navs[parts[0].strip()] = {'name': parts[3].strip(), 'nav': nav, 'date': parts[5].strip(),
                                  'isins': [p.strip() for p in parts[1:3] if p.strip() not in ('', '-')]}
    return navs


def find_fund(fund, navs):
    code = str(fund.get('amfi_code', '')).strip()
    if code and code in navs:
        return code
    isin = fund.get('isin', '').strip()
    if isin:
        for c, v in navs.items():
            if isin in v['isins']:
                return c
    name = fund.get('name', '').lower()
    if name:
        exact = [c for c, v in navs.items() if v['name'].lower() == name]
        if len(exact) == 1:
            return exact[0]
    return None


def fetch_stock(sym):
    data = json.loads(get(YAHOO_URL.format(sym=urllib.parse.quote(sym))))
    res = data['chart']['result'][0]
    meta = res['meta']
    closes = [c for c in res.get('indicators', {}).get('quote', [{}])[0].get('close', []) if c is not None]
    t = meta.get('regularMarketTime')
    return {
        'price': meta['regularMarketPrice'],
        'prev_close': meta.get('chartPreviousClose') if len(closes) < 2 else closes[-2],
        'month_ago': closes[0] if closes else None,
        'currency': meta.get('currency', 'INR'),
        'time': datetime.fromtimestamp(t, IST).isoformat() if t else None,
        'source': 'yahoo',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('portfolio')
    ap.add_argument('out')
    a = ap.parse_args()
    pf = json.load(open(a.portfolio, encoding='utf-8'))
    out = {'fetched_at': datetime.now(IST).isoformat(timespec='seconds'), 'mf': {}, 'stocks': {}, 'missing': []}

    funds = pf.get('mutual_funds', [])
    if funds:
        try:
            navs = parse_amfi(get(AMFI_URL, timeout=60))
        except (urllib.error.URLError, OSError) as e:
            navs = {}
            print(f'AMFI NAV file failed: {e}', file=sys.stderr)
        for f in funds:
            code = find_fund(f, navs)
            if code:
                v = navs[code]
                out['mf'][f['name']] = {'amfi_code': code, 'nav': v['nav'], 'date': v['date'],
                                        'amfi_name': v['name'], 'source': 'amfi'}
            else:
                out['missing'].append({'type': 'mf', 'name': f['name'], 'amfi_code': f.get('amfi_code')})

    for s in pf.get('stocks', []):
        sym = yahoo_symbol(s)
        try:
            out['stocks'][s['symbol']] = dict(fetch_stock(sym), yahoo_symbol=sym)
        except (urllib.error.URLError, OSError, KeyError, IndexError, TypeError, ValueError) as e:
            out['missing'].append({'type': 'stock', 'symbol': s['symbol'], 'yahoo_symbol': sym, 'error': str(e)[:120]})

    json.dump(out, open(a.out, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f"prices: {len(out['mf'])} funds, {len(out['stocks'])} stocks, {len(out['missing'])} missing -> {a.out}")
    for m in out['missing']:
        print('  missing:', m.get('name') or m.get('symbol'))


if __name__ == '__main__':
    main()

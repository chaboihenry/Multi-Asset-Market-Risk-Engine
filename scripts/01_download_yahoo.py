"""Download raw daily prices for XIU.TO, SPY and GLD from Yahoo Finance.
Saves one untouched CSV per ticker to data/raw/yahoo/. Skips files that already exist.
Expected: XIU from ~1999, SPY from 1993, GLD from Nov 2004; XIU in CAD, others USD.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import YAHOO

TICKERS = ['GLD', 'SPY', 'XIU.TO']
START = '1990-01-01'

def download(ticker):
    df = yf.download(ticker, start=START, auto_adjust=False, multi_level_index=False)
    if df.empty:
        raise ValueError(f"no data returned for {ticker}")
    return df

def main():
    YAHOO.mkdir(parents=True, exist_ok=True)
    for ticker in TICKERS:
        output = YAHOO / f"{ticker}.csv"
        if output.exists():
            print(f"skip {ticker}: already saved")
            continue
        df = download(ticker)
        currency = yf.Ticker(ticker).fast_info['currency']
        print(f"{ticker}: {df.index.min().date()} to {df.index.max().date()}, {len(df)} rows {currency}")
        df.to_csv(output)

if __name__ == "__main__":
    main()

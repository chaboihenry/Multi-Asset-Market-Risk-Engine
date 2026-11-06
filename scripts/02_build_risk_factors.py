"""Build the daily risk-factor table (levels) on the Canadian business-day calendar.
Loads BoC, FRED and Yahoo raw files, aligns them, forward-fills, and saves
data/processed/risk_factors.csv. Expected: 2004-11-18 to 2026-10-27, ~5,500 rows.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import BOC, FRED, YAHOO, PROCESSED

BOC_BENCHMARK = {
    "BD.CDN.2YR.DQ.YLD": "goc_2y",
    "BD.CDN.3YR.DQ.YLD": "goc_3y",
    "BD.CDN.5YR.DQ.YLD": "goc_5y",
    "BD.CDN.7YR.DQ.YLD": "goc_7y",
    "BD.CDN.10YR.DQ.YLD": "goc_10y",
    "BD.CDN.LONG.DQ.YLD": "goc_long",
}
BOC_TBILLS = {
    "TB.CDN.30D.MID": "tb_1m",
    "TB.CDN.60D.MID": "tb_2m",
    "TB.CDN.90D.MID": "tb_3m",
    "TB.CDN.180D.MID": "tb_6m",
    "TB.CDN.1Y.MID": "tb_1y",
    "AVG.INTWO": "corra",
}

FRED_FILES = {"DGS10.csv": "ust_10y", "DEXCAUS.csv": "usdcad", "DCOILWTICO.csv": "wti"}
YAHOO_FILES = {"XIU.TO.csv": "xiu", "SPY.csv": "spy", "GLD.csv": "gld"}

FFILL_LIMIT = 3
FFILL_EXCEPTIONS = {"wti": 5}   # FRED oil has 4-5 day gaps in 2011 and 2015
OUT = PROCESSED / "risk_factors.csv"

def load_boc(path, columns):
    """Read a BoC Valet CSV; return the renamed columns in `columns` only."""
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    marker = lines.index('"OBSERVATIONS"')
    df = pd.read_csv(path, skiprows=marker + 1, index_col='date', encoding='utf-8-sig', parse_dates=True)
    return df[list(columns)].rename(columns=columns)

def load_fred(path, name):
    """Read a FRED CSV; return one column called `name`."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    old = path.stem
    df = df.rename(columns={old : name})
    return df[[name]]

def load_yahoo(path, name):
    """Read a Yahoo CSV; return Adj Close as one column called `name`."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    old = "Adj Close"
    df = df.rename(columns={old : name})
    return df[[name]]

def summarize(df:pd.DataFrame):
    """Print each column's dtype, NaN count, and first and last valid dates."""
    tables = pd.DataFrame({
        "dtype" : df.dtypes,
        "nans" : df.isna().sum(),
        "first" : [df[c].first_valid_index().date() for c in df.columns],
        "last" : [df[c].last_valid_index().date() for c in df.columns],
    })
    # print(tables, "\n")

def build_table(frames:list):
    """Join frames, forward-fill, keep TSX days in the common sample; fail on leftover Nans"""
    df = pd.concat(frames, axis=1, sort=True).sort_index()
    start = max(df[c].first_valid_index() for c in df.columns)
    end = min(df[c].last_valid_index() for c in df.columns)
    mask = (df.index >= start) & (df.index <= end) & (~df['xiu'].isna())
    calendar = df.index[mask]
    count = df.loc[calendar].isna().sum()
    print(count)
    df = pd.DataFrame({c : df[c].ffill(limit=FFILL_EXCEPTIONS.get(c, FFILL_LIMIT)) for c in df.columns}).loc[calendar]
    if df.isna().any().any():
        bad = list(df.columns[df.isna().any()])
        raise ValueError(f"NaNs remain after forward-fill in: {bad}")
    return df

def main():
    frames = [
        load_boc(BOC / "bond_yields_benchmark.csv", BOC_BENCHMARK),
        load_boc(BOC / "CL.CDN.MOST.1DL,AVG.INTWO,TB.CDN.30D.MID,TB.CDN.60D.MID,TB.CDN.90D.MID,TB.CDN.180D.MID,TB.CDN.1Y.MID.csv", BOC_TBILLS),
    ]
    for filename, name in FRED_FILES.items():
        frames.append(load_fred(FRED / filename, name))
    for filename, name in YAHOO_FILES.items():
        frames.append(load_yahoo(YAHOO / filename, name))
    for df in frames:
        summarize(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df = build_table(frames)
    print(f"{df.shape[0]} rows, {df.shape[1]} columns, {df.index.min().date()} to {df.index.max().date()}")
    df.to_csv(OUT)


if __name__ == "__main__":
    main()
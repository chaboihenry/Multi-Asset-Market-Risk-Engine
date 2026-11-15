"""
Daily returns of a constant-maturity 10y GoC bond: each day's par bond repriced on the next day's bootstrapped curve.
Reads data/processed/goc_discount_factors.csv and risk_factors.csv (coupon = goc_10y), labels each return with day t+1.
Saves data/processed/goc_10y_returns.csv.
Expected: 5,506 returns, daily std ≈ 0.43%, implied duration ≈ 8.9, largest moves on known rate shocks (2008, 2022, 2023).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.paths import PROCESSED

import numpy as np
import pandas as pd

from engine.pricing import bond_return

GRID = np.arange(0.25, 10.01, 0.25)
MATURITY = 10


def load_inputs():
    """
    Load the GoC discount-factor grid and the risk-factor table (both date-indexed).
    Returns (dfs, factors).
    """
    df1 = pd.read_csv(PROCESSED / 'goc_discount_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    return df1, df2


def check_input(dfs, factors):
    """
    Raise ValueError unless both tables have exactly the same dates.
    """
    if not dfs.index.equals(factors.index):
        raise ValueError("discount factor and risk factors don't have the same dates")


def daily_bond_returns(dfs, factors):
    """
    Daily returns of the constant-maturity 10y GoC bond: day t's par bond repriced on day t+1's curve.
    Returns a Series indexed by day t+1 (the day the return is earned).
    """
    dates1 = dfs.index
    dates2 = dfs[1:].index.copy()
    rets, date = [], []
    for today, tomorrow in zip(dates1, dates2):
        coupon = factors.loc[today]['goc_10y'] / 100
        next_dfs = dfs.loc[tomorrow]
        ret = bond_return(coupon, MATURITY, GRID, next_dfs)
        rets.append(ret)
        date.append(tomorrow)
    return pd.Series(rets, index=date, name='goc_10y_ret')


def check(returns, factors):
    """
    Print a sanity report: summary statistics, the five largest absolute returns with dates, and the implied duration.
    Implied duration = median of -return / Δgoc_10y (decimal); expect about 8.5-9 for a 10y par bond.
    """
    print(returns.describe())
    print('='*40)
    largest_moves = returns.abs().nlargest(n=5)
    print(largest_moves, returns.loc[largest_moves.index])
    print('='*40)
    y_change = factors['goc_10y'].diff() / 100
    duration = -returns / y_change
    duration = duration.replace(to_replace=[np.inf, -np.inf], value=np.nan)
    print(duration.median())


def main():
    """
    Load and check the inputs, compute daily 10y GoC bond returns, print the sanity report.
    Saves the return series to data/processed/goc_10y_returns.csv.
    """
    dfs, factors = load_inputs()
    check_input(dfs, factors)
    rets = daily_bond_returns(dfs, factors)
    check(rets, factors)
    rets.index.name = 'date'
    rets.to_csv(PROCESSED / 'goc_10y_returns.csv')


if __name__ == "__main__":
    main()
"""
Run the P&L engine on the full sample: daily CAD P&L per position and in total, 2004-11-19 to 2026-10-27.
Reads risk_factors.csv and goc_10y_returns.csv; portfolio, notional and hedge ratio come from common/portfolio.py.
Saves the breakdown and the total to data/processed/ and prints summary checks.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.paths import PROCESSED
from common.portfolio import PORTFOLIO, TOTAL_VALUE, HEDGE_RATIO
from engine.portfolio import portfolio_pnl, min_variance_hedge, asset_returns

import pandas as pd


def load_inputs():
    """
    Load the risk factors table and 10y bond returns, both indexed by date.
    Returns (factors DataFrame, bond_return Series named 'goc_10y_ret')
    """
    df1 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'goc_10y_returns.csv', index_col=0, parse_dates=True)
    series = df2['goc_10y_ret']
    return (df1, series)


def main():
    """
    Load the inputs, run the P&L engine with the portfolio settings, 
    print checks and save both outputs. 
    """
    factors, bond_returns = load_inputs()
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, TOTAL_VALUE, HEDGE_RATIO)
    pnl.index.name = 'date'
    pnl.to_csv(PROCESSED / 'pnl_breakdown_portfolio.csv')
    total.name = 'pnl_total'
    total.index.name = 'date'
    total.to_csv(PROCESSED / 'total_pnl_portfolio.csv')
    print(pnl.shape)
    print('='*40)
    print(pnl.columns)
    print('='*40)
    print('Total P&L breakdown')
    print(total.describe())
    rets = asset_returns(factors, bond_returns)
    asset_ret, fx_ret = rets['spy'], rets['usdcad']
    hedge = min_variance_hedge(asset_ret, fx_ret)   
    print(hedge)


if __name__ == "__main__":
    main()












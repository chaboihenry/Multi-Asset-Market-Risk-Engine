"""
Buy-and-hold portfolio rebalanced to target weights at each CPP fiscal quarter-end (March, June, September, December).
Builds CAD prices (bond index with carry), simulates unit holdings, and reports the wealth path and weight drift.
Reads risk_factors.csv and goc_10y_returns.csv; saves rebalanced_values.csv and rebalanced_weights.csv to data/processed/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from common.paths import PROCESSED, TABLES
from common.portfolio import PORTFOLIO, TOTAL_VALUE
from engine.rebalance import cad_prices, rebalance_dates, simulate_holdings, holdings_values, holdings_var_es
from engine.backtest import summary_row

WINDOW = 500

def load_inputs():
    """Load the risk factors (DataFrame) and the 10y bond returns (Series named 'goc_10y_ret'), indexed by date."""
    df1 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'goc_10y_returns.csv', index_col=0, parse_dates=True)
    series = df2['goc_10y_ret']
    return df1, series


def main():
    """Build prices, rebalance dates and holdings; print the wealth and weight summaries; save both tables."""
    factors, goc_10y = load_inputs()
    cad_price = cad_prices(factors, goc_10y)
    rebalance = rebalance_dates(cad_price.index)
    units = simulate_holdings(cad_price, PORTFOLIO, TOTAL_VALUE, rebalance)
    value, total, weights = holdings_values(units, cad_price)
    holdings = holdings_var_es(cad_price, units, WINDOW)
    print(cad_price.iloc[-1])
    print('='*40)
    print(len(rebalance), rebalance[0], rebalance[-1])
    print('='*40)
    print('total first day', total.iloc[0], 'total last day', total.iloc[-1])
    print('='*40)
    print(weights.describe())
    print('='*40)
    print(weights.idxmax(), weights.idxmin())
    print('='*40)
    print(value.loc['04-20-2020', 'wti'])
    print('='*40)
    print(holdings.describe())
    print('='*40)
    print(holdings.iloc[0], holdings.iloc[-1])
    value['total'] = total
    value.index.name = 'date'
    weights.index.name = 'date'
    holdings.index.name = 'date'
    value.to_csv(PROCESSED / 'rebalanced_values.csv')
    weights.to_csv(PROCESSED / 'rebalanced_weights.csv')
    holdings.to_csv(PROCESSED / 'rebalanced_var.csv')

    df = pd.read_csv(PROCESSED / 'var_forecasts.csv', index_col=0, parse_dates=True)
    constant = summary_row(df['pnl'], df['hs_var'])
    constant['mean_var_pct'] = (df['hs_var'].mean()) / TOTAL_VALUE
    constant['max_var_pct'] = (df['hs_var'].max()) / TOTAL_VALUE
    rebalanced = summary_row(total.diff().loc[holdings.index], holdings['var'])
    rebalanced['mean_var_pct'] = holdings['var_pct'].mean()
    rebalanced['max_var_pct'] = holdings['var_pct'].max()
    out = pd.DataFrame.from_dict({'constant weights' : constant, 'rebalanced quarterly' : rebalanced}, orient='index')
    out.index.name = 'portfolio'
    out.to_csv(TABLES / 'rebalanced_vs_constant.csv')

if __name__ == "__main__": 
    main()
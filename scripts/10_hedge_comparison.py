"""
Compare portfolio risk under four FX hedge ratios: unhedged, the full-sample minimum-variance ratio (0.37),
fully hedged, and a rolling minimum-variance ratio estimated from the previous 250 days (capped to 0-1).
For each setting: daily P&L volatility, worst day, 99% VaR and 97.5% ES, all on the dates where the rolling ratio exists.
Reads risk_factors.csv and goc_10y_returns.csv; saves hedge_comparison.csv to results/tables/.
"""
import sys 
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from common.paths import PROCESSED, TABLES
from common.portfolio import PORTFOLIO, TOTAL_VALUE
from engine.portfolio import asset_returns, portfolio_pnl, min_variance_hedge, rolling_min_variance_hedge
from engine.var import empirical_var_es

HEDGE_SETTINGS = {'Unhedged (h = 0)': 0.0, 'Min-variance (h = 0.37)': 0.37, 'Fully hedged (h = 1)': 1.0}
WINDOW = 250


def load_inputs():
    """Load the risk factors and the 10y bond returns, both indexed by date."""
    df1 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'goc_10y_returns.csv', index_col=0, parse_dates=True)
    return df1, df2


def risk_row(total_pnl):
    """Risk summary of one P&L series: daily std, worst day, 99% VaR and 97.5% ES (full sample - window (days), positive loss amounts)."""
    var, es = empirical_var_es(total_pnl, var_level=0.99, es_level=0.975)
    return {
        'daily_std' : total_pnl.std(),
        'worst_day' : total_pnl.min(),
        'var_99' : var,
        'es_975' : es
    }


def main():
    """Run the P&L engine once per hedge setting, summarise each, print the table and save it."""
    factors, bond_returns = load_inputs()
    asset_ret = asset_returns(factors, bond_returns)
    roll_h = rolling_min_variance_hedge(asset_ret['spy'], asset_ret['usdcad'], WINDOW)
    hedge = dict(HEDGE_SETTINGS)
    hedge['Rolling h* (250d)'] = roll_h
    dates = roll_h.dropna().index
    out = {}
    for name, h in hedge.items():
        _, pnl = portfolio_pnl(factors, bond_returns, PORTFOLIO, TOTAL_VALUE, h)
        pnl = pnl.loc[dates]
        out[name] = risk_row(pnl)

    out = pd.DataFrame.from_dict(out, orient='index')
    out.index.name = 'hedge_setting'
    out.to_csv(TABLES / 'hedge_comparison.csv')


if __name__ == "__main__":
    main()


"""
Historical stress tests: the CAD price moves of four crisis episodes (peak to trough) applied to today's
C$10M portfolio at target weights, so the episodes are directly comparable.
Reads risk_factors.csv and goc_10y_returns.csv; saves stress_historical.csv to results/tables/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from common.paths import PROCESSED, TABLES
from common.portfolio import PORTFOLIO, TOTAL_VALUE
from engine.portfolio import position_values
from engine.rebalance import cad_prices
from engine.stress import episode_returns, episode_pnl, shock_to_cad_returns


EPISODES = {
    '2008 financial crisis': ('2007-10-09', '2009-03-09'),
    '2014-16 oil crash': ('2014-06-20', '2016-02-11'),
    '2020 COVID crash': ('2020-02-19', '2020-03-23'),
    '2022 rate shock': ('2022-01-04', '2022-10-12'),
}


SHOCKS = {
    'Stagflation': {'spy': -0.20, 'xiu': -0.20, 'gld': 0.0, 'wti': 0.50, 'usdcad': 0.0, 'yield_bp': 200},
    'CAD rally in a crash': {'spy': -0.25, 'xiu': 0.0, 'gld': 0.0, 'wti': 0.0, 'usdcad': -0.10, 'yield_bp': 0},
    'Oil shock': {'spy': 0.0, 'xiu': 0.0, 'gld': 0.0, 'wti': -0.60, 'usdcad': 0.10, 'yield_bp': 0},
}


def load_inputs():
    """Load the risk factors (DataFrame) and the 10y bond returns (Series), indexed by date."""
    df1 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'goc_10y_returns.csv', index_col=0, parse_dates=True)
    series = df2['goc_10y_ret']
    return df1, series


def main():
    """Build CAD prices and position values once, run each episode, print and save the P&L table."""
    factors, bond_returns = load_inputs()
    cad_price = cad_prices(factors, bond_returns)
    pos_values = position_values(PORTFOLIO, TOTAL_VALUE)
    out = {}
    for name, date in EPISODES.items():
        episode = episode_returns(cad_price, date[0], date[-1])
        pnl = episode_pnl(episode, pos_values)
        out[name] = pnl
    out = pd.DataFrame.from_dict(out, orient='index')
    out['total'] = out.sum(axis=1)
    out['total_pct'] = out['total'] / TOTAL_VALUE
    out.index.name = 'episode'
    out.to_csv(TABLES / 'stress_historical.csv')

    # hypothetical shocks
    base_yield = factors['goc_10y'].iloc[-1] / 100
    out2 = {}
    for name2, shock in SHOCKS.items():
        result = shock_to_cad_returns(shock, base_yield)
        pnl2 = episode_pnl(result, pos_values)
        out2[name2] = pnl2
    out2 = pd.DataFrame.from_dict(out2, orient='index')
    out2['total'] = out2.sum(axis=1)
    out2['total_pct'] = out2['total'] / TOTAL_VALUE
    out2.index.name = 'scenario'
    out2.to_csv(TABLES / 'stress_hypothetical.csv')

if __name__ == "__main__":
    main()
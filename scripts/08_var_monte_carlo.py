"""
Daily 1-day VaR (99%) and ES (97.5%) from a Monte Carlo simulation of six risk factors (multivariate Student-t).
Reads risk_factors.csv, goc_10y_returns.csv and pnl_breakdown_portfolio.csv; portfolio settings from common/portfolio.py.
Adds mc_var and mc_es columns to var_forecasts.csv.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.paths import PROCESSED
from common.portfolio import PORTFOLIO, TOTAL_VALUE, HEDGE_RATIO
from engine.portfolio import asset_returns, position_values
from engine.montecarlo import factor_table, monte_carlo_var_es

import pandas as pd

WINDOW = 500
N_SIMS = 10_000
DF = 4
SEED = 42


def load_inputs():
    """Load the risk factors, bond returns and P&L breakdown, all indexed by date."""
    df1 = pd.read_csv(PROCESSED / 'risk_factors.csv', index_col=0, parse_dates=True)
    df2 = pd.read_csv(PROCESSED / 'goc_10y_returns.csv', index_col=0, parse_dates=True)
    df3 = pd.read_csv(PROCESSED / 'pnl_breakdown_portfolio.csv', index_col=0, parse_dates=True)
    return df1, df2, df3


def main():
    """Build the factor table, run the rolling Monte Carlo, add its columns to the forecast table and save."""
    factors, bond_returns, pnl_breakdown = load_inputs()
    rets = asset_returns(factors, bond_returns)
    pos_values = position_values(PORTFOLIO, TOTAL_VALUE)
    oil_value = pos_values['wti']
    fac_table = factor_table(rets, pnl_breakdown, oil_value)
    forecasts = monte_carlo_var_es(fac_table, pos_values, PORTFOLIO, HEDGE_RATIO, WINDOW, N_SIMS, DF, SEED, var_level=0.99, es_level=0.975)
    forecasts = forecasts.rename(columns={'var' : 'mc_var', 'es' : 'mc_es'})
    df = pd.read_csv(PROCESSED / 'var_forecasts.csv', index_col=0, parse_dates=True)
    df['mc_var'] = forecasts['mc_var']
    df['mc_es'] = forecasts['mc_es']
    df.to_csv(PROCESSED / 'var_forecasts.csv')
    print(df.describe())
    print('='*40)
    print(df.shape)


if __name__ == "__main__":
    main()
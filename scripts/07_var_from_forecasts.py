"""
Daily 1-day VaR (99%) and ES (97.5%) forecasts from three models: historical simulation, normal with a rolling
volatility, and normal with EWMA volatility. Each forecast uses only P&L up to the previous day.
Reads total_pnl_portfolio.csv; saves var_forecasts.csv to data/processed/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from common.paths import PROCESSED
from engine.var import historical_var_es, rolling_sigma, ewma_sigma, normal_var_es, student_t_var_es

WINDOW = 500
DF = 4

def load_pnl():
    """Load the total daily P&L as a Series indexed by date."""
    df = pd.read_csv(PROCESSED / 'total_pnl_portfolio.csv', index_col=0, parse_dates=True)
    return df['pnl_total']


def build_forecasts(pnl, window):
    """Run the four models and return one table: the realised P&L plus a VaR and an ES column per model.
    Columns: pnl, hs_var, hs_es, norm_var, norm_es, ewma_var, ewma_es, ewma_t_var, ewma_t_es; one row per forecast date."""
    hs_df = historical_var_es(pnl, window)
    sigma = rolling_sigma(pnl, window)
    norm_var, norm_es = normal_var_es(sigma)
    ewma_sig = ewma_sigma(pnl, window, lam=0.94)
    ewma_var, ewma_es= normal_var_es(ewma_sig)
    ewma_t_var, ewma_t_es = student_t_var_es(ewma_sig, DF)
    return pd.DataFrame({
        'pnl' : pnl,
        'hs_var' : hs_df['var'],
        'hs_es' : hs_df['es'], 
        'norm_var' : norm_var, 
        'norm_es' : norm_es,
        'ewma_var' : ewma_var,
        'ewma_es' : ewma_es,
        'ewma_t_var' : ewma_t_var,
        'ewma_t_es' : ewma_t_es
    }, index=hs_df.index)


def main():
    """Load the P&L, build the forecasts, print a summary and save the table."""
    pnl = load_pnl()
    df = build_forecasts(pnl, WINDOW)
    print(df.shape)
    print('='*40)
    print(df.describe())
    df.index.name = 'date'
    if WINDOW == 250:
        df.to_csv(PROCESSED / 'var_forecasts250.csv')
    else:
        df.to_csv(PROCESSED / 'var_forecasts.csv')


if __name__=="__main__":
    main()


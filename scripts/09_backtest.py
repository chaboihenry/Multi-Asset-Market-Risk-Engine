"""
Backtest the four 99% VaR models over the full forecast sample: breach counts, Kupiec and Christoffersen tests,
and Basel traffic-light zones by calendar year.
Reads var_forecasts.csv; saves backtest_summary.csv and breaches_by_year.csv to results/tables/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from common.paths import PROCESSED, TABLES
from engine.backtest import breaches, kupiec_test, christoffersen_test, basel_zone, summary_row

WINDOW = 500
MODELS = {'hs_var': 'Historical', 'norm_var': 'Normal, rolling', 'ewma_var': 'Normal, EWMA', 
            'mc_var': 'Monte Carlo (t)', 'ewma_t_var' : 'Student-t, EWMA'}
CRISIS = [2008, 2015, 2020, 2022]

def load_forecasts():
    """Load the forecast table (realised P&L plus one VaR and ES column per model), indexed by date."""
    if WINDOW == 250:
        df = pd.read_csv(PROCESSED / 'var_forecasts250.csv', index_col=0, parse_dates=True)
    else:
        df = pd.read_csv(PROCESSED / 'var_forecasts.csv', index_col=0, parse_dates=True)
    return df


def yearly_breaches(pnl, var):
    """Number of breaches in each calendar year for one model, as a Series indexed by year."""
    bre = breaches(pnl, var)
    return bre.groupby(bre.index.year).sum()


def crisis_share(yearly, crisis_years):
    """Share of each model's breaches that fall in the crisis years.
    Takes the breaches-by-year table; returns one row per model: breaches in crisis years, total breaches, share."""
    cr = yearly.loc[crisis_years]
    cr_sum = cr.sum()
    yr_sum = yearly.sum()
    ratio = cr_sum / yr_sum
    return pd.DataFrame({
        'crisis_breaches' : cr_sum,
        'total_breaches' : yr_sum,
        'share_of_total_from_crisis' : ratio
    })


def main():
    """Run the backtests for every model, print both tables and save them."""
    var_forecasts = load_forecasts()
    pnl = var_forecasts['pnl']
    summary = {}
    yr_count = {}
    for model, name in MODELS.items():
        var = var_forecasts[model]
        model_summary = summary_row(pnl, var)
        year = yearly_breaches(pnl, var)
        zones = year.apply(basel_zone)
        for i in ['green', 'yellow', 'red']:
            model_summary[i] = (zones == i).sum()
        summary[name] = model_summary
        yr_count[name] = year

    summary = pd.DataFrame.from_dict(summary, orient='index')
    yr_count = pd.DataFrame(yr_count)
    summary.index.name = 'model'
    yr_count.index.name = 'year'
    if WINDOW == 250:
        summary.to_csv(TABLES / 'backtest_summary250.csv')
        yr_count.to_csv(TABLES / 'breaches_by_year250.csv')
    else:
        summary.to_csv(TABLES / 'backtest_summary.csv')
        yr_count.to_csv(TABLES / 'breaches_by_year.csv')
    crisis_table = crisis_share(yr_count, CRISIS)
    crisis_table.to_csv(TABLES / 'crisis_breaches.csv')


if __name__ == "__main__":
    main()
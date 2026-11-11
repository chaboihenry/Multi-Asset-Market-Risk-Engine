"""
Compare the bootstrapped GoC zero curve with the Bank of Canada's published zero curve.
Both converted to continuously compounded zero rates; gaps reported in basis points.
Saves results/tables/curve_vs_boc.csv and two figures in results/figures/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import PROCESSED, BOC, TABLES, FIGURES

GRID = np.arange(0.25, 10.01, 0.25)
BOC_COLS = [f"ZC{int(round(t * 100)):03d}YR" for t in GRID]   # ZC025YR ... ZC1000YR, matching GRID
PLOT_DATES = ["2008-10-10", "2020-04-20", "2026-01-05"]        # pick dates both files have


def load_my_curve():
    """My discount factors -> continuous zero rates (decimals), columns = GRID."""
    df = pd.read_csv(PROCESSED / 'goc_discount_factors.csv', index_col=0, parse_dates=True)
    df = -np.log(df) / GRID
    df.columns = GRID
    return df


def load_boc_curve():
    """BoC zero curve (already continuous, decimals), only the GRID maturities, no empty days."""
    df = pd.read_csv(BOC / 'yield_curves.csv', skipinitialspace=True, na_values="na", index_col=0, parse_dates=True)
    df = df[BOC_COLS].dropna(how='all')
    df.columns = GRID
    return df


def gap_table(mine, boc):
    """Mean gap, mean absolute gap and largest absolute gap (bp) per maturity, on shared dates."""
    shared = mine.index.intersection(boc.index)
    mine = mine.loc[shared]
    boc = boc.loc[shared]
    gap = (mine - boc) * 10000
    return pd.DataFrame({
        "mean_bp" : gap.mean(),
        "mean_abs_bp" : gap.abs().mean(),
        "max_abs_bp" : gap.abs().max()
    })


def worst_day_table(mine, boc):
    """The biggest deviations in my bootstrapped yield curve vs BoC yield curve"""
    mine = load_my_curve()
    boc = load_boc_curve()

    shared = mine.index.intersection(boc.index)
    mine = mine.loc[shared]
    boc = boc.loc[shared]
    gap = (mine - boc) * 10000

    gap2 = gap[2.0]
    mask = (gap2.index > pd.to_datetime('2025-01-01')) & (gap2.index < pd.to_datetime('2026-01-01'))
    gap2 = gap2[mask]
    gap2.abs().nlargest(5) # 2025-02-20, 2025-08-14
    feb = pd.to_datetime('2025-02-20')
    aug = pd.to_datetime('2025-08-14')
    feb_gap = gap2.loc[feb - pd.Timedelta(days=5):feb + pd.Timedelta(days=5)]
    aug_gap = gap2.loc[aug - pd.Timedelta(days=5):aug + pd.Timedelta(days=5)]

    risk_factors = pd.read_csv(PROCESSED / 'risk_factors.csv', parse_dates=True, index_col=0)

    mine_feb = risk_factors[['tb_6m', 'tb_1y', 'goc_2y']].loc[feb_gap.index]
    boc_feb = boc[[0.50, 1.00, 2.00]].loc[feb_gap.index] * 100
    feb = pd.concat([mine_feb, boc_feb], axis=1)
    mine_aug = risk_factors[['tb_6m', 'tb_1y', 'goc_2y']].loc[aug_gap.index]
    boc_aug = boc[[0.50, 1.00, 2.00]].loc[aug_gap.index] * 100
    aug = pd.concat([mine_aug, boc_aug], axis=1)
    full = pd.concat([feb, aug], axis=0)
    full = full.rename(columns=
                {'tb_6m' : 'tb_6m (mine)',
                'tb_1y' : 'tb_1y (mine)', 
                'goc_2y' : 'goc_2y (mine)',
                0.5 : 'BoC 0.5yr zero rate', 
                1.0 : 'BoC 1.0yr zero rate', 
                2.0 : 'BoC 2.0yr zero rate'})
    full = full[['tb_6m (mine)', 'BoC 0.5yr zero rate', 'tb_1y (mine)', 'BoC 1.0yr zero rate', 'goc_2y (mine)', 'BoC 2.0yr zero rate']]
    full.to_csv(TABLES / 'worst_differences.csv')


def plot_curves(mine, boc):
    """Both curves on the same axes for each date in PLOT_DATES."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,6))
    for date, ax in zip(PLOT_DATES, (ax1, ax2, ax3)):
        ax.plot(mine.loc[date].index, mine.loc[date] * 100, label='My Curve', color='red')
        ax.plot(boc.loc[date].index, boc.loc[date] * 100, label='Boc Curve', color='blue', linestyle='dashed')
        ax.legend()
        ax.set_xlabel('Time to Maturity (years)')
        ax.set_ylabel('Zero rates (%)')
        ax.set_title(f"Curve comparison for {date}")
    
    fig.tight_layout()
    fig.savefig(FIGURES/ "Comparsion_of_curves.png")
    plt.close(fig)


def plot_gap_history(mine, boc):
    """Gap (bp) over time at 2, 5 and 10 years."""
    shared = mine.index.intersection(boc.index)
    mine = mine.loc[shared]
    boc = boc.loc[shared]
    gap = (mine - boc) * 10000
    fig, ax = plt.subplots(figsize=(12,6))
    for maturity in [2.00, 5.00, 10.00]:
        ax.plot(shared, gap[maturity], label=f'{maturity} Maturity (years)')

    ax.set_title('Comparsion of Gap Curve (Mine - BoC)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Gap (bp)')
    ax.legend()
    ax.axhline()
    fig.tight_layout()
    fig.savefig(FIGURES / 'gap_curve_comparison.png')
    plt.close(fig)


def main():
    mine, boc = load_my_curve(), load_boc_curve()
    # keep only dates in both; call gap_table, print it, save it; make both plots
    df = gap_table(mine, boc)
    df.to_csv(TABLES / 'gap_table.csv')
    plot_curves(mine, boc)
    plot_gap_history(mine, boc)
    worst_day_table(mine, boc)


if __name__ == "__main__":
    main()
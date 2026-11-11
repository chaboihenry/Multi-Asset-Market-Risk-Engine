"""
Bootstrap a GoC semi-annual zero curve for every TSX day from T-bills and benchmark par yields.
Saves discount factors on a 0.25-10y grid to data/processed/goc_discount_factors.csv.
Expected: 5,507 rows x 40 columns; every par bond reprices to 100 within 1e-8.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import PROCESSED
from engine.curve import bootstrap_curve, interp_zero, discount_factor, bond_price

TBILL_COLS = ["tb_1m", "tb_2m", "tb_3m", "tb_6m", "tb_1y"]
TBILL_DAYS = [30, 60, 90, 180, 365]
PAR_COLS = ["goc_2y", "goc_3y", "goc_5y", "goc_7y", "goc_10y"]
PAR_MATURITIES = [2, 3, 5, 7, 10]
GRID = np.arange(0.25, 10.01, 0.25)             # 40 maturities in years
OUT = PROCESSED / "goc_discount_factors.csv"


def curve_for_day(row):
    """Bootstrap one day; return (known_t, known_z)."""
    tbills = row[TBILL_COLS].to_numpy()
    pars = row[PAR_COLS].to_numpy()
    return bootstrap_curve(TBILL_DAYS, tbills, PAR_MATURITIES, pars)


def worst_reprice_error(row, known_t, known_z):
    """Largest |price - 100| across that day's five par bonds."""
    pars = row[PAR_COLS].to_numpy()
    curve = lambda t: interp_zero(t, known_t, known_z)
    gaps = [
        abs(bond_price(y_pct / 100, maturity, curve) - 100)
            for maturity, y_pct in zip(PAR_MATURITIES, pars)   
    ]
    return max(gaps)


def build_all(factors):
    """Discount factors on GRID for every date; also returns the worst repricing error."""
    rows, dates = [], []
    worst = 0.0

    for date, row in factors.iterrows():
        known_t, known_z = curve_for_day(row)
        z_grid = interp_zero(GRID, known_t, known_z)
        d_grid = discount_factor(z_grid, GRID)

        rows.append(d_grid)
        dates.append(date)
        worst = max(worst, worst_reprice_error(row, known_t, known_z))

    columns = [f"df_{t:.2f}y" for t in GRID]
    table = pd.DataFrame(rows, index=dates, columns=columns)
    table.index.name = 'date'
    return table, worst

def main():
    factors = pd.read_csv(PROCESSED / "risk_factors.csv", index_col=0, parse_dates=True)
    dfs, worst = build_all(factors)
    print(f"{dfs.shape[0]} days x {dfs.shape[1]} maturities; worst par repricing error {worst:.1e}")
    dfs.to_csv(OUT)


if __name__ == "__main__":
    main()
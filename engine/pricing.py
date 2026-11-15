"""
Bond pricing and P&L on the bootstrapped GoC curve.
Pure functions, no file I/O. Rates are decimals, times in years, prices per 100 face value.
Curves arrive as discount factors on a fixed maturity grid and are converted to semi-annual zero rates.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.curve import bond_price, interp_zero, zero_rate

import numpy as np


def curve_from_dfs(grid_t, dfs):
    """
    Curve function t → semi-annual zero rate, built from one day's grid discount factors.
    grid_t: grid maturities (years); dfs: discount factors at those maturities. 
    """
    dfs = np.asarray(dfs)
    grid_t = np.asarray(grid_t)
    zero_rates = zero_rate(dfs, grid_t)
    return lambda t: interp_zero(t, grid_t, zero_rates)


def bond_return(coupon, maturity, grid_t, next_dfs):
    """
    One-day return of a par bond bought on day t (coupon = day t's par yield, decimal), repriced on day t+1's curve.
    grid_t, next_dfs: day t+1's grid maturities (years) and discount factors. Returns price/100 - 1 (negative when rates rise).
    """
    tmrw_curve = curve_from_dfs(grid_t, next_dfs)
    price = bond_price(coupon, maturity, tmrw_curve)
    return (price / 100) - 1
    













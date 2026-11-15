"""
Tests for engine/pricing.py: curve_from_dfs and bond_return on flat curves.
A 10y par bond at 4%: unchanged curve → 0; +1% → about -7.79%; -1% → about +8.58%.
"""
import pytest
import numpy as np

from engine.curve import (bond_price, discount_factor)
from engine.pricing import (curve_from_dfs, bond_return)

COUPON = 0.04
MATURITY = 10
BASE_RATE = 0.04
UP_RATE = 0.05
DOWN_RATE = 0.03
GRID = np.arange(0.25, 10.01, 0.25)             # 40 maturities in years


def flat_dfs(rate):
    """
    Discount factors on GRID for a curve flat at rate (semi-annual).
    """
    return discount_factor(rate, GRID)


def test_curve_from_dfs_flat_rate_everywhere():
    """Flat discount factors give the same rate on and between grid points."""
    tmp = curve_from_dfs(GRID, flat_dfs(BASE_RATE))
    assert tmp(2.0) == pytest.approx(BASE_RATE, abs=1e-12)
    assert tmp(3.6) == pytest.approx(BASE_RATE, abs=1e-12)


def test_curve_from_dfs_round_trips_grid_rates():
    """Grid zero rates survive the discount-factor round trip."""
    rates = np.linspace(0.02, 0.04, num=40)
    dfs = discount_factor(rates, GRID)
    tmp = curve_from_dfs(GRID, dfs)
    assert tmp(GRID) == pytest.approx(rates, abs=1e-12)


def test_bond_return_zero_when_curve_unchanged():
    """A par bond repriced on the same flat curve has zero return."""
    assert bond_return(COUPON, MATURITY, GRID, flat_dfs(BASE_RATE)) == pytest.approx(0, abs=1e-12)


def test_bond_return_loses_when_rates_rise():
    """A 1% rise in rates cuts a 10y par bond's value by about 7.8%."""
    expected = bond_price(COUPON, MATURITY, lambda t: UP_RATE + 0 * t) / 100 - 1
    assert bond_return(COUPON, MATURITY, GRID, flat_dfs(UP_RATE)) == pytest.approx(expected, abs=1e-12)


def test_bond_return_convexity():
    """A 1% fall in rates gains more than a 1% rise loses (convexity)."""
    up_return = bond_return(COUPON, MATURITY, GRID, flat_dfs(UP_RATE))
    down_return = bond_return(COUPON, MATURITY, GRID, flat_dfs(DOWN_RATE))
    assert up_return < 0
    assert down_return > 0
    assert abs(up_return) < abs(down_return)



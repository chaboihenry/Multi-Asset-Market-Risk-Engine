"""
Tests for engine/curve.py: T-bill discount factors, zero-rate conversions, interpolation, bond pricing.
Check values: a 90-day bill quoted at 3.00% has D = 0.9926571 and z = 0.030114.
"""
import pytest
import numpy as np

from engine.curve import (tbill_discount_factor, 
                        zero_rate, discount_factor, 
                        interp_zero, bond_price, bootstrap_curve)


def flat(rate):
    """A flat zero curve: the same rate at every maturity (works on arrays)."""
    return lambda t: rate + 0 * t


def test_tbill_discount_factor_90_day():
    """A 90-day bill quoted at 3.00% has discount factor 0.9926571."""
    assert tbill_discount_factor(3.00, 90) == pytest.approx(0.9926571, abs=1e-6)


def test_zero_rate_from_tbill():
    """That discount factor at t = 90/365 implies a semi-annual zero rate of 0.030114."""
    assert zero_rate(0.9926571, 90 / 365) == pytest.approx(0.030114, abs=1e-6)


def test_zero_rate_discount_factor_round_trip():
    """Converting a zero rate to a discount factor and back returns the original rate."""
    z, t = 0.030114, 90 / 365
    assert zero_rate(discount_factor(z, t), t) == pytest.approx(z, abs=1e-12)


def test_interp_zero_inside_range():
    """Halfway between two known points gives the average rate."""
    assert interp_zero(1.5, [1, 2], [0.02, 0.03]) == pytest.approx(0.025, abs=1e-12)


def test_interp_zero_flat_below_first_point():
    """Below the first known point, the first rate is held flat."""
    assert interp_zero(0.5, [1, 2], [0.02, 0.03]) == pytest.approx(0.02, abs=1e-12)


def test_interp_zero_flat_above_last_point():
    """Above the last known point, the last rate is held flat."""
    assert interp_zero(3.0, [1, 2], [0.02, 0.03]) == pytest.approx(0.03, abs=1e-12)


@pytest.mark.parametrize("maturity", [0.5, 2, 5, 10])
def test_bond_price_par_on_flat_curve(maturity):
    """A bond whose coupon equals a flat curve's rate prices at exactly 100."""
    assert bond_price(0.04, maturity, flat(0.04)) == pytest.approx(100, abs=1e-9)


def test_bond_price_above_par_when_coupon_exceeds_rate():
    """A coupon above the curve's rate is worth more than par."""
    assert bond_price(0.05, 5, flat(0.04)) > 100


def test_bond_price_zero_coupon_equals_discounted_face():
    """With no coupon, the price is just 100 discounted from maturity."""
    assert bond_price(0.0, 3, flat(0.04)) == pytest.approx(100 * discount_factor(0.04, 3), abs=1e-9)


def test_bond_price_counts_twenty_cash_flows_for_ten_years():
    """At a 0% rate nothing is discounted, so the price is 100 + 20 coupons of 1."""
    assert bond_price(0.02, 10, flat(0.0)) == pytest.approx(120, abs=1e-9)


TBILL_DAYS = [30, 60, 90, 180, 365]
PAR_MATURITIES = [2, 3, 5, 7, 10]
TBILL_YIELDS = [3.0, 3.1, 3.2, 3.3, 3.5]
PAR_YIELDS = [3.6, 3.7, 3.9, 4.0, 4.2]


def test_bootstrap_par_bonds_reprice_to_100():
    """Every input par bond prices at 100 on the bootstrapped curve."""
    known_t, known_z = bootstrap_curve(TBILL_DAYS, TBILL_YIELDS, PAR_MATURITIES, PAR_YIELDS)
    curve = lambda t: interp_zero(t, known_t, known_z)
    for maturity, y_pct in zip(PAR_MATURITIES, PAR_YIELDS):
        assert bond_price(y_pct / 100, maturity, curve) == pytest.approx(100, abs=1e-8)


def test_bootstrap_tbill_points_match_quotes():
    """The first points are the T-bill quotes converted to semi-annual zero rates."""
    known_t, known_z = bootstrap_curve(TBILL_DAYS, TBILL_YIELDS, PAR_MATURITIES, PAR_YIELDS)
    for i, (days, y_pct) in enumerate(zip(TBILL_DAYS, TBILL_YIELDS)):
        assert known_t[i] == pytest.approx(days / 365)
        assert known_z[i] == pytest.approx(zero_rate(tbill_discount_factor(y_pct, days), days / 365), abs=1e-12)


def test_bootstrap_flat_inputs_give_flat_bond_zeros():
    """With every input at 4%, the bond zero rates are all about 4%."""
    _, known_z = bootstrap_curve(TBILL_DAYS, [4.0] * 5, PAR_MATURITIES, [4.0] * 5)
    assert known_z[len(TBILL_DAYS):] == pytest.approx(np.full(len(PAR_MATURITIES), 0.04), abs=1e-4)


def test_bootstrap_maturities_sorted():
    """Returned maturities increase, as interp_zero requires."""
    known_t, _ = bootstrap_curve(TBILL_DAYS, TBILL_YIELDS, PAR_MATURITIES, PAR_YIELDS)
    assert np.all(np.diff(known_t) > 0)

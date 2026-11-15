"""
Tests for engine/portfolio.py: the daily CAD P&L breakdown and total for the constant-weight portfolio.
Uses a four-day hand-made factor table with round numbers; every expected value is computed by hand.
Covers the oil identity, the total, full FX hedging, CAD-only columns, dates, and the negative oil price.
"""

from common.portfolio import PORTFOLIO
from engine.portfolio import portfolio_pnl, min_variance_hedge

import pytest
import pandas as pd

NOTIONAL = 10_000_000
DATES = pd.date_range(start='01/01/2021', periods=4, freq='D')

def fake_factors():
    """Four-day hand-made factor table (xiu, spy, gld, usdcad, wti) with prices easy to check by hand.
    Indexed by a DatetimeIndex like the real risk_factors.csv."""
    return pd.DataFrame({
        'usdcad' : [1.25, 1.25, 1.00, 1.25], 
        'wti' : [40, 50, 50, 80], 
        'spy' : [100, 110, 110, 121],
        'xiu' : [20 , 20, 21, 21], 
        'gld' : [200, 190, 190, 209]
    }, index=DATES)


def fake_bond_returns(dates):
    """Hand-made 10y bond returns named 'goc_10y_ret', on every date except the first.
    Mirrors goc_10y_returns.csv, which has no return on day one."""
    return pd.Series([0.01, -0.02, 0.00], index=dates[1:], name='goc_10y_ret')


def test_oil_identity():
    """wti_asset + wti_fx equals yesterday's barrels times the change in CAD oil price, every day.
    Expected oil P&L is computed by hand from the fake prices, not from the engine."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=0)
    oil_pnl = pnl['wti_asset'] + pnl['wti_fx']
    assert oil_pnl.to_list() == pytest.approx([50_000, -40_000, 200_000])


def test_total_is_row_sum():
    """The total P&L equals the sum of every breakdown column on each day."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=0)
    assert total.to_list() == pytest.approx([750_000, -1_480_000, 2_937_500])
    pd.testing.assert_series_equal(total, pnl.sum(axis=1))


def test_full_hedge_cancels_fx():
    """With hedge = 1, each USD position's fx and hedge columns sum to zero every day."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=1)
    for i in ['spy', 'gld', 'wti']:
        tmp = pnl[f'{i}_hedge'] + pnl[f'{i}_fx']
        assert tmp.to_list() == pytest.approx([0, 0, 0], abs=1e-6)
    assert total.to_list() == pytest.approx([750_000, 20_000, 1_062_500])


def test_cad_assets_have_no_fx_columns():
    """CAD positions (xiu, goc_10y_ret) get only an _asset column; no _fx, _cross or _hedge."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=0)
    for i in ['xiu', 'goc_10y_ret']:
        assert f'{i}_asset' in pnl.columns
        for suf in ['fx', 'cross', 'hedge']:
            assert f'{i}_{suf}' not in pnl.columns


def test_dates_match_bond_returns():
    """The breakdown has exactly the bond-return dates: no first-day row of NaN."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=0)
    assert pnl.index.equals(bond_returns.index)
    assert not pnl.isna().any().any()


def test_negative_oil_carries_barrels():
    """A day with a negative oil price keeps the previous day's barrels instead of resetting them.
    The P&L on the day after the negative price uses those carried barrels."""
    factors = fake_factors()
    bond_returns = fake_bond_returns(DATES)
    factors.loc[DATES[2], 'wti'] = -10
    pnl, total = portfolio_pnl(factors, bond_returns, PORTFOLIO, NOTIONAL, hedge=0)
    assert (pnl['wti_asset'] + pnl['wti_fx']).to_list() == pytest.approx([50_000, -232_000, 352_000])


def test_min_variance_hedge():
    """h* on hand-made returns with known answers: 
    perfect natural hedge, no relationship, and same direction."""
    FX = pd.Series([0.02, -0.02, 0.04, -0.04])
    asset = -0.5 * FX
    assert min_variance_hedge(asset, FX) == pytest.approx(0.5, abs=1e-6)
    FX = pd.Series([1, 1, -1, -1])
    asset = pd.Series([1, -1, 1, -1])
    assert min_variance_hedge(asset, FX) == pytest.approx(1.0, abs=1e-6)
    FX = pd.Series([0.02, -0.02, 0.05, 0.04])
    asset = FX
    assert min_variance_hedge(asset, FX) == pytest.approx(2.0, abs=1e-6)

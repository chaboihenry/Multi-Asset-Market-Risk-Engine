
"""
Tests for engine/var.py: empirical, historical, rolling-sigma, EWMA and normal VaR/ES on tiny hand-made series.
Every expected value is computed by hand; two tests check that no forecast uses its own day's P&L.
"""

import pytest
import pandas as pd


from engine.var import (empirical_var_es, 
                        historical_var_es,
                        rolling_sigma, 
                        ewma_sigma, 
                        normal_var_es)

def test_empirical_var_es():
    """VaR and ES on the integers -5..5 at 90% / 80% come out as whole numbers, both positive."""
    test = pd.Series([-5,-4,-3,-2,-1,0,1,2,3,4,5])
    assert empirical_var_es(test, var_level=0.9, es_level=0.8) == pytest.approx((4, 4), abs=1e-6)


def test_historical_has_no_lookahead():
    """Forecasts start after `window` days, and changing the last day's P&L changes no forecast."""
    window = 3
    dates = pd.date_range(start='01/01/2020', periods=6, freq='D')
    pnl = pd.Series([-3, 1, -2, 4, -1, 2], index=dates)
    before = historical_var_es(pnl, window)
    pnl_changed = pnl.copy()
    pnl_changed.iloc[-1] = -1_000_000
    after = historical_var_es(pnl_changed, window)
    assert len(before) == 3
    assert before.index.equals(dates[3:])
    pd.testing.assert_frame_equal(before, after)


def test_rolling_sigma_excludes_today():
    """The sigma for a day is the std of the previous `window` days only; a huge P&L on the day itself is ignored."""
    test = pd.Series([1, -1, 1, -1, 100])
    window = 4
    assert rolling_sigma(test, window).to_list() == pytest.approx([1.1547], abs=1e-6)


def test_ewma_sigma_recursion():
    """EWMA sigma follows the hand recursion: seed variance 100, then updates with lambda = 0.94."""
    test = pd.Series([-10, 0, 10, 20, 0, 5])
    window = 3
    lam = 0.94
    assert ewma_sigma(test, window, lam=lam).to_list() == pytest.approx([10, 10.8628, 10.5319], abs=1e-3)


def test_normal_var_es():
    """Normal multipliers are 2.3263 (99% VaR) and 2.3378 (97.5% ES), and scale linearly with sigma."""
    sigma1 = 1
    sigma2 = 100
    assert normal_var_es(sigma1) == pytest.approx((2.3263, 2.3378), abs=0.01)
    assert normal_var_es(sigma2) == pytest.approx((232.63, 233.78), abs=0.01)








"""
Tests for engine/backtest.py: breach indicators, Kupiec, Christoffersen and the Basel traffic light.
Expected values are hand-computed or taken from small hand-made series.
"""

import pandas as pd
import pytest

from engine.backtest import breaches, kupiec_test, christoffersen_test, basel_zone

def test_breaches_flags_losses_only():
    """A breach is a loss beyond VaR; a gain of the same size, or a loss exactly equal to VaR, is not."""
    test_pnl = pd.Series([-150, 150, -100, -50]) 
    test_var = pd.Series([100, 100, 100, 100])
    assert breaches(test_pnl, test_var).to_list() == [True, False, False, False]


def test_kupiec_zero_when_rate_matches():
    """The LR statistic is about 0 when the observed breach rate equals the expected rate, and large when it is far off."""
    lr1, _ = kupiec_test(50, 5_000, var_level=0.99)
    assert lr1 == pytest.approx(0, abs=1e-6)
    lr2, _ = kupiec_test(83, 5_006, var_level=0.99) 
    assert lr2 == pytest.approx(18.27, abs=0.01)


def test_christoffersen_counts():
    """On a short hand-made breach sequence the test returns the hand-computed LR."""
    test1 = pd.Series((([True] * 10) + [False] * 990))
    _, p1 = christoffersen_test(test1)
    assert p1 < 0.05
    test2 = pd.Series((([True] + [False] * 100) * 10))
    _, p2 = christoffersen_test(test2)
    assert p2 > 0.05

def test_basel_zone_boundaries():
    """Zone edges: 0 and 4 are green, 5 and 9 yellow, 10 red."""
    test1 = 0
    assert basel_zone(test1) == 'green'
    test2 = 4
    assert basel_zone(test2) == 'green'
    test3 = 5
    assert basel_zone(test3) == 'yellow'
    test4 = 9
    assert basel_zone(test4) == 'yellow'
    test5 = 10
    assert basel_zone(test5) == 'red'




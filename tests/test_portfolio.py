"""
Tests for common/portfolio.py: the portfolio definition is internally consistent.
Weights sum to 1, every currency is 'usd' or 'cad', and the hedge ratio is between 0 and 1.
"""
from common.portfolio import PORTFOLIO, HEDGE_RATIO

import pytest


def test_weights_sum_to_one():
    """All position weights add up to 100% of the portfolio"""
    total = 0
    for i in PORTFOLIO.values():
        total += i['weight']
    assert total == pytest.approx(1.0, abs=1e-12)

def test_currencies_are_usd_or_cad():
    """Every position is priced in USD or CAD"""
    need = ['usd', 'cad']
    for i in PORTFOLIO.values():
        assert i['currency'] in need


def test_hedge_ratio_between_zero_and_one():
    """The default FX hedge ratio is a fraction from 0 (unhedged) to 1 (fully hedged)"""
    assert HEDGE_RATIO >= 0 and HEDGE_RATIO <= 1.00 















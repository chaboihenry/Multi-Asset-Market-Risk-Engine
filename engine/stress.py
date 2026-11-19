"""
Stress tests: apply the price moves of a historical episode, or a hypothetical shock, to the portfolio at target weights.
Pure functions, no file I/O.
"""

import pandas as pd

from engine.curve import bond_price

def episode_returns(prices, start, end):
    """Change in each position's CAD price over an episode: end price / start price - 1.
    Takes the CAD price table and two dates; returns one value per position."""
    return (prices.loc[end] / prices.loc[start]) - 1


def episode_pnl(returns, values):
    """CAD P&L of each position over an episode: position value x the episode's price change.
    Takes the output of episode_returns and the position values; returns one value per position."""
    val = pd.Series(values)
    return returns * val


def shock_to_cad_returns(shock, base_yield):
    """CAD price change of each position under a hypothetical shock stated in market terms (USD moves, USD/CAD, yield change in bp).
    The bond is repriced in full: a 10y par bond at base_yield revalued on a flat curve at base_yield + the shock."""
    spy = (1 + shock['spy']) * (1 + shock['usdcad']) - 1
    gld = (1 + shock['gld']) * (1 + shock['usdcad']) - 1
    wti = (1 + shock['wti']) * (1 + shock['usdcad']) - 1
    xiu = shock['xiu']
    shock_yield = base_yield + (shock['yield_bp'] / 10_000)
    new_price = bond_price(base_yield, 10, lambda t: shock_yield)
    goc_10y_ret = (new_price / 100) - 1
    return pd.Series([spy, gld, wti, xiu, goc_10y_ret], index=['spy', 'gld', 'wti', 'xiu', 'goc_10y_ret'])




















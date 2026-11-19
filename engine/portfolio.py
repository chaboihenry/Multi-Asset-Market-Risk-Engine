"""
Portfolio P&L in CAD for a constant-weight portfolio: daily asset returns, position values, oil barrels.
Breaks each position's P&L into asset, FX, cross and hedge components; the total is their sum.
Pure functions, no file I/O: the portfolio, notional and hedge ratio are passed in as arguments.
"""

import numpy as np
import pandas as pd

def asset_returns(factors, bond_returns):
    """Daily % returns of XIU, SPY, GLD and USD/CAD, joined with the bond returns (labeled day t+1).
    The first day drops out: no % change, and no bond return on it."""
    factors = factors.drop(columns=['wti'])
    factors = factors[['xiu', 'spy', 'gld', 'usdcad']]
    factors = factors.pct_change()
    rets = factors.join(bond_returns, how='inner')
    return rets


def position_values(portfolio, notional):
    """CAD value of each position: weight x notional. Returns {position name: CAD value}."""
    out = {}
    for asset, info in portfolio.items():
        value = info['weight'] * notional
        out[asset] = value
    return out


def oil_barrels(oil_price, usd_cad, oil_cad):
    """Barrels of oil held at the end of each day: (oil's CAD value ÷ USD/CAD) ÷ oil price.
    On days the price is ≤ 0, the previous day's barrels are carried forward."""
    barrels = (oil_cad / usd_cad) / oil_price
    barrels[oil_price <= 0] = np.nan
    barrels = barrels.ffill()
    return barrels


def pnl_breakdown(rets, values, barrels, factors, portfolio, hedge):
    """Daily CAD P&L per position, split into asset, FX, cross and hedge columns (e.g. spy_asset, spy_fx).
    USD positions get FX, cross and hedge columns; CAD positions only asset; oil uses barrels x price changes."""
    fx_ret = rets['usdcad']
    out = {}
    for asset, info in portfolio.items():
        if asset != 'wti': 
            v = values[asset]
            r = rets[asset]
            out[f'{asset}_asset'] = v * r
            if info['currency'] == 'usd':
                out[f'{asset}_fx'] = v * fx_ret
                out[f'{asset}_cross'] = v * r * fx_ret
                out[f'{asset}_hedge'] = -hedge * v * fx_ret
        else:
            oil_cad = factors['wti'] * factors['usdcad']
            oil_cad = oil_cad.diff()
            oil_pnl = oil_cad * barrels.shift(1)
            v = values['wti']
            out[f'{asset}_fx'] = v * fx_ret
            out[f'{asset}_hedge'] = -hedge * v * fx_ret
            out[f'{asset}_asset'] = oil_pnl - (v * fx_ret)
    return pd.DataFrame(out, index=rets.index)


def portfolio_pnl(factors, bond_returns, portfolio, notional, hedge):
    """Run the full P&L pipeline: returns, position values, oil barrels, then the per-position breakdown.
    Returns (breakdown table, total daily P&L Series)."""
    rets = asset_returns(factors, bond_returns)
    values = position_values(portfolio, notional)
    barrels = oil_barrels(factors['wti'], factors['usdcad'], values['wti'])
    pnl = pnl_breakdown(rets, values, barrels, factors, portfolio, hedge)
    total = pnl.sum(axis=1, skipna=True)
    return (pnl, total)


def min_variance_hedge(asset_ret, fx_ret):
    """
    Minimum-variance FX hedge ratio h* = 1 + corr(asset, fx) * std(asset) / std(fx).
    Takes two aligned return Series; returns one number (0 = unhedged, 1 = fully hedged).
    """
    corr = asset_ret.corr(fx_ret)
    return 1 + corr * (asset_ret.std() / fx_ret.std())


def rolling_min_variance_hedge(asset_ret, fx_ret, window):
    """Minimum-variance hedge ratio for each day from the previous `window` days only, capped to the range 0 to 1.
    Returns a Series on the same dates; days without a full window of history are NaN."""
    out = []
    dates = []
    for i in range(window, len(asset_ret)):
        asset = asset_ret.iloc[i-window:i]
        fx = fx_ret.iloc[i-window:i]
        rol = min_variance_hedge(asset, fx)
        out.append(rol)
        date = asset_ret.index[i]
        dates.append(date)

    out = pd.Series(out, index=dates)
    out = out.clip(lower=0, upper=1)
    out = out.reindex(asset_ret.index)
    return out


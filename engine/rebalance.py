"""
Buy-and-hold portfolio with quarterly rebalancing: CAD prices per position, unit holdings that drift between
rebalance dates, the resulting wealth path and weights, and VaR/ES on the actual holdings.
Pure functions, no file I/O.
"""

import pandas as pd

from engine.portfolio import position_values
from engine.var import empirical_var_es

def cad_prices(factors, bond_returns):
    """CAD price per unit for the five positions: spy, gld and wti converted with usdcad, xiu as quoted.
    The bond is an index starting at 1 that compounds the daily 10y price return plus coupon carry."""
    fx = factors['usdcad']
    spy = factors['spy'] * fx
    gld = factors['gld'] * fx
    wti = factors['wti'] * fx
    xiu = factors['xiu']
    cdays = factors.index.to_series().diff().dt.days
    carry = (factors['goc_10y'].shift(1) / 100) * (cdays / 365)
    total = bond_returns + carry 
    total = total.dropna()
    compound = (1 + total).cumprod()
    compound = compound.reindex(factors.index)
    compound = compound.fillna(1)
    return pd.DataFrame({
        'spy' : spy,
        'goc_10y_ret' : compound,
        'xiu' : xiu,
        'gld' : gld, 
        'wti' : wti
    })


def rebalance_dates(index):
    """Last trading day of each fiscal quarter (ends of March, June, September, December) found in `index`.
    Returns a DatetimeIndex of rebalance dates.
    Note, sample that ends partway through March, June, September or December would be treated as quarter-end"""
    serie = index.to_series()
    quart = serie.groupby(index.to_period('Q')).max()
    quart = pd.DatetimeIndex(quart)
    return quart[quart.month.isin([3, 6, 9, 12])]


def simulate_holdings(prices, portfolio, notional, rebal_dates):
    """Units held of each position on every day: bought at target weights on the first day, fixed between
    rebalance dates, and reset to target weights (at that day's prices and total value) on each rebalance date."""
    dollars = pd.Series(position_values(portfolio, notional))
    units = dollars / prices.iloc[0]
    out = {}
    for date in prices.index:
        if date in rebal_dates:
            total = (units * prices.loc[date]).sum()
            dollars_wanted = pd.Series(position_values(portfolio, total))
            units = dollars_wanted / prices.loc[date]
        out[date] = units
    return pd.DataFrame.from_dict(out, orient='index')


def holdings_values(units, prices):
    """Dollar value of each position every day (units x price), the total portfolio value, and each position's weight.
    Returns (values DataFrame, total Series, weights DataFrame)."""
    value = units * prices
    total = value.sum(axis=1)
    weights = value.div(total, axis=0)
    return value, total, weights


def holdings_var_es(prices, units, window, var_level=0.99, es_level=0.975):
    """Daily VaR and ES of the actual holdings: the previous `window` days of market moves applied to the
    holdings at the previous close. Returns columns 'var', 'es' (dollars) and 'var_pct', 'es_pct' (share of value)."""
    var_list = []
    es_list = []
    var_pct_list = []
    es_pct_list = []
    dates = []
    value, total, _ = holdings_values(units, prices)
    values_ex_oil = value.drop(columns='wti')
    barrels = units['wti']
    returns = prices.drop(columns='wti').pct_change()
    oil_changes = prices['wti'].diff()
    for i in range(window + 1, len(prices)):
        held_values = values_ex_oil.iloc[i-1]
        held_barrels = barrels.iloc[i-1]
        held_total = total.iloc[i-1]
        past_returns = returns.iloc[i - window:i]
        past_oil_changes = oil_changes.iloc[i - window:i]
        hypo_pnl = (past_returns * held_values).sum(axis=1) + (past_oil_changes * held_barrels)
        var, es = empirical_var_es(hypo_pnl, var_level=var_level, es_level=es_level)
        var_pct = var / held_total
        es_pct = es / held_total
        var_list.append(var)
        es_list.append(es)
        var_pct_list.append(var_pct)
        es_pct_list.append(es_pct)
        date = prices.index[i]
        dates.append(date)

    return pd.DataFrame({
        'var' : var_list,
        'es' : es_list,
        'var_pct' : var_pct_list,
        'es_pct' : es_pct_list
    }, index=dates)




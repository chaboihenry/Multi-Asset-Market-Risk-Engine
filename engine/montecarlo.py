"""
Monte Carlo VaR and ES: simulate the six risk factors jointly from a multivariate Student-t and reprice the portfolio.
The covariance for each day comes from the previous `window` days only; VaR and ES are read off the simulated P&Ls.
Pure functions, no file I/O.
"""

import pandas as pd

from engine.var import empirical_var_es
from scipy.stats import multivariate_t


def factor_table(rets, breakdown, oil_value):
    """Six risk factors on the P&L dates: returns of spy, xiu, gld, usdcad and goc_10y_ret, plus oil's CAD position return.
    Oil's return is its total daily P&L (wti_asset + wti_fx) divided by the oil position value."""
    oil_ret = (breakdown['wti_asset'] + breakdown['wti_fx']) / oil_value
    oil_ret.name = 'wti'
    return pd.concat([rets, oil_ret], axis=1)


def simulate_factors(history, n_sims, df, seed):
    """Draw n_sims joint scenarios for the factors from a zero-mean multivariate Student-t with `df` degrees of freedom.
    The scenarios' covariance matches that of `history` (a window of past factor rows); returns one column per factor."""
    cov_matrix = history.cov()
    cov_shape = cov_matrix * (df - 2)/df
    draws = multivariate_t.rvs(
        loc = [0] * len(history.columns),
        shape=cov_shape,
        df=df, 
        size=n_sims,
        random_state=seed
    )
    out = pd.DataFrame(draws, columns=history.columns)
    return out 


def scenario_pnl(scenarios, values, portfolio, hedge):
    """CAD P&L of each simulated scenario: position value x factor return, plus FX and cross terms for USD assets.
    Oil's return is already in CAD, so it gets no FX or cross term, only the hedge. Returns one P&L per scenario."""
    total = 0
    fx = scenarios['usdcad']
    for asset, info in portfolio.items():
        v = values[asset]
        r = scenarios[asset]
        if info['currency'] == 'cad':
            total += v * r
        elif info['currency'] == 'usd' and asset != 'wti':
            total += v * (r + fx + r * fx) - (hedge * v * fx)
        else:
            total += v * r - (hedge * v * fx)
    return total


def monte_carlo_var_es(factors, values, portfolio, hedge, window, n_sims, df, seed, var_level=0.99, es_level=0.975):
    """Rolling Monte Carlo VaR and ES: each day simulates from the previous `window` days of factors and reprices the portfolio.
    Returns a DataFrame with columns 'var' and 'es', indexed by the forecast date."""
    var_list = []
    es_list = []
    dates = []
    for i in range(window, len(factors)):
        scenarios = simulate_factors(factors.iloc[i - window: i], n_sims, df, seed)
        sim_pnl = scenario_pnl(scenarios, values, portfolio, hedge)
        var, es = empirical_var_es(sim_pnl, var_level=var_level, es_level=es_level)
        var_list.append(var)
        es_list.append(es)
        date = factors.index[i]
        dates.append(date)
    return pd.DataFrame({
        'var' : var_list,
        'es' : es_list
    }, index=dates)








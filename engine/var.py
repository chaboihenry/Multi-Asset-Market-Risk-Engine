"""
VaR and ES estimators for a daily P&L series: historical simulation and parametric (normal), rolling through time.
Every forecast for day t uses only data up to day t-1. VaR and ES are returned as positive loss amounts.
Pure functions, no file I/O.
"""

import pandas as pd
import numpy as np
from scipy.stats import norm


def empirical_var_es(pnl_sample, var_level=0.99, es_level=0.975):
    """
    VaR and ES read directly off a sample of P&Ls, both returned as positive loss amounts.
    VaR is the loss at the (1 - var_level) quantile; 
    ES is the average loss at or beyond the (1 - es_level) quantile.
    """
    var = pnl_sample.quantile(round(1-var_level, 10))
    indices = (pnl_sample <= pnl_sample.quantile(round(1-es_level, 10)))
    es = pnl_sample[indices].mean()
    return -var, -es


def historical_var_es(pnl, window, var_level=0.99, es_level=0.975):
    """Rolling historical-simulation VaR and ES: each day's forecast is empirical_var_es on the previous `window` days.
    Returns a DataFrame with columns 'var' and 'es', indexed by the forecast date."""
    var_list = []
    es_list = []
    dates = []
    for i in range(window, len(pnl)):
        var, es = empirical_var_es(pnl.iloc[i - window:i], var_level=var_level, es_level=es_level)
        var_list.append(var)
        es_list.append(es)
        date = pnl.index[i]
        dates.append(date)
    return pd.DataFrame({
        'var' : var_list,
        'es' : es_list, 
    }, index=dates)


def rolling_sigma(pnl, window):
    """Standard deviation of P&L over the previous `window` days, 
    lined up so day t uses data up to t-1."""
    std_list = []
    dates = []
    for i in range(window, len(pnl)):
        std = pnl.iloc[i - window : i].std()
        std_list.append(std)
        date = pnl.index[i]
        dates.append(date)
    return pd.Series(std_list, index=dates, name='std_pnl')


def ewma_sigma(pnl, window, lam=0.94):
    """EWMA volatility (RiskMetrics): variance = lam * previous variance + (1 - lam) * previous day's squared P&L.
    Seeded with the variance of the first `window` days; day t uses data up to t-1; 
    assumes zero mean."""
    std_list = []
    dates = []
    seed = pnl.iloc[0:window].var()
    for i in range(window, len(pnl)):
        sigma = np.sqrt(seed)
        std_list.append(sigma)
        date = pnl.index[i]
        dates.append(date)
        seed = lam * seed + (1 - lam) * (pnl.iloc[i] ** 2)
    return pd.Series(std_list, index=dates, name='ewma_std')


def normal_var_es(sigma, var_level=0.99, es_level=0.975):
    """Parametric VaR and ES for a zero-mean normal P&L with volatility `sigma` (a number or a Series).
    VaR = z * sigma; ES = sigma * pdf(z_es) / (1 - es_level). Returns (var, es)."""
    var_multiplier = norm.ppf(var_level)
    es_multiplier = norm.pdf(norm.ppf(es_level)) / (1 - es_level)
    return sigma * var_multiplier, sigma * es_multiplier

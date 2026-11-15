"""
Backtests for VaR forecasts: breach indicators, the Kupiec frequency test, the Christoffersen independence test
and the Basel traffic light. Pure functions, no file I/O.
"""

import numpy as np
from scipy.stats import chi2

def breaches(pnl, var):
    """True on each day where the loss exceeded the VaR forecast (P&L below -VaR), False otherwise.
    Takes two aligned Series; returns a boolean Series on the same dates."""
    return pnl < -var


def kupiec_test(n_breaches, n_days, var_level=0.99):
    """Kupiec proportion-of-failures test: is the breach count consistent with the expected rate (1 - var_level)?
    Returns (LR statistic, p-value); the statistic is chi-squared with 1 degree of freedom under a correct model."""
    p = 1 - var_level
    p_ = n_breaches / n_days
    lr = -2 * (((n_days - n_breaches) * np.log(1-p)) + (n_breaches * np.log(p))
                - ((n_days - n_breaches) * np.log(1 - p_)) - (n_breaches * np.log(p_)))
    return lr, chi2.sf(lr, 1)


def christoffersen_test(breach):
    """Christoffersen independence test: is a breach more likely on the day after a breach than after a quiet day?
    Takes a boolean breach Series; returns (LR statistic, p-value), chi-squared with 1 degree of freedom."""
    today = breach[1:].to_numpy()
    yesterday = breach[:-1].to_numpy()

    n00 = ((yesterday == False) & (today == False)).sum()
    n01 = ((yesterday == False) & (today == True)).sum()
    n10 = ((yesterday == True) & (today == False)).sum()
    n11 = ((today == True) * (yesterday == True)).sum()

    p01 = n01 / (n00 + n01)
    p11 = n11 / (n10 + n11)
    p = (n01 + n11) / (n00 + n01 + n10 + n11)
    
    l0 = ((n00 + n10) * np.log(1-p)) + ((n01 + n11) * np.log(p))
    l1 = (n00 * np.log(1 - p01)) + (n01 * np.log(p01)) + (n10 * np.log(1-p11)) + (n11 * np.log(p11))

    lr = -2 * (l0 - l1)
    return lr, chi2.sf(lr, 1)












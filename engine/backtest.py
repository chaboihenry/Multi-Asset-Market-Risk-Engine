"""
Backtests for VaR forecasts: breach indicators, the Kupiec frequency test, the Christoffersen independence test
and the Basel traffic light. Pure functions, no file I/O.
"""

from scipy.stats import chi2
from scipy.special import xlogy

def breaches(pnl, var):
    """True on each day where the loss exceeded the VaR forecast (P&L below -VaR), False otherwise.
    Takes two aligned Series; returns a boolean Series on the same dates."""
    return pnl < -var


def kupiec_test(n_breaches, n_days, var_level=0.99):
    """Kupiec proportion-of-failures test: is the breach count consistent with the expected rate (1 - var_level)?
    Returns (LR statistic, p-value); the statistic is chi-squared with 1 degree of freedom under a correct model."""
    p = 1 - var_level
    p_ = n_breaches / n_days
    lr = -2 * ((xlogy((n_days - n_breaches), 1 - p)) + (xlogy(n_breaches, p))
                - (xlogy(n_days - n_breaches, 1 - p_)) - (xlogy(n_breaches, p_)))
    return lr, chi2.sf(lr, 1)


def christoffersen_test(breach):
    """Christoffersen independence test: is a breach more likely on the day after a breach than after a quiet day?
    Takes a boolean breach Series; returns (LR statistic, p-value), chi-squared with 1 degree of freedom."""
    today = breach[1:].to_numpy()
    yesterday = breach[:-1].to_numpy()

    n00 = ((~yesterday) & (~today)).sum()
    n01 = ((~yesterday) & (today)).sum()
    n10 = ((yesterday) & (~today)).sum()
    n11 = ((yesterday) & (today)).sum()

    p01 = n01 / (n00 + n01)
    p11 = n11 / (n10 + n11)
    p = (n01 + n11) / (n00 + n01 + n10 + n11)
    
    l0 = (xlogy(n00 + n10, 1 - p)) + (xlogy(n01 + n11, p))
    l1 = (xlogy(n00, 1 - p01)) + (xlogy(n01, p01)) + (xlogy(n10, 1 - p11)) + (xlogy(n11, p11))

    lr = -2 * (l0 - l1)
    return lr, chi2.sf(lr, 1)


def basel_zone(n_breaches):
    """Basel traffic-light zone for a 250-day backtest of 99% VaR: 
    'green' (0-4), 'yellow' (5-9) or 'red' (10+)."""
    if n_breaches >= 0 and n_breaches <= 4:
        return 'green'
    elif n_breaches >= 5 and n_breaches <= 9:
        return 'yellow'
    else:
        return 'red'


def summary_row(pnl, var):
    """Backtest one model: breaches, breach rate, Kupiec LR and p-value, Christoffersen LR and p-value.
    Returns a dict with one entry per statistic."""
    out = {}
    bre = breaches(pnl, var)
    out['breaches'] = bre.sum()
    out['rate'] = bre.sum() / len(bre)
    kupiec_lr, kupiec_p = kupiec_test(bre.sum(), len(bre), var_level=0.99)
    out['kupiec_lr'] = kupiec_lr
    out['kupiec_p'] = kupiec_p
    christ_lr, christ_p = christoffersen_test(bre)
    out['christ_lr'] = christ_lr
    out['christ_p'] = christ_p
    return out




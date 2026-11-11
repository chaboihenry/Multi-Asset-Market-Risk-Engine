"""
Zero-curve building blocks: T-bill discount factors and semi-annual zero rates.
Pure functions, no file I/O. Rates inside engine/ are decimals (0.03 = 3%), times in years.
"""
import numpy as np
from scipy.optimize import brentq


def tbill_discount_factor(yield_pct, days):
    """Discount factor of a T-bill quoted as a simple yield on a 365-day year."""
    y = yield_pct / 100
    return 1 / (1 + y * (days/365))


def zero_rate(df, t):
    """Semi-annual zero rate (decimal) implied by discount factor `df` at time `t` (years)."""
    return 2 * (df **(-1/(2*t)) - 1)


def discount_factor(z, t):
    """Discount factor at time `t` (years) for a semi-annual zero rate `z` (decimal)."""
    return (1+z/2)**(-2*t)


def interp_zero(t, known_t, known_z):
    """Zero rate at t: linear between known points, flat outside them. known_t must be sorted ascending."""
    return np.interp(t, known_t, known_z)


def bond_price(coupon, maturity, zero_fn):
    """Price per 100 face of a semi-annual bond (decimal coupon; maturity a multiple of 0.5 years)."""
    times = np.linspace(0.5, maturity, int(maturity*2))
    amounts = np.full(len(times), 100*coupon/2)
    amounts[-1] += 100
    fac = discount_factor(zero_fn(times), times)
    return np.sum(fac * amounts)


def bootstrap_curve(tbill_days, tbill_yield_pct, par_maturities, par_yield_pct):
    """
    Bootstrap one day's semi-annual zero curve from T-bill quotes and par yields (both in percent).
    Returns (known_t, known_z): maturities in years and zero rates (decimals), sorted by maturity.
    """
    tbill_days = np.asarray(tbill_days, dtype=float)
    t_bills = tbill_days / 365
    d_bills = tbill_discount_factor(np.asarray(tbill_yield_pct), tbill_days)
    z_bills = zero_rate(d_bills, t_bills)

    known_t = list(t_bills)
    known_z = list(z_bills)

    for T, y_pct in zip(par_maturities, par_yield_pct):
        coupon = y_pct / 100

        def objective(z_guess):
            curve = lambda t: interp_zero(t, known_t + [T], known_z + [z_guess])
            return bond_price(coupon, T, curve) - 100

        z_T = brentq(objective, -0.05, 0.25)
        known_t.append(T)
        known_z.append(z_T)

    return np.array(known_t), np.array(known_z)





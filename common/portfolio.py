"""
Portfolio definition: notional, weights, currencies, default FX hedge ratio. Constants only.
"""

TOTAL_VALUE = 10_000_000
HEDGE_RATIO = 0             # Default ratio, 0 = unhedged & 1 = fully hedged

PORTFOLIO = {
    'spy' : {'weight' : 0.70, 'currency' : 'usd'},
    'goc_10y_ret' : {'weight' : 0.15, 'currency' : 'cad'},
    'xiu' : {'weight' : 0.10, 'currency' : 'cad'}, 
    'gld' : {'weight' : 0.03, 'currency' : 'usd'}, 
    'wti' : {'weight' : 0.02, 'currency' : 'usd'}
}


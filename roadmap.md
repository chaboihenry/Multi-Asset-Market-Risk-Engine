# Risk Engine — Roadmap

**Goal:** a CAD-based risk engine for a six-asset portfolio. Compare historical, parametric and Monte Carlo VaR/ES, backtest them over ~20 years, and stress-test the portfolio.

**Portfolio:** XIU (TSX 60), SPY, 10y GoC bond (own curve), 10y US Treasury, GLD, WTI oil. USD/CAD enters as a risk factor.
**Measures:** 1-day 99% VaR (backtested), 97.5% ES. Optional 10-day horizon for Monte Carlo paths.

## Phase 0 — Setup and data

- [ ] Repo structure, conda env, CLAUDE.md
- [ ] BoC and FRED files in `data/raw/` (done)
- [ ] Yahoo downloads (XIU, SPY, GLD); inventory complete

## Phase 1 — Clean and align

- [ ] One daily table of risk factors, CAD base
- [X] Holiday mismatch: **Option C** (TSX/BoC calendar; forward-fill US data on Canada-only days; US-only days drop out). Costs: ~104 zero-return days for US assets, ~116 two-day returns.
- [X] Forward-fill limit: 3 days; exception `wti` = 5 (FRED oil gaps of 4–5 days in 2011 and 2015)
- [X] Built `data/processed/risk_factors.csv`: 5,507 TSX days × 18 columns, 2004-11-18 to 2026-10-27, no NaNs
- [X] Oil: keep WTI spot; model with **absolute $ changes** (position in barrels). Rule: relative returns for XIU, SPY, GLD, USD/CAD; absolute changes for rates (bp) and oil.
  Limitation: absolute changes ignore price level, so over long windows they overweight high-price periods (2008, 2022) and underweight low-price ones (2016, 2020). Also spot WTI is not directly investable.
- [X] CAD short rate: none in VaR; assume zero expected 1-day return. Use CORRA if a cash rate is needed later.

- Filled values per column (Option C cost): CAD rates 27, SPY/GLD 104, UST 10y 119, USD/CAD 126, WTI 242

## Phase 2 — Zero curve

- [ ] Bootstrap GoC zero curve from T-bills + benchmark par yields
- [ ] Test: every input bond reprices to par
- [ ] Compare against the BoC published curve

## Phase 3 — Pricing and P&L

- [ ] Price the GoC and US bonds daily
- [ ] Decide: fixed bond that ages, or constant 10y maturity
- [ ] Daily portfolio P&L in CAD; split USD assets into asset move vs FX move

## Phase 4 — VaR and ES

- [ ] Historical simulation
- [ ] Parametric (normal; then a fat-tailed or EWMA variant)
- [ ] Monte Carlo
- [ ] Decide: estimation window length

## Phase 5 — Backtesting

- [ ] Write predictions **before** running (see below)
- [ ] Kupiec (breach frequency), Christoffersen (clustering), Basel traffic light
- [ ] Calm vs crisis periods; where the models disagree most

## Phase 6 — Stress tests

- [ ] Historical: 2008, 2015 oil crash, 2020 COVID, 2022 rate shock
- [ ] Hypothetical shocks
- [ ] Extension: propagate shocks through a causal graph

## Phase 7 — Write-up

- [ ] README results, journal posts

## Predictions (write before Phase 5)

- ---

## Deviations log

Record any change of plan here: date, what changed, why.

- 2026-11-04: USD/CAD from FRED (`DEXCAUS`), not BoC; BoC's daily series only starts 2017.
- 2026-11-04: Gold from Yahoo (`GLD`); FRED no longer carries LBMA gold.
- 2026-11-04: Forward-fill exception for `wti` (limit 5 vs 3) after finding 4–5 day gaps in FRED oil (2011-04 to 2011-07, 2015-01).
- 2026-11-04: Oil modeled with absolute changes because of the negative price on 2020-04-20. Considered USO (investable, never negative) but kept WTI spot to keep the 2004 sample start and the event itself.

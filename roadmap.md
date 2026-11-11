# Risk Engine — Roadmap

**Goal:** a CAD-based risk engine for a six-asset portfolio. Compare historical, parametric and Monte Carlo VaR/ES, backtest them over ~20 years, and stress-test the portfolio.

**Portfolio:** C$10M, pension-style, anchored on CPP Investments' 85/15 market risk target (global equities / Canadian government bonds). No leverage, no shorts.

| Position                                                                                                 | Weight         | Currency                                    |
| -------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------- |
| SPY                                                                                                      | 70%            | USD                                         |
| GLD                                                                                                      | 3%             | USD                                         |
| WTI                                                                                                      | 2%             | USD                                         |
| **USD total**                                                                                      | **75%**  | moves with USD/CAD (adjustable hedge ratio) |
| GoC 10y                                                                                                  | 15%            | CAD                                         |
| XIU                                                                                                      | 10%            | CAD                                         |
| **CAD total**                                                                                      | **25%**  |                                             |
| **Portfolio**                                                                                      | **100%** |                                             |
| **Measures:** 1-day 99% VaR (backtested), 97.5% ES. Optional 10-day horizon for Monte Carlo paths. |                |                                             |

## Phase 0 — Setup and data

- [X] Repo structure, conda env, CLAUDE.md
- [X] BoC and FRED files in `data/raw/`
- [X] Yahoo downloads (XIU, SPY, GLD); inventory complete

## Phase 1 — Clean and align

- [X] One daily table of risk factors, CAD base
- [X] Holiday mismatch: **Option C** (TSX/BoC calendar; forward-fill US data on Canada-only days; US-only days drop out). Costs: ~104 zero-return days for US assets, ~116 two-day returns.
- [X] Forward-fill limit: 3 days; exception `wti` = 5 (FRED oil gaps of 4–5 days in 2011 and 2015)
- [X] Built `data/processed/risk_factors.csv`: 5,507 TSX days × 18 columns, 2004-11-18 to 2026-10-27, no NaNs
- [X] Oil: keep WTI spot; model with **absolute $ changes** (position in barrels). Rule: relative returns for XIU, SPY, GLD, USD/CAD; absolute changes for rates (bp) and oil.
  Limitation: absolute changes ignore price level, so over long windows they overweight high-price periods (2008, 2022) and underweight low-price ones (2016, 2020). Also spot WTI is not directly investable.
- [X] CAD short rate: none in VaR; assume zero expected 1-day return. Use CORRA if a cash rate is needed later.

- Filled values per column (Option C cost): CAD rates 27, SPY/GLD 104, UST 10y 119, USD/CAD 126, WTI 242

## Phase 2 — Zero curve

- [X] Bootstrap GoC zero curve from T-bills + benchmark par yields (semi-annual; linear in zero rates; flat outside known points)
- [X] Test: every input bond reprices to par. Worst repricing error across 5,507 days ≈ 5e-10.
- [X] Compare against the BoC published curve (both as continuous zero rates; 5,454 shared days, 2004-11-18 to 2026-10-14)
  - Results: `results/tables/curve_vs_boc.csv`, `results/tables/worst_day_table.csv`; figures in `results/figures/`.
  - Mean absolute gap 2.3–5.8 bp by maturity (≈4.6 bp averaged over the curve). Mean gap negative at all 40 maturities, deepest ≈ −5.6 bp at 7.75y.
  - Largest single-day gaps at the short end (45.8 bp at 0.25y), where crisis-period T-bill moves are followed exactly by my curve but smoothed by the Bank's fit.
  - Largest 2y gaps in 2025 (2025-02-20, 2025-08-14, ≈ +25–29 bp) come from one-day dips of ≈ 25 bp in the **Bank's** 2y zero rate; my inputs (`goc_2y`, `tb_6m`, `tb_1y`) were stable on both days. No change to data or curve.
  - Gap is nonzero even at benchmark maturities (e.g. −5.5 bp at 7y), so linear interpolation is not the only cause. Hypothesis (untested): benchmark (on-the-run) bonds trade with a liquidity premium, so their yields sit below the Bank's fit across many bonds.

## Phase 3 — Pricing and P&L

- [X] Portfolio defined (weights above). SPY stands in for all foreign equity (simplification).
- [X] Constant weights (reset to target daily) and a constant 10y GoC maturity (each day: hold yesterday's 10y par bond through today's curve, then roll). Simplification: real funds drift between quarterly rebalances and hold bond portfolios managed to an index; carry and trading costs ignored. The VaR methods are unaffected.
- [ ] Price the GoC 10y bond daily from my curve
- [ ] Daily portfolio P&L in CAD; split USD assets into asset move vs FX move
- [ ] FX hedge ratio setting h (0 = unhedged, 1 = fully hedged); compute the minimum-variance h* = 1 + ρ·σ_SPY/σ_FX

- Finding: 1-year rolling corr(SPY return, USD/CAD return) ≈ −0.29 full sample; ≈ −0.55 in 2010–12 but near 0 in 2014 and 2025–26 (natural hedge weakest recently).

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

## Predictions

**Phase 2: my curve vs BoC published curve** (continuous zero rates, 2004–2026; written 2026-11-07, before seeing results)

| Prediction                                                                     | Actual                                                                                                                                                                                        | Verdict                                                                                          |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Typical gap (mean absolute) ≈ 2 bp                                            | 2.3–5.8 bp by maturity; ≈ 4.6 bp averaged                                                                                                                                                   | Missed (≈ 2× too small)                                                                        |
| Worst single day ≈ 10 bp, in a stress period (2008, 2020, 2022)               | 19–46 bp by maturity; largest 45.8 bp at 0.25y. Stress periods visible (2008–09 ≈ −20 bp at 5y/10y; 2022 ≈ +15 bp at 5y), but the largest 2y spikes (2025) were reference-curve glitches | Missed on size; partly right on timing                                                           |
| Largest typical gaps at 7–10y (and 3–5y), the widest gaps between benchmarks | Peaks at ≈ 5.8 bp around 7–7.5y and ≈ 5.6 bp around 3–3.5y                                                                                                                                | Held                                                                                             |
| My curve sits BELOW the Bank's there (straight chord under a concave curve)    | Mean gap negative at all 40 maturities; deepest −5.6 bp at 7.75y. Chord shape visible in the 2008-10-10 and 2026-01-05 curve plots                                                           | Held, but the chord effect alone does not explain the gap at benchmark nodes (see Phase 2 notes) |

**Phase 5: backtests**

- ---

## Deviations log

Record any change of plan here: date, what changed, why.

- 2026-11-04: USD/CAD from FRED (`DEXCAUS`), not BoC; BoC's daily series only starts 2017.
- 2026-11-04: Gold from Yahoo (`GLD`); FRED no longer carries LBMA gold.
- 2026-11-04: Forward-fill exception for `wti` (limit 5 vs 3) after finding 4–5 day gaps in FRED oil (2011-04 to 2011-07, 2015-01).
- 2026-11-04: Oil modeled with absolute changes because of the negative price on 2020-04-20. Considered USO (investable, never negative) but kept WTI spot to keep the 2004 sample start and the event itself.
- 2026-11-08: Kept my bootstrapped curve as the engine's curve; the BoC published curve is used only for validation (it lags ~3 weeks, has empty days, and is a smoothed fit).
- 2026-11-09: Dropped the 10y US Treasury. The portfolio follows CPP Investments' 85/15 market risk target, whose bond leg is Canadian government bonds only. `ust_10y` stays in the data but is unused.
- 2026-11-09: Added an FX hedge ratio setting after finding the SPY/USD-CAD natural hedge varies over time (CPP hedges only to a target CAD exposure, not fully).

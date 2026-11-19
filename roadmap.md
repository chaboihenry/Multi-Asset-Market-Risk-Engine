# Risk Engine — Roadmap

**Goal:** a CAD-based risk engine for a pension-style multi-asset portfolio. Compare historical, parametric and Monte Carlo VaR/ES, backtest them over ~20 years, and stress-test the portfolio.
**Why:** preparation for an investment/market risk role at a Canadian pension fund (CPP-style): fixed income and curve building, VaR/ES, Monte Carlo, backtesting, FX hedging.

**Portfolio:** C$10M, pension-style, anchored on CPP Investments' 85/15 market risk target (global equities / Canadian government bonds). No leverage, no shorts.

| Position            | Weight         | Currency                                    |
| ------------------- | -------------- | ------------------------------------------- |
| SPY                 | 70%            | USD                                         |
| GLD                 | 3%             | USD                                         |
| WTI                 | 2%             | USD                                         |
| **USD total** | **75%**  | moves with USD/CAD (adjustable hedge ratio) |
| GoC 10y             | 15%            | CAD                                         |
| XIU                 | 10%            | CAD                                         |
| **CAD total** | **25%**  |                                             |
| **Portfolio** | **100%** |                                             |

**Measures:** 1-day 99% VaR (backtested), 97.5% ES. Optional 10-day horizon for Monte Carlo paths.

## Phase 0 — Setup and data

- [X] Repo structure, conda env, CLAUDE.md
- [X] BoC and FRED files in `data/raw/`
- [X] Yahoo downloads (XIU, SPY, GLD); inventory complete

## Phase 1 — Clean and align

- [X] One daily table of risk factors, CAD base
- [X] Holiday mismatch: use the TSX/BoC calendar; forward-fill US data on Canada-only days; US-only days drop out. Costs: ~104 zero-return days for US assets, ~116 two-day returns.
- [X] Forward-fill limit: 3 days; exception `wti` = 5 (FRED oil gaps of 4–5 days in 2011 and 2015)
- [X] Built `data/processed/risk_factors.csv`: 5,507 TSX days × 18 columns, 2004-11-18 to 2026-10-27, no NaNs
- [X] Oil: keep WTI spot; model with **absolute $ changes** (position in barrels). Rule: relative returns for XIU, SPY, GLD, USD/CAD; absolute changes for rates (bp) and oil.
  Limitation: absolute changes ignore price level, so over long windows they overweight high-price periods (2008, 2022) and underweight low-price ones (2016, 2020). Also spot WTI is not directly investable.
- [X] CAD short rate: none in VaR; assume zero expected 1-day return. Use CORRA if a cash rate is needed later.

- Filled values per column (cost of the calendar choice): CAD rates 27, SPY/GLD 104, UST 10y 119, USD/CAD 126, WTI 242

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
- [X] Price the GoC 10y bond daily from my curve
  - 5,506 daily returns, std 0.43%; implied duration ≈ 8.86.
- [X] Daily portfolio P&L in CAD; split USD assets into asset move vs FX move
  - 5,506 days, hedge = 0. Daily std C$88.8k (0.89%). Worst −C$888k (2020-03-16); best +C$904k (2008-10-28).
  - Natural hedge: SPY std C$82.8k, FX C$40.6k, corr −0.29; combined ≈ C$81k, below SPY alone.
  - Oil: 2020-04-20 is the 4th worst day (−C$703k; −C$606k from the 2% oil position). Revisit in Phase 4.
- [X] FX hedge ratio setting h (0 = unhedged, 1 = fully hedged); compute the minimum-variance h* = 1 + ρ·σ_SPY/σ_FX
  - Full sample: corr(SPY, USD/CAD) = −0.29 and σ_SPY/σ_FX ≈ 2.2, so h* = 1 − 0.29 × 2.2 ≈ 0.366 (hedge about 37% of USD exposure).
  - 1-year rolling: corr ≈ −0.55 in 2010–12 (h* ≈ −0.2 to 0.1: hedge nothing) but near 0 in 2014 and 2025–26 (h* ≈ 0.85: hedge most). Rolling h* ranges −0.41 to 1.31, so no single value is stable.
  - Setting used: h = 0 is the base case for Phases 4–5. h* = 0.366 is a comparison setting only, because it is estimated from the whole sample (look-ahead). SPY's h* is applied to all USD positions (SPY is 70 of the 75 points).

## Phase 4 — VaR and ES

- [X] Historical simulation
- [X] Parametric (normal; then a fat-tailed or EWMA variant)
  - `engine/var.py`, `scripts/07_var_forecasts.py` → `var_forecasts.csv`: 5,006 daily forecasts (2006-11-15 on), window 500, EWMA λ = 0.94.
  - Average 99% VaR: historical C$230k, normal (rolling σ) C$199k, normal (EWMA) C$180k. EWMA peaks at C$960k (2020-03-18), above the worst actual loss (C$888k).
- [X] Monte Carlo
  - `engine/montecarlo.py`, `scripts/08_var_monte_carlo.py`: six factors drawn jointly from a multivariate Student-t (df = 4), 10,000 scenarios a day, covariance from the previous 500 days. Average 99% VaR C$225k.
- [X] Decide: estimation window length
  - 500 days (base case); 250 days as a sensitivity check in Phase 5. Longer windows estimate the tail better but react more slowly (Hendricks 1996).

## Phase 5 — Backtesting

- [X] Write predictions **before** running (see below)
- [X] Kupiec (breach frequency), Christoffersen (clustering), Basel traffic light

  - `engine/backtest.py`, `scripts/09_backtest.py` → `results/tables/backtest_summary.csv`, `breaches_by_year.csv`. 5,006 days, 99% VaR, window 500, hedge = 0.

  | Model                  | Breaches (rate) | Kupiec LR           | Christoffersen LR | Years green / yellow / red |
  | ---------------------- | --------------- | ------------------- | ----------------- | -------------------------- |
  | Historical             | 83 (1.66%)      | 18.3, rejected      | 9.0, rejected     | 13 / 4 / 4                 |
  | Normal, rolling σ     | 121 (2.42%)     | 72.7, rejected      | 11.3, rejected    | 12 / 2 / 7                 |
  | Normal, EWMA           | 103 (2.06%)     | 43.3, rejected      | 1.4, passes       | 9 / 11 / 1                 |
  | Monte Carlo (t, df 4)  | 80 (1.60%)      | 15.3, rejected      | 9.7, rejected     | 13 / 5 / 3                 |
  | Student-t, EWMA (df 4) | 66 (1.32%)      | 4.7, rejected at 5% | 0.02, passes      | 15 / 6 / 0                 |


  - None of the first four models passes both tests (reject above 3.84). The 500-day models fail in bursts (2008, 2018, 2020); EWMA reacts in time but its normal multiplier is too small, so it is breached a little in most years.
- [X] Window sensitivity: repeat with 250 days

  - 5,256 days (not the same dates as the 500-day run, so the comparison is approximate). Breach rates: historical 1.66%, normal rolling 2.17%, EWMA 2.07%, Monte Carlo 1.37%. All four still fail Kupiec, and the three window models still fail Christoffersen (LR 8.3–12.4). A shorter window does not fix the clustering.
- [X] Fifth model: EWMA volatility with a Student-t multiplier (df = 4), combining EWMA's timing with fat tails

  - 66 breaches (1.32%); the only model with no red year, and 1 breach in 2008 against 14–27 for the window models. Passes Christoffersen (p = 0.89). Kupiec LR 4.7 (p = 0.03): rejected at the 5% level, not at 1%; the acceptance range at 5% is about 37–64 breaches.
  - Caveat: designed after seeing the first backtest, so this is not an out-of-sample result. df was not tuned.
- [X] Calm vs crisis periods, all five models; where the models disagree most

  - `scripts/09_backtest.py` → `results/tables/crisis_breaches.csv`. Crisis years = 2008, 2015, 2020, 2022 (the Phase 6 events, chosen before looking at breaches); they are about 20% of the sample.

  | Model              | Breaches in crisis years | Share of its breaches |
  | ------------------ | ------------------------ | --------------------- |
  | Historical         | 41 of 83                 | 49%                   |
  | Normal, rolling σ | 58 of 121                | 48%                   |
  | Monte Carlo (t)    | 40 of 80                 | 50%                   |
  | Normal, EWMA       | 24 of 103                | 23%                   |
  | Student-t, EWMA    | 14 of 66                 | 21%                   |


  - The three window models have about half their breaches in a fifth of the sample; the two EWMA models are close to the 20% an evenly spread model would show.
- [X] Hedge comparison: h = 0, 0.37, 1, and rolling h* (capped to 0–1, using past data only)

  - `scripts/10_hedge_comparison.py` → `results/tables/hedge_comparison.csv`. All four settings on the same 5,256 days (those where the 250-day rolling h* exists).

  | Setting                              | Daily std | Worst day | 99% VaR | 97.5% ES |
  | ------------------------------------ | --------- | --------- | ------- | -------- |
  | Unhedged (h = 0)                     | C$89.8k   | −C$888k  | C$252k  | C$272k   |
  | Min-variance, full sample (h = 0.37) | C$89.2k   | −C$885k  | C$259k  | C$277k   |
  | Fully hedged (h = 1)                 | C$94.0k   | −C$879k  | C$281k  | C$301k   |
  | Rolling h* (250 days)                | C$89.0k   | −C$884k  | C$255k  | C$278k   |


  - Hedging lowers volatility slightly (rolling h*: −0.9%) but raises tail risk: 99% VaR is 1.2% higher with the rolling h*, 2.9% higher at h = 0.37 and 11.7% higher when fully hedged. The unhedged portfolio has the lowest VaR and ES.
  - Likely reason (not yet checked in the repo): USD/CAD tends to rise on the days SPY falls hardest, so the unhedged FX exposure cushions the worst days and a hedge gives that up.
  - h = 0.37 is fitted on the full sample (look-ahead); the rolling h* uses past data only and still does not beat the unhedged portfolio in the tail.

## Phase 5b — Buy-and-hold with periodic rebalancing

Goal: see how wealth, weights and risk behave when the portfolio is run like a real fund (holdings drift, quarterly rebalance) instead of being reset to target every day. Unhedged; no trading costs, contributions or benefit payments.

- [X] Portfolio bought in 2004, rebalanced to 70/15/10/3/2 on the last trading day of each CPP fiscal quarter (March, June, September, December): 88 rebalance dates, 2004-12-31 to 2026-09-30

  - `engine/rebalance.py`, `scripts/11_rebalanced_portfolio.py` → `rebalanced_values.csv`, `rebalanced_weights.csv`. Holdings are fixed units between rebalances.
  - Bond sleeve: constant 10y maturity, now with coupon carry (previous day's yield × calendar days / 365). The bond index ends at 1.85; without carry it ends at 1.03.
- [X] Wealth path over 22 years; weight drift between rebalances

  - C$10.0M on 2004-11-18 grows to C$88.0M on 2026-10-27.
  - Weight ranges: SPY 66.0–75.0% (target 70), GoC 10y 12.9–19.9% (15), XIU 7.6–11.9% (10), GLD 2.3–4.2% (3), WTI −3.5–3.8% (2).
  - Oil: with barrels fixed, the position was worth −C$1.15M on 2020-04-20 (weight −3.5%).
- [X] VaR/ES on actual holdings each day, as a real risk report would; compare with the constant-weight results

  - Each day: the previous 500 days of market moves applied to the holdings at the previous close (% returns for four positions, $ changes per barrel for oil), then `empirical_var_es`. → `rebalanced_var.csv`, `results/tables/rebalanced_vs_constant.csv`. Same 5,006 days as the constant-weight forecasts.

  | Portfolio            | Mean 99% VaR (% of value) | Max   | Breaches (rate) | Kupiec LR | Christoffersen LR |
  | -------------------- | ------------------------- | ----- | --------------- | --------- | ----------------- |
  | Constant weights     | 2.30%                     | 4.01% | 83 (1.66%)      | 18.3      | 9.0               |
  | Rebalanced quarterly | 2.28%                     | 4.37% | 82 (1.64%)      | 17.3      | 9.2               |


  - The two are almost identical: quarterly rebalancing keeps the weights close enough to target that the risk, and the historical model's failures, are the same. In dollars the VaR grows from C$180k (2006) to C$1.77M (2026) with the portfolio. The Phase 4–5 conclusions carry over to a portfolio run like a real fund.
  - Not done: the EWMA Student-t model on the rebalanced portfolio.

## Phase 6 — Stress tests

- [X] Historical: 2008, 2015 oil crash, 2020 COVID, 2022 rate shock

  - Episodes (peak to trough, dates from public sources, chosen before running anything):

  | Episode               | Start      | End        | Defined by                                                                              |
  | --------------------- | ---------- | ---------- | --------------------------------------------------------------------------------------- |
  | 2008 financial crisis | 2007-10-09 | 2009-03-09 | S&P 500 closing peak to trough (−56.8%)                                                |
  | 2014–16 oil crash    | 2014-06-20 | 2016-02-11 | WTI peak ($107.95) to trough ($26.21)                                                   |
  | 2020 COVID crash      | 2020-02-19 | 2020-03-23 | S&P 500 record to trough (−34%)                                                        |
  | 2022 rate shock       | 2022-01-04 | 2022-10-12 | S&P 500 record (2022-01-03) to trough (−25.4%); starts a day later, see deviations log |


  - Method: CAD price change of each position over the episode (`cad_prices`, bond with carry), applied to C$10M at target weights.
  - `engine/stress.py`, `scripts/12_stress_tests.py` → `results/tables/stress_historical.csv`. P&L in C$:

  | Episode               | SPY      | GoC 10y | XIU    | GLD   | WTI    | Total    | % of C$10M |
  | --------------------- | -------- | ------- | ------ | ----- | ------ | -------- | ---------- |
  | 2008 financial crisis | −2,860k | +295k   | −421k | +191k | −45k  | −2,840k | −28.4%    |
  | 2014–16 oil crash    | +1,717k  | +238k   | −138k | +65k  | −137k | +1,745k  | +17.5%     |
  | 2020 COVID crash      | −1,902k | +84k    | −355k | +18k  | −104k | −2,259k | −22.6%    |
  | 2022 rate shock       | −1,255k | −201k  | −126k | 0k    | +48k   | −1,534k | −15.3%    |

  - Bonds cushioned 2008 and 2020 but lost in 2022, when stocks and bonds fell together.
- [X] Hypothetical shocks

  - `engine/stress.py` (`shock_to_cad_returns`), `scripts/12_stress_tests.py` → `results/tables/stress_hypothetical.csv`. Shocks in market terms (USD moves, USD/CAD, 10y yield), converted to CAD price changes; the bond is repriced in full with `bond_price` on a flat curve (base yield 3.83%, 2026-10-27). Markets not listed are flat.

  | Scenario             | Shock                                          | SPY      | GoC 10y | XIU    | GLD   | WTI    | Total    | % of C$10M |
  | -------------------- | ---------------------------------------------- | -------- | ------- | ------ | ----- | ------ | -------- | ---------- |
  | Stagflation          | SPY −20%, XIU −20%, WTI +50%, yields +200 bp | −1,400k | −225k  | −200k | 0k    | +100k  | −1,725k | −17.2%    |
  | CAD rally in a crash | SPY −25%, USD/CAD −10%                       | −2,275k | 0k      | 0k     | −30k | −20k  | −2,325k | −23.2%    |
  | Oil shock            | WTI −60%, USD/CAD +10%                        | +700k    | 0k      | 0k     | +30k  | −112k | +618k    | +6.2%      |


  - CAD rally: SPY falls less in USD than in the COVID episode (−25% against −34%), yet the portfolio loses more (−23.2% against −22.6%), because the FX move adds to the loss instead of cushioning it. This is the scenario the portfolio is most exposed to.
  - Full revaluation: +200 bp costs the bond 15.0%, against 17.7% from duration alone (convexity).
- [X] Propagate shocks through a causal graph. Not done here, noted for a future extension.

## Phase 7 — Write-up

- [X] README results, STRUCTURE layout.

## Predictions

**Phase 2: my curve vs BoC published curve** (continuous zero rates, 2004–2026; written 2026-11-07, before seeing results)

| Prediction                                                                     | Actual                                                                                                                                                                                        | Verdict                                                                                          |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Typical gap (mean absolute) ≈ 2 bp                                            | 2.3–5.8 bp by maturity; ≈ 4.6 bp averaged                                                                                                                                                   | Missed (≈ 2× too small)                                                                        |
| Worst single day ≈ 10 bp, in a stress period (2008, 2020, 2022)               | 19–46 bp by maturity; largest 45.8 bp at 0.25y. Stress periods visible (2008–09 ≈ −20 bp at 5y/10y; 2022 ≈ +15 bp at 5y), but the largest 2y spikes (2025) were reference-curve glitches | Missed on size; partly right on timing                                                           |
| Largest typical gaps at 7–10y (and 3–5y), the widest gaps between benchmarks | Peaks at ≈ 5.8 bp around 7–7.5y and ≈ 5.6 bp around 3–3.5y                                                                                                                                | Held                                                                                             |
| My curve sits BELOW the Bank's there (straight chord under a concave curve)    | Mean gap negative at all 40 maturities; deepest −5.6 bp at 7.75y. Chord shape visible in the 2008-10-10 and 2026-01-05 curve plots                                                           | Held, but the chord effect alone does not explain the gap at benchmark nodes (see Phase 2 notes) |

**Phase 5: backtests** (99% 1-day VaR, 5,006 days, window 500; written 2026-11-15, before counting breaches. Target: 1%, about 50 breaches)

| Prediction                                                                                                  | Actual                                                                         | Verdict                                          |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------ |
| Historical: breach rate 1.5–2.5%; clustered in crises (slow to adjust in March 2020)                       | 1.66%; 17 breaches in 2008, 11 in 2020, none in 10 of 21 years                 | Held                                             |
| Normal, rolling: breach rate above 2.5%; mostly spread out, with a cluster in March 2020                    | 2.42%; the most clustered model (27 in 2008)                                   | Just missed on rate; missed on timing            |
| Normal, EWMA: breach rate below 1%; spread out                                                              | 2.06%; breaches in 19 of 21 years, at most 11 in one year                      | Missed on rate (2× the target); held on timing  |
| Monte Carlo (t, df 4): breach rate below 1%; clustered                                                      | 1.60%; 14 in 2008, 12 in 2020                                                  | Missed on rate; held on timing                   |
| Ranking, fewest to most breaches: Monte Carlo or EWMA, then historical, then normal rolling                 | Monte Carlo 80, historical 83, EWMA 103, normal rolling 121                    | Partly held (EWMA is third, not first or second) |
| March 2020: EWMA has the fewest breaches; historical the most (possibly normal rolling)                     | EWMA 3; normal rolling 8; historical and Monte Carlo 7                         | Held                                             |
| 2020-04-20 (−C$703k): all four models are breached                                                         | All four breached                                                              | Held                                             |
| Independence test: none pass, except possibly EWMA (added before running the test)                          | Only EWMA passes (LR 1.4); the other three are rejected                        | Held                                             |
| Student-t EWMA (written 2026-11-16): fails Kupiec but is closer than the normal EWMA; passes Christoffersen | Kupiec LR 4.7 against 43.3 (rejected at 5%, narrowly); Christoffersen p = 0.89 | Held                                             |

Lesson: the rate misses all came from underestimating fat tails. A fast volatility estimate (EWMA) fixes the timing of breaches but not their number; fat tails with a slow window (Monte Carlo) do the reverse.

## Deviations log

Record any change of plan here: date, what changed, why.

- 2026-11-04: USD/CAD from FRED (`DEXCAUS`), not BoC; BoC's daily series only starts 2017.
- 2026-11-04: Gold from Yahoo (`GLD`); FRED no longer carries LBMA gold.
- 2026-11-04: Forward-fill exception for `wti` (limit 5 vs 3) after finding 4–5 day gaps in FRED oil (2011-04 to 2011-07, 2015-01).
- 2026-11-04: Oil modeled with absolute changes because of the negative price on 2020-04-20. Considered USO (investable, never negative) but kept WTI spot to keep the 2004 sample start and the event itself.
- 2026-11-08: Kept my bootstrapped curve as the engine's curve; the BoC published curve is used only for validation (it lags ~3 weeks, has empty days, and is a smoothed fit).
- 2026-11-09: Dropped the 10y US Treasury. The portfolio follows CPP Investments' 85/15 market risk target, whose bond leg is Canadian government bonds only. `ust_10y` stays in the data but is unused.
- 2026-11-09: Added an FX hedge ratio setting after finding the SPY/USD-CAD natural hedge varies over time (CPP hedges only to a target CAD exposure, not fully).
- 2026-11-13: Oil P&L split: `wti_fx` and `wti_hedge` use the target C$200k, but on 2020-04-21 the true position was ≈ −C$405k (barrels carried through the negative price). Only the FX/asset split is off that day; the total is exact. Oil has no `_cross` column (its cross term sits in `wti_asset`).
- 2026-11-15: Added a fifth VaR model (EWMA volatility with a Student-t multiplier) after the backtest showed EWMA passes the independence test but fails on breach count, while the fat-tailed Monte Carlo does the reverse. It was designed after seeing the results, so its backtest is not out-of-sample; df = 4 is kept from the Monte Carlo model (chosen before any backtest) and is not tuned.
- 2026-11-17: 2022 stress episode starts 2022-01-04, not the S&P 500 record date of 2022-01-03, because the TSX was closed on January 3 (New Year's holiday observed). The S&P 500 closed about 0.06% below its record on January 4.
- 2026-11-18: Dropped the causal-graph stress extension. Done properly it needs graph discovery, estimation and validation, which would be another phase; a rushed version would overstate what it shows. Kept as future work.

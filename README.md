# Multi-Asset Market Risk Engine (CAD)

A daily risk engine for a **C$10M pension-style portfolio**, built in Python from free public data covering **2004–2026**. It builds the Government of Canada yield curve, prices the portfolio in Canadian dollars, forecasts **1-day 99% VaR and 97.5% Expected Shortfall** with five models, backtests them over 20 years, and stress-tests the portfolio against real crises and hypothetical shocks.

**Headline results**

- None of the four standard VaR models passes both regulatory-style backtests; a fifth model (EWMA volatility + fat tails) comes closest, with no Basel red year in 20.
- Hedging the US-dollar exposure *raises* tail risk: for a Canadian investor the US dollar rises in sell-offs and cushions the worst days.
- The worst stress is a crash in which the Canadian dollar strengthens (−23.2%), worse than COVID (−22.6%) even with a smaller fall in US stocks.

Every result below links to the section of [`ROADMAP.md`](ROADMAP.md) that records how it was produced, and to the file that holds it. Predictions were written down before each backtest and scored afterwards ([`ROADMAP.md` › Predictions](ROADMAP.md#predictions)).

## The portfolio

Anchored on CPP Investments' 85/15 market risk target (global equities / Canadian government bonds). No leverage, no shorts, unhedged in the base case.

| SPY (US equities) | GoC 10y bond | XIU (TSX 60) | GLD (gold) | WTI crude oil |
| ----------------- | ------------ | ------------ | ---------- | ------------- |
| 70% · USD        | 15% · CAD   | 10% · CAD   | 3% · USD  | 2% · USD     |

## Results by phase

### 1. Data — one clean daily table

5,507 trading days × 18 risk factors from the Bank of Canada, FRED and Yahoo Finance, aligned to the TSX calendar. Oil is modelled in barrels with dollar price changes, so the negative oil price of 20 April 2020 (a −302% one-day move) is handled correctly.
Details: [Phase 1](ROADMAP.md#phase-1--clean-and-align) · Data: [`data/processed/risk_factors.csv`](data/processed/risk_factors.csv) · Code: [`scripts/02_build_risk_factors.py`](scripts/02_build_risk_factors.py)

### 2. Yield curve — bootstrapped daily, checked against the Bank of Canada

Zero curve bootstrapped every day from T-bills and benchmark bonds. Every input bond reprices to par within 5e-10, and the curve sits on average **4.6 bp** from the Bank of Canada's published curve over 5,454 days.
Details: [Phase 2](ROADMAP.md#phase-2--zero-curve) · Results: [`results/tables/gap_table.csv`](results/tables/gap_table.csv), [`results/figures/`](results/figures/) · Code: [`engine/curve.py`](engine/curve.py), [`scripts/03_build_curve.py`](scripts/03_build_curve.py), [`scripts/04_compare_boc_curve.py`](scripts/04_compare_boc_curve.py)

### 3. Pricing and P&L — daily, in CAD

The 10y bond is repriced daily on the curve (implied duration 8.86). Daily portfolio P&L has a standard deviation of C$88.8k (0.89%); the worst day was −C$888k (16 March 2020). The US-dollar exposure is a natural hedge: SPY and USD/CAD returns have a correlation of −0.29.
Details: [Phase 3](ROADMAP.md#phase-3--pricing-and-pl) · Data: [`data/processed/pnl_breakdown_portfolio.csv`](data/processed/pnl_breakdown_portfolio.csv) · Code: [`engine/portfolio.py`](engine/portfolio.py), [`scripts/06_portfolio_pnl.py`](scripts/06_portfolio_pnl.py)

### 4. VaR and ES — five models

Historical simulation, normal (rolling and EWMA volatility), a Monte Carlo simulation of six risk factors from a multivariate Student-t, and EWMA volatility with a Student-t multiplier. 5,006 daily forecasts each, using only data available the day before.
Details: [Phase 4](ROADMAP.md#phase-4--var-and-es) · Data: [`data/processed/var_forecasts.csv`](data/processed/var_forecasts.csv) · Code: [`engine/var.py`](engine/var.py), [`engine/montecarlo.py`](engine/montecarlo.py), [`scripts/07_var_from_forecasts.py`](scripts/07_var_from_forecasts.py), [`scripts/08_var_monte_carlo.py`](scripts/08_var_monte_carlo.py)

### 5. Backtesting — does each model breach as often as it should?

A correct 99% VaR is breached on about 50 of 5,006 days. Kupiec tests the count, Christoffersen tests whether breaches cluster (reject above 3.84).

| Model                                | Breaches     | Kupiec                      | Christoffersen    | Basel red years |
| ------------------------------------ | ------------ | --------------------------- | ----------------- | --------------- |
| Historical simulation                | 83           | 18.3 ✗                     | 9.0 ✗            | 4               |
| Normal, rolling volatility           | 121          | 72.7 ✗                     | 11.3 ✗           | 7               |
| Normal, EWMA volatility              | 103          | 43.3 ✗                     | 1.4 ✓            | 1               |
| Monte Carlo, Student-t               | 80           | 15.3 ✗                     | 9.7 ✗            | 3               |
| **Student-t, EWMA volatility** | **66** | **4.7 ✗ (narrowly)** | **0.02 ✓** | **0**     |

Models with a 500-day window put about half their breaches into four crisis years (20% of the sample); EWMA reacts in time but needs fat tails. The fifth model was designed after the first backtest, so its result is not out-of-sample. Hedging test: fully hedging the FX raises 99% VaR by 11.7%; even a hedge fitted only on past data raises it.
Details: [Phase 5](ROADMAP.md#phase-5--backtesting) · Results: [`results/tables/backtest_summary.csv`](results/tables/backtest_summary.csv), [`crisis_breaches.csv`](results/tables/crisis_breaches.csv), [`hedge_comparison.csv`](results/tables/hedge_comparison.csv) · Code: [`engine/backtest.py`](engine/backtest.py), [`scripts/09_backtest.py`](scripts/09_backtest.py), [`scripts/10_hedge_comparison.py`](scripts/10_hedge_comparison.py)

### 5b. A portfolio run like a real fund

Holdings drift and are rebalanced each CPP fiscal quarter. C$10M grows to **C$88M**; SPY never drifts more than 5 points from target. VaR (2.28% vs 2.30% of value) and breaches (82 vs 83) match the daily-reset portfolio, so the Phase 4–5 conclusions carry over.
Details: [Phase 5b](ROADMAP.md#phase-5b--buy-and-hold-with-periodic-rebalancing) · Results: [`results/tables/rebalanced_vs_constant.csv`](results/tables/rebalanced_vs_constant.csv) · Code: [`engine/rebalance.py`](engine/rebalance.py), [`scripts/11_rebalanced_portfolio.py`](scripts/11_rebalanced_portfolio.py)

### 6. Stress tests — historical crises and hypothetical shocks

Applied to today's C$10M at target weights; the bond is fully repriced on the curve.

| Scenario                                                           | % of portfolio |
| ------------------------------------------------------------------ | -------------- |
| 2008 financial crisis                                              | −28.4%        |
| Hypothetical: US stocks −25%, Canadian dollar strengthens 10%     | −23.2%        |
| 2020 COVID crash                                                   | −22.6%        |
| Hypothetical: stagflation (stocks −20%, yields +200 bp, oil +50%) | −17.2%        |
| 2022 rate shock                                                    | −15.3%        |
| 2014–16 oil crash                                                 | +17.5%         |

In every historical crisis the Canadian dollar fell and cushioned the loss; the hypothetical CAD rally removes that cushion. In 2022 bonds fell alongside stocks.
Details: [Phase 6](ROADMAP.md#phase-6--stress-tests) · Results: [`results/tables/stress_historical.csv`](results/tables/stress_historical.csv), [`stress_hypothetical.csv`](results/tables/stress_hypothetical.csv) · Code: [`engine/stress.py`](engine/stress.py), [`scripts/12_stress_tests.py`](scripts/12_stress_tests.py)

## Limitations and next steps

SPY stands in for all foreign equity and one 10y bond for the bond portfolio; no trading costs or cash flows; spot WTI is not directly investable. Next: propagate shocks through an estimated causal graph, and test the Student-t EWMA model out of sample.

## Running it

`conda env create -f environment.yml`, then run the scripts in `scripts/` in numerical order from the repository root. Tests: `python -m pytest`.

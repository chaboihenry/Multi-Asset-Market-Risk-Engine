# Repository structure

Where everything lives, and which script produces which file. Results are summarised in [`README.md`](README.md); the full record of decisions and results is in [`ROADMAP.md`](ROADMAP.md).

## Layout

```
├── README.md              Results summary
├── ROADMAP.md             Phase-by-phase plan, results, predictions and deviations log
├── data_inventory.md      Every data series: source, ID, dates, units, gaps
├── environment.yml        Conda environment
│
├── common/                Shared settings
│   ├── paths.py           Folder locations
│   └── portfolio.py       Weights, currencies, C$10M notional, hedge ratio
│
├── engine/                Pure functions (no file reading or writing)
│   ├── curve.py           T-bill discounting, bond pricing, curve bootstrap
│   ├── pricing.py         Bond return on the next day's curve
│   ├── portfolio.py       Asset returns, position values, oil barrels, P&L breakdown, hedge ratios
│   ├── hedging.py         FX hedge-ratio functions
│   ├── var.py             Historical, normal, EWMA and Student-t VaR/ES
│   ├── montecarlo.py      Six-factor Student-t simulation and Monte Carlo VaR/ES
│   ├── backtest.py        Breaches, Kupiec, Christoffersen, Basel zones
│   ├── rebalance.py       CAD prices, quarterly rebalancing, VaR on actual holdings
│   └── stress.py          Historical-episode and hypothetical-shock P&L
│
├── scripts/               Run in numerical order; each reads and writes files
├── tests/                 pytest tests for the engine
│
├── data/
│   ├── raw/               Downloaded files (boc/, fred/, yahoo/)
│   └── processed/         Daily tables built by the scripts
│
└── results/
    ├── tables/            Summary tables (the numbers in the README)
    └── figures/           Curve comparison charts
```

## Scripts and their outputs

| Script                         | Reads                                             | Writes                                                                                                                                             | ROADMAP  |
| ------------------------------ | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `01_download_yahoo.py`       | Yahoo Finance                                     | `data/raw/yahoo/*.csv`                                                                                                                           | Phase 0  |
| `02_build_risk_factors.py`   | `data/raw/`                                     | `processed/risk_factors.csv`                                                                                                                     | Phase 1  |
| `03_build_curve.py`          | risk factors                                      | `processed/goc_discount_factors.csv`                                                                                                             | Phase 2  |
| `04_compare_boc_curve.py`    | discount factors, BoC curve                       | `tables/gap_table.csv`, `tables/worst_differences.csv`, `figures/*.png`                                                                      | Phase 2  |
| `05_bond_returns.py`         | discount factors, risk factors                    | `processed/goc_10y_returns.csv`                                                                                                                  | Phase 3  |
| `06_portfolio_pnl.py`        | risk factors, bond returns                        | `processed/pnl_breakdown_portfolio.csv`, `processed/total_pnl_portfolio.csv`                                                                   | Phase 3  |
| `07_var_from_forecasts.py`   | total P&L                                         | `processed/var_forecasts.csv` (and `var_forecasts250.csv` for the 250-day check)                                                               | Phase 4  |
| `08_var_monte_carlo.py`      | risk factors, bond returns, P&L breakdown         | adds Monte Carlo columns to `var_forecasts.csv`                                                                                                  | Phase 4  |
| `09_backtest.py`             | `var_forecasts.csv`                             | `tables/backtest_summary.csv`, `tables/breaches_by_year.csv`, `tables/crisis_breaches.csv` (and the `250` versions)                        | Phase 5  |
| `10_hedge_comparison.py`     | risk factors, bond returns                        | `tables/hedge_comparison.csv`                                                                                                                    | Phase 5  |
| `11_rebalanced_portfolio.py` | risk factors, bond returns, `var_forecasts.csv` | `processed/rebalanced_values.csv`, `processed/rebalanced_weights.csv`, `processed/rebalanced_var.csv`, `tables/rebalanced_vs_constant.csv` | Phase 5b |
| `12_stress_tests.py`         | risk factors, bond returns                        | `tables/stress_historical.csv`, `tables/stress_hypothetical.csv`                                                                               | Phase 6  |

Scripts 07 and 08 must run in that order: 07 rebuilds `var_forecasts.csv`, and 08 adds its columns back.

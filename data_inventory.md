# Data inventory

Base currency: CAD. Free sources only. All series business daily. Checked 2026-11-04.

| #  | Series                                      | Source / ID                         | Start      | End        | Units             | Blanks          | Notes                                                                                       |
| -- | ------------------------------------------- | ----------------------------------- | ---------- | ---------- | ----------------- | --------------- | ------------------------------------------------------------------------------------------- |
| 1  | GoC benchmark yields: 2, 3, 5, 7, 10y, long | BoC Valet `bond_yields_benchmark` | 2001-01-02 | 2026-11-03 | %                 | 1 row           | 23-line metadata header. "Long" is not a fixed 30y. Ignore RRB column.                      |
| 2  | GoC T-bills 1m, 2m, 3m, 6m, 1y              | BoC Valet `TB.CDN.*.MID`          | 2001-01-02 | 2026-11-03 | %                 | ~0 after 2001   | 14-line header. Column order differs from the URL. 1m/2m dip to 0.00 and -0.01 in 2020–21. |
| 3  | CORRA                                       | BoC Valet `AVG.INTWO`             | 1997-08-12 | 2026-11-03 | %                 | 0               | Candidate CAD short rate.                                                                   |
| 4  | Overnight money market rate                 | BoC Valet `CL.CDN.MOST.1DL`       | 2001-01-02 | 2026-11-02 | %                 | —              | Not needed; drop.                                                                           |
| 5  | GoC zero curve (comparison only)            | BoC zero-coupon curves              | 1986-01-02 | 2026-10-14 | **decimal** | 628 all-na rows | 120 columns, 0.25–30y. ~3-week lag. 30y starts 1991.                                       |
| 6  | US 10y Treasury yield                       | FRED `DGS10`                      | 1962-01-02 | 2026-11-02 | %                 | 721             | US holidays blank.                                                                          |
| 7  | USD/CAD                                     | FRED `DEXCAUS`                    | 1971-01-04 | 2026-10-30 | CAD per USD       | 559             | NY noon rate, US calendar.                                                                  |
| 8  | WTI crude, spot                             | FRED `DCOILWTICO`                 | 1986-01-02 | 2026-10-27 | USD/bbl           | 1117            | 2020-04-20 = -36.98.                                                                        |
| 9  | TSX 60 ETF                                  | Yahoo `XIU.TO`                    | 1999-10-04 | 2026-11-04 | CAD               | 0               | TSX calendar. Use Adj Close (dividends). Downloaded 2026-11-04.                             |
| 10 | S&P 500 ETF                                 | Yahoo `SPY`                       | 1993-01-29 | 2026-11-04 | USD               | 0               | NYSE calendar. Use Adj Close. Downloaded 2026-11-04.                                        |
| 11 | Gold ETF                                    | Yahoo `GLD`                       | 2004-11-18 | 2026-11-04 | USD               | 0               | No dividends: Adj Close = Close. Downloaded 2026-11-04.                                     |

## Common sample

- Start: GLD, 2004-11-18. End: oil, 2026-10-27.
- Usable sample: 2004-11-18 to 2026-10-27 (~22 years).
- Calendars in that window: 5,403 days both TSX and NYSE open, 104 TSX-only, 116 NYSE-only.
  FX (FRED) is missing on 81 more days when the NYSE is open (Fed holidays, e.g. Columbus Day).

## Open questions

- Holiday mismatch (TSX vs NYSE closed days): ______
- Oil on 2020-04-20 (negative price): ______
- CAD short rate: 3m T-bill or CORRA? ______

# ECON6067 Individual Project — Replication of Card & Krueger (1994)

**Paper replicated:** Card, D., & Krueger, A. B. (1994). *Minimum Wages and
Employment: A Case Study of the Fast-Food Industry in New Jersey and
Pennsylvania.* American Economic Review, 84(4), 772–793.

## Research question

Does raising the minimum wage reduce employment? The paper exploits a natural
experiment: on April 1, 1992, New Jersey raised its minimum wage from $4.25 to
$5.05 per hour, while neighboring Pennsylvania kept it at $4.25. The empirical
strategy is a difference-in-differences (DiD) design comparing fast-food
restaurants in New Jersey (treatment) and eastern Pennsylvania (control) before
and after the increase.

## Data

- **Raw data:** `data/public.csv` — a two-wave panel of 410 fast-food
  restaurants (Burger King, KFC, Roy Rogers, Wendy's).
  - Wave 1 (pre-treatment): February–March 1992.
  - Wave 2 (post-treatment): November–December 1992.
- Variables without a suffix are Wave 1; variables with a `2` suffix
  (e.g. `EMPFT2`, `WAGE_ST2`) are Wave 2.

## Repository structure

```
.
├── data/          # raw data (public.csv)
├── scripts/       # Python analysis pipeline
├── processed/     # processed datasets (generated)
├── output/        # tables and figures (generated)
├── report/        # empirical report
└── README.md
```

## Environment

- Python 3.14 with `pandas`, `numpy`, `statsmodels`, `matplotlib`, `seaborn`,
  `scipy`.
- A virtual environment (`.venv/`) is used locally and is excluded from git.

## Reproduce

*Instructions will be finalized here once the pipeline is complete.*

## Status

- [x] Project scaffolding and data import
- [ ] Sample construction and variable definitions
- [ ] Replication of main tables (DiD on wages and employment)
- [ ] Comparison with original paper
- [ ] Independent extension

# ECON6067 Individual Project — Replication of Card & Krueger (1994)

**Paper replicated:** Card, D., & Krueger, A. B. (1994). *Minimum Wages and
Employment: A Case Study of the Fast-Food Industry in New Jersey and
Pennsylvania.* American Economic Review, 84(4), 772–793.

## Research question

Does raising the minimum wage reduce employment? On April 1, 1992, New Jersey
raised its minimum wage from $4.25 to $5.05 while neighbouring Pennsylvania kept
it at $4.25. This project replicates the paper's difference-in-differences (DiD)
estimate of the employment effect, compares it with the original, and adds an
independent extension on ownership heterogeneity.

## Results (summary)

| Estimate | This replication | Original paper |
|---|---|---|
| **FTE employment DiD (Table 3)** | **+2.75 (SE 1.34)** | **+2.76 (SE 1.36)** |

The full write-up is in `report.pdf`.

## Repository structure

```
.
├── data/
│   ├── raw/               # original input data (public.csv)
│   └── processed/         # constructed analysis data
├── code/                  # analysis code
│   ├── run_all.py         # single self-contained workflow (all analysis)
│   └── 01_explore_data.py # standalone data-exploration script
├── outputs/
│   ├── tables/            # generated tables
│   └── figures/           # generated figures
├── skills/
│   └── SKILL.md           # reusable skill that regenerates tables & figures
├── report.pdf             # final research report
├── AI_USE_DISCLOSURE.md
├── requirements.txt
└── README.md
```

## Reproduce

Requirements: Python 3.14 (macOS/Linux). From the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -I code/run_all.py
```

`code/run_all.py` is a single self-contained script: it constructs the analysis
sample, reproduces Tables 2–4 and Figure 1, and runs the extension and
robustness checks — all in one file, with no other scripts
required. Running it regenerates every table (`outputs/tables/`) and figure
(`outputs/figures/`) from `data/raw/` without any manual editing. Its four
stages are:

1. `build_sample()` — construct FTE, starting wage, treatment indicator
2. `replicate()` — Table 2 (Means of Key Variables), Table 3 (Employment DiD),
   Table 4 (Reduced-Form Models), and Figure 1 (wage distribution)
3. `extension()` — ownership-heterogeneity extension
4. `robustness()` — robustness to controls

`code/01_explore_data.py` is a standalone data-exploration script (not part of
the output-producing pipeline).

## Data

- **Raw data:** `data/raw/public.csv` — two-wave panel of 410 fast-food restaurants.
  - Wave 1 (pre-treatment): February–March 1992.
  - Wave 2 (post-treatment): November–December 1992.
- Variables without a suffix are Wave 1; variables with a `2` suffix are Wave 2.
- This is public survey data (Card & Krueger 1994); no restricted data is included.

---
name: card-krueger-replication
description: Regenerate the Card & Krueger (1994) minimum-wage DiD replication tables and figures from data/raw/public.csv. Run this skill whenever the analysis outputs need to be (re)produced.
---

# Card & Krueger (1994) Replication Skill

This skill regenerates every table and figure for the Card & Krueger (1994)
minimum-wage replication directly from the raw survey data. It is the single,
reusable entry point for reproducing the project's results.

## Prerequisites

- Python 3.14 with the packages pinned in `requirements.txt`.
- Raw data at `data/raw/public.csv` (410 fast-food restaurants, two-wave panel).

## One-time setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Regenerate all outputs

```bash
.venv/bin/python -I code/run_all.py
```

`code/run_all.py` runs the pipeline in order and writes:

- `data/processed/wide.csv`, `data/processed/panel.csv` — constructed data
- `outputs/tables/*.csv` — replicated tables
- `outputs/figures/*.png` — Figure 1 (wage-distribution histogram)

## Pipeline

All analysis code lives in a single script, `code/run_all.py`, which runs four
stages in order:

| Function | What it produces |
|---|---|
| `build_sample()` | FTE employment, starting wage, NJ treatment indicator |
| `replicate()` | Table 2 (Means), Table 3 (Employment DiD), Table 4 (Reduced-Form), Table 5 (Wage DiD), Figure 1 (wage distribution) |
| `extension()` | Ownership-heterogeneity extension |
| `robustness()` | Robustness to controls |

`code/01_explore_data.py` is a standalone data-exploration script (not part of
the output-producing pipeline).

## Validation notes

- `FTE = full-time + 0.5*part-time + managers`; verified against the paper's
  Wave-1 means (NJ 20.44 / PA 23.33).
- `STATE == 1` is New Jersey (treatment); `STATE == 0` is Pennsylvania (control).
- `SHEET` is not a unique store id (number 407 labels two stores); the row index
  is used instead.

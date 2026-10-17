# Raw data

The original survey data `public.csv` — the Card & Krueger (1994) fast-food
panel (410 restaurants × 46 columns, two waves) — is **not uploaded** to this
repository, per course policy.

To reproduce the results, obtain the file and place it at this exact path:

    data/raw/public.csv

then run the pipeline from the project root (see `../skills/SKILL.md`):

    .venv/bin/python -I code/run_all.py

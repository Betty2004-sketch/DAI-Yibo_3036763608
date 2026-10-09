"""
Reusable workflow — regenerate all processed data, tables, and figures.

Run from the project root:
    .venv/bin/python -I code/run_all.py

This is the single entry point required by the reproducibility package: with
the raw data in data/raw/, it reproduces the assigned tables (Table 2, 3, 4)
and figure (Figure 1) plus the extension and robustness results, without any
manual editing of data or code.
"""
import subprocess
import sys

STEPS = [
    "code/02_build_sample.py",        # construct FTE / wage / treatment
    "code/03_paper_replication.py",   # Table 2, 3, 4 and Figure 1 (paper format)
    "code/04_extension.py",           # ownership heterogeneity
    "code/05_robustness.py",          # robustness to controls
]

for step in STEPS:
    print(f"\n{'=' * 70}\n>>> {step}\n{'=' * 70}")
    subprocess.run([sys.executable, "-I", step], check=True)

print("\nDone. All outputs in data/processed/ and outputs/ are up to date.")

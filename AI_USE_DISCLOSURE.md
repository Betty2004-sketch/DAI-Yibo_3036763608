# AI-Use Disclosure

This project used Claude (an AI coding/analysis assistant) throughout the
workflow. Every data choice, method, validation check, interpretation, and
conclusion was reviewed and approved by the author.

## Where and how AI was used

1. **Understanding the paper.** AI summarized Card & Krueger (1994): the
   research question, the natural-experiment design, and the DiD estimator.
2. **Data exploration.** AI wrote and ran `code/01_explore_data.py` to
   inspect the 46 columns, missingness, and treatment/control composition.
3. **Analysis code.** AI wrote the single self-contained workflow
   `code/run_all.py`, which builds FTE employment
   (`FTE = full-time + 0.5*part-time + managers`), the starting wage, and the
   NJ treatment indicator (`build_sample()`); reproduces Table 2 (means of key
   variables), Table 3 (employment DiD), Table 4 (reduced-form models), and
   Figure 1 (wage distribution) (`replicate()`); implements
   the ownership-heterogeneity extension (`extension()`); and runs the robustness
   checks (`robustness()`).
4. **Packaging.** AI wrote the README, the reusable skill (`skills/SKILL.md`),
   and this disclosure.

## How AI-generated work was checked

- **Exact-value validation.** The FTE formula and STATE coding were verified by
  matching the computed Wave-1 means to the paper's published numbers
  (NJ FTE 20.44, PA FTE 23.33; NJ wage 4.61, PA wage 4.63) — an exact match.
- **Replication comparison.** The DiD estimate was compared to the paper's
  Table 3 (+2.76 employment); ours is +2.75.
- **Manual review.** Every script's output was read and sanity-checked; the
  report numbers were re-derived from the saved CSVs, not copied from chat.

## AI errors that were corrected or rejected

- **Collinearity bug in the robustness check.** An early specification added
  NJ-region dummies (`SOUTHJ`/`CENTRALJ`/`NORTHJ`) alongside the NJ treatment
  indicator, making the design matrix rank-deficient and the DiD coefficient
  unidentified. This was detected from a `SingularMatrixWarning`, diagnosed as
  perfect collinearity (the three region dummies sum to the treatment dummy),
  and fixed by replacing them with non-collinear controls (chain FE, ownership,
  hours, and prices).
- **Duplicate `SHEET` identifier.** AI initially treated `SHEET` as the store
  id but found one number (407) labels two different restaurants; the row index
  was used instead and the issue documented as a data-validation note.
- **Overly long explanations.** The author asked AI to reduce explanation and
  proceed directly with the analysis; this preference was applied.

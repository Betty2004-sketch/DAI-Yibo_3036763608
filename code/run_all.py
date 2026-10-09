"""
Reusable workflow — regenerate all processed data, tables, and figures.

Run from the project root:
    .venv/bin/python -I code/run_all.py

Single entry point: constructs the analysis sample from the raw data, reproduces
the assigned tables (Table 2, 3, 4) and figure (Figure 1), and runs the
extension and robustness results — without any manual editing of data or code.
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# Step 1 — build the analysis sample (merged from code/02_build_sample.py)
# --------------------------------------------------------------------------
def build_sample():
    """Construct FTE / wage / treatment variables and save wide + panel data.

    FTE definition (Card & Krueger 1994): FTE = full-time + 0.5*part-time + managers.
    Prints the wave-1 means so the definition can be checked against the paper's
    Table 3/4 (NJ FTE ~20.44, PA ~23.33; NJ wage ~4.61, PA ~4.63).
    """
    RAW = "data/raw/public.csv"
    df = pd.read_csv(RAW)

    # store id: SHEET is NOT unique (number 407 labels two restaurants),
    # so use the row position as the store identifier
    df = df.reset_index().rename(columns={"index": "store_id"})

    # treatment indicator: STATE == 1 -> NJ (treated), 0 -> PA (control)
    df["treated"] = (df["STATE"] == 1).astype(int)

    # full-time-equivalent employment
    df["fte1"] = df["EMPFT"] + 0.5 * df["EMPPT"] + df["NMGRS"]
    df["fte2"] = df["EMPFT2"] + 0.5 * df["EMPPT2"] + df["NMGRS2"]

    # starting wage
    df["wage1"] = df["WAGE_ST"]
    df["wage2"] = df["WAGE_ST2"]

    # first differences (DiD building blocks)
    df["d_fte"] = df["fte2"] - df["fte1"]
    df["d_wage"] = df["wage2"] - df["wage1"]

    df.to_csv("data/processed/wide.csv", index=False)

    id_cols = ["store_id", "treated", "STATE", "CHAIN", "CO_OWNED",
               "SOUTHJ", "CENTRALJ", "NORTHJ", "PA1", "PA2", "SHORE"]
    long = pd.concat([
        df[id_cols + ["fte1", "wage1"]].rename(columns={"fte1": "fte", "wage1": "wage"}).assign(wave=1),
        df[id_cols + ["fte2", "wage2"]].rename(columns={"fte2": "fte", "wage2": "wage"}).assign(wave=2),
    ], ignore_index=True)
    long.to_csv("data/processed/panel.csv", index=False)

    # verification against the paper's published wave-1 means
    print("=" * 70)
    print("验证：我们的变量是否与论文的已知数值对上")
    print("=" * 70)
    print()
    print("Wave-1 FTE employment by state (论文: NJ≈20.44, PA≈23.33):")
    print(df.groupby("STATE")["fte1"].mean().round(2).to_string())
    print()
    print("Wave-1 starting wage by state (论文: NJ≈4.61, PA≈4.63):")
    print(df.groupby("STATE")["wage1"].mean().round(2).to_string())
    print()
    print("平衡样本规模（两波都有该变量）:")
    print(f"  FTE 平衡样本:  {df['d_fte'].notna().sum()}  家")
    print(f"  起薪平衡样本:  {df['d_wage'].notna().sum()}  家")
    print()
    print("FTE 平衡样本按州分组:")
    print(df[df["d_fte"].notna()].groupby("STATE").size().to_string())


# --------------------------------------------------------------------------
# Step 2 — replicate the core tables and figure (merged from code/03_paper_replication.py)
# --------------------------------------------------------------------------
def replicate():
    """Reproduce Table 2, Table 3, Table 4, and Figure 1 in the paper's format.

    Column layout for Tables 3 and 4 follows the paper exactly:
      Pennsylvania | New Jersey | Difference (NJ - PA)
    with rows Wave 1 (before) / Wave 2 (after) / Change. As in the paper,
    "Change" is the difference of the (full-sample) wave means, and the DiD is
    the NJ-minus-PA difference of those changes.
    """
    df = pd.read_csv("data/processed/wide.csv")
    os.makedirs("outputs/tables", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

    def did_block(v1, v2):
        g1 = df.groupby("STATE")[v1]           # wave 1 (before)
        g2 = df.groupby("STATE")[v2]           # wave 2 (after)
        m1, s1, n1 = g1.mean(), g1.std(), g1.count()
        m2, s2, n2 = g2.mean(), g2.std(), g2.count()
        se1 = s1 / np.sqrt(n1)
        se2 = s2 / np.sqrt(n2)

        # Change = difference of the (full-sample) wave means, as in the paper.
        change = m2 - m1

        # SE of the change: std of store-level changes / sqrt(n) on the balanced panel
        d = df.dropna(subset=[v1, v2]).copy()
        d["ch"] = d[v2] - d[v1]
        chg = d.groupby("STATE")["ch"].agg(["std", "count"])
        se_change = chg["std"] / np.sqrt(chg["count"])
        n_bal = chg["count"]

        # DiD = NJ change - PA change; SE = sqrt(se_NJ^2 + se_PA^2)
        did = change[1] - change[0]
        se_did = np.sqrt(se_change[1] ** 2 + se_change[0] ** 2)

        diff1, se_diff1 = m1[1] - m1[0], np.sqrt(se1[1] ** 2 + se1[0] ** 2)
        diff2, se_diff2 = m2[1] - m2[0], np.sqrt(se2[1] ** 2 + se2[0] ** 2)

        return {
            "m1": m1, "m2": m2, "se1": se1, "se2": se2,
            "change": change, "se_change": se_change, "n_bal": n_bal,
            "did": did, "se_did": se_did,
            "diff1": diff1, "se_diff1": se_diff1, "diff2": diff2, "se_diff2": se_diff2,
        }

    def paper_table(blocks, title):
        lines = []
        lines.append("=" * 78)
        lines.append(title)
        lines.append("=" * 78)
        lines.append(f"{'':28s}{'Pennsylvania':>15s}{'New Jersey':>14s}{'Difference (NJ-PA)':>20s}")
        for label, b in blocks:
            lines.append(f"{label}")
            lines.append(f"  Wave 1 (before)   {b['m1'][0]:>12.2f} ({b['se1'][0]:.2f})"
                         f"{b['m1'][1]:>11.2f} ({b['se1'][1]:.2f})"
                         f"{b['diff1']:>15.2f} ({b['se_diff1']:.2f})")
            lines.append(f"  Wave 2 (after)    {b['m2'][0]:>12.2f} ({b['se2'][0]:.2f})"
                         f"{b['m2'][1]:>11.2f} ({b['se2'][1]:.2f})"
                         f"{b['diff2']:>15.2f} ({b['se_diff2']:.2f})")
            lines.append(f"  Change            {b['change'][0]:>12.2f} ({b['se_change'][0]:.2f})"
                         f"{b['change'][1]:>11.2f} ({b['se_change'][1]:.2f})"
                         f"{b['did']:>15.2f} ({b['se_did']:.2f})")
        lines.append("-" * 78)
        print("\n".join(lines), "\n")
        return lines

    # --- Table 3 ----------------------------------------------------------
    wage = did_block("wage1", "wage2")
    paper_table([("Starting wage ($/hr)", wage)], "TABLE 3 — Changes in Wages (DiD)")

    # --- Table 4 ----------------------------------------------------------
    fte = did_block("fte1", "fte2")
    ft = did_block("EMPFT", "EMPFT2")
    pt = did_block("EMPPT", "EMPPT2")
    mg = did_block("NMGRS", "NMGRS2")
    paper_table([
        ("FTE employment", fte),
        ("Full-time workers", ft),
        ("Part-time workers", pt),
        ("Managers", mg),
    ], "TABLE 4 — Changes in Employment (DiD)")

    def block_rows(b):
        return {
            "Wave 1 PA": b["m1"][0], "Wave 1 NJ": b["m1"][1],
            "Wave 2 PA": b["m2"][0], "Wave 2 NJ": b["m2"][1],
            "Change PA": b["change"][0], "Change NJ": b["change"][1],
            "DiD": b["did"], "SE_DiD": b["se_did"],
            "n_bal_PA": b["n_bal"][0], "n_bal_NJ": b["n_bal"][1],
        }

    pd.DataFrame([block_rows(wage)]).to_csv("outputs/tables/table3_wage_did.csv", index=False)
    pd.DataFrame([
        {"measure": "FTE", **block_rows(fte)},
        {"measure": "Full-time", **block_rows(ft)},
        {"measure": "Part-time", **block_rows(pt)},
        {"measure": "Managers", **block_rows(mg)},
    ]).to_csv("outputs/tables/table4_employment_did.csv", index=False)

    # --- Table 2 ----------------------------------------------------------
    edges = [0, 4.00, 4.25, 4.50, 4.75, 5.00, 5.05, 5.50, 6.00, np.inf]
    labels = ["<4.00", "4.00-4.24", "4.25", "4.26-4.50",
              "4.51-4.75", "4.76-5.00", "5.05", "5.06-5.50", ">5.50"]

    def dist_col(s):
        c = pd.cut(s, bins=edges, labels=labels, right=False).dropna()
        return c.value_counts(normalize=True).reindex(labels).fillna(0) * 100

    t2 = pd.DataFrame({
        "Wage bin": labels,
        "NJ wave1": dist_col(df["wage1"][df["STATE"] == 1]),
        "PA wave1": dist_col(df["wage1"][df["STATE"] == 0]),
        "NJ wave2": dist_col(df["wage2"][df["STATE"] == 1]),
        "PA wave2": dist_col(df["wage2"][df["STATE"] == 0]),
    })
    t2.to_csv("outputs/tables/table2_wage_distribution.csv", index=False)
    print("TABLE 2 — Distribution of starting wage rates (percent of stores)")
    print("=" * 78)
    print(t2.to_string(index=False, float_format=lambda x: f"{x:5.1f}"))
    print()

    # --- Figure 1 ---------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=200)
    bins = np.arange(3.25, 7.55, 0.10)
    for ax, (wv, title) in zip(axes, [("wage1", "Wave 1 (Feb–Mar 1992)"),
                                      ("wage2", "Wave 2 (Nov–Dec 1992)")]):
        ax.hist(df.loc[df["STATE"] == 1, wv].dropna(), bins=bins, alpha=0.6,
                color="#2e5a87", label="New Jersey", density=True)
        ax.hist(df.loc[df["STATE"] == 0, wv].dropna(), bins=bins, alpha=0.6,
                color="#c9a86a", label="Pennsylvania", density=True)
        ax.axvline(4.25, color="gray", ls="--", lw=1)
        if wv == "wage2":
            ax.axvline(5.05, color="#a33a2b", ls="--", lw=1)
            ax.text(5.05, ax.get_ylim()[1] * 0.9, "$5.05", color="#a33a2b", ha="left")
        ax.set_title(title)
        ax.set_xlabel("Starting wage ($/hour)")
        ax.set_ylabel("Density")
        ax.legend(frameon=False, fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Figure 1 — Distribution of Starting Wage Rates", fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig("outputs/figures/figure1_wage_distribution.png", bbox_inches="tight")
    print("Saved outputs/figures/figure1_wage_distribution.png")


# --------------------------------------------------------------------------
# Step 3 — ownership-heterogeneity extension (merged from code/04_extension.py)
# --------------------------------------------------------------------------
def extension():
    """Estimate the employment DiD separately for franchise vs company-owned stores."""
    df = pd.read_csv("data/processed/wide.csv")
    os.makedirs("outputs/tables", exist_ok=True)

    def subgroup_did(mask, var1, var2):
        d = df[mask].dropna(subset=[var1, var2])
        d["ch"] = d[var2] - d[var1]
        nj = d[d["STATE"] == 1]["ch"]
        pa = d[d["STATE"] == 0]["ch"]
        return nj.mean(), pa.mean(), nj.mean() - pa.mean(), len(nj), len(pa)

    print("=" * 70)
    print("扩展：按门店所有权分组的 DiD（结果变量 = FTE 就业变化）")
    print("=" * 70)
    print()

    for co, label in [(0, "加盟店 franchise (CO_OWNED=0)"),
                      (1, "直营店 company-owned (CO_OWNED=1)")]:
        m = df["CO_OWNED"] == co
        nj_ch, pa_ch, did, n_nj, n_pa = subgroup_did(m, "fte1", "fte2")
        print(f"{label}:")
        print(f"   NJ 变化 = {nj_ch:+.2f}  (n={n_nj})")
        print(f"   PA 变化 = {pa_ch:+.2f}  (n={n_pa})")
        print(f"   DiD     = {did:+.2f}")
        print()

    d = df.dropna(subset=["fte1", "fte2"]).copy()
    d["ch"] = d["fte2"] - d["fte1"]
    d["treated_x_co"] = d["treated"] * d["CO_OWNED"]

    X = sm.add_constant(d[["treated", "CO_OWNED", "treated_x_co"]])
    res = sm.OLS(d["ch"], X).fit(cov_type="HC1")

    print("交互项回归： ch_FTE ~ NJ + CO_OWNED + NJ*CO_OWNED")
    print(res.summary().tables[1].as_text())
    print()

    delta_fr = res.params["treated"]
    gamma = res.params["treated_x_co"]
    delta_co = delta_fr + gamma

    vcov = res.cov_params()
    se_co = np.sqrt(vcov.loc["treated", "treated"]
                    + vcov.loc["treated_x_co", "treated_x_co"]
                    + 2 * vcov.loc["treated", "treated_x_co"])

    print("解读：")
    print(f"  加盟店 DiD        (NJ)      = {delta_fr:+.2f}  (SE {res.bse['treated']:.2f})")
    print(f"  直营店 DiD        (NJ+交互) = {delta_co:+.2f}  (SE {se_co:.2f})")
    print(f"  所有权差异 (交互项)          = {gamma:+.2f}  (SE {res.bse['treated_x_co']:.2f}, "
          f"p={res.pvalues['treated_x_co']:.3f})")
    print()

    out = pd.DataFrame({
        "group": ["franchise", "company-owned"],
        "NJ_change": [subgroup_did(df["CO_OWNED"] == 0, "fte1", "fte2")[0],
                      subgroup_did(df["CO_OWNED"] == 1, "fte1", "fte2")[0]],
        "PA_change": [subgroup_did(df["CO_OWNED"] == 0, "fte1", "fte2")[1],
                      subgroup_did(df["CO_OWNED"] == 1, "fte1", "fte2")[1]],
        "DiD": [subgroup_did(df["CO_OWNED"] == 0, "fte1", "fte2")[2],
                subgroup_did(df["CO_OWNED"] == 1, "fte1", "fte2")[2]],
    })
    out.to_csv("outputs/tables/extension_ownership.csv", index=False)


# --------------------------------------------------------------------------
# Step 4 — robustness checks (merged from code/05_robustness.py)
# --------------------------------------------------------------------------
def robustness():
    """Estimate the employment DiD under progressively richer specifications."""
    df = pd.read_csv("data/processed/wide.csv")
    os.makedirs("outputs/tables", exist_ok=True)

    def fit(formula, data):
        r = smf.ols(formula, data=data).fit(cov_type="HC1")
        return r.params["treated"], r.bse["treated"], int(r.nobs)

    # (0) baseline on the full balanced sample -- same as the Table 4 DiD
    d_full = df.dropna(subset=["fte1", "fte2"]).copy()
    d_full["ch"] = d_full["fte2"] - d_full["fte1"]

    # control-complete sample, fixed across specifications (1)-(3).
    # Note: NJ-region dummies (SOUTHJ/CENTRALJ/NORTHJ) are omitted on purpose --
    # they are collinear with `treated` and would absorb the treatment effect.
    d = df.dropna(subset=["fte1", "fte2", "CHAIN", "CO_OWNED", "HRSOPEN",
                          "PSODA", "PFRY", "PENTREE"]).copy()
    d["ch"] = d["fte2"] - d["fte1"]

    rows = []
    est, se, n = fit("ch ~ treated", d_full)
    rows.append({"spec": "(0) baseline (full Table 4 sample)", "DiD": est, "SE": se, "n": n})

    specs = [
        ("(1) baseline (control-complete sample)", "ch ~ treated"),
        ("(2) + chain FE", "ch ~ treated + C(CHAIN)"),
        ("(3) + chain FE + ownership + hours + prices",
         "ch ~ treated + C(CHAIN) + CO_OWNED + HRSOPEN + PSODA + PFRY + PENTREE"),
    ]
    for name, formula in specs:
        est, se, n = fit(formula, d)
        rows.append({"spec": name, "DiD": est, "SE": se, "n": n})

    print("稳健性检验：不同设定下 NJ 的 DiD 系数（结果变量 = FTE 变化）")
    print("=" * 74)
    for r in rows:
        print(f"{r['spec']:46s}  DiD = {r['DiD']:+6.3f}  (SE {r['SE']:.3f}, n={r['n']})")

    pd.DataFrame(rows).to_csv("outputs/tables/robustness.csv", index=False)


def main():
    print("\n" + "=" * 70)
    print(">>> build_sample (inline)")
    print("=" * 70)
    build_sample()

    print("\n" + "=" * 70)
    print(">>> replicate (inline)")
    print("=" * 70)
    replicate()

    print("\n" + "=" * 70)
    print(">>> extension (inline)")
    print("=" * 70)
    extension()

    print("\n" + "=" * 70)
    print(">>> robustness (inline)")
    print("=" * 70)
    robustness()

    print("\nDone. All outputs in data/processed/ and outputs/ are up to date.")


if __name__ == "__main__":
    main()

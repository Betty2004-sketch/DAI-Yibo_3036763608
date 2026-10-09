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
# Step 1 — build the analysis sample
# --------------------------------------------------------------------------
def build_sample():
    """Construct FTE / wage / treatment variables and save wide + panel data.

    FTE definition (Card & Krueger 1994): FTE = full-time + 0.5*part-time + managers.
    Prints the wave-1 means so the definition can be checked against the paper's
    Table 2 (NJ FTE ~20.44, PA ~23.33; NJ wage ~4.61, PA ~4.63).
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

    # GAP: proportional wage increase needed to reach the $5.05 minimum
    # (NJ stores only; PA stores and NJ stores already at/above $5.05 = 0)
    df["gap"] = np.where((df["STATE"] == 1) & (df["WAGE_ST"] < 5.05),
                         (5.05 - df["WAGE_ST"]) / df["WAGE_ST"], 0.0)

    # price of a full meal = soda + fries + entree
    df["meal1"] = df["PSODA"] + df["PFRY"] + df["PENTREE"]
    df["meal2"] = df["PSODA2"] + df["PFRY2"] + df["PENTREE2"]

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
# Step 2 — replicate the core tables and figure
# --------------------------------------------------------------------------
def replicate():
    """Reproduce Table 2, Table 3, Table 4, Table 5, and Figure 1.

    Paper layout (Card & Krueger 1994):
      Table 2  = Means of Key Variables (store types + wave-1/2 means)
      Table 3  = Average Employment per Store Before/After (FTE, DiD)
      Table 4  = Reduced-Form Models for Change in Employment (5 regressions)
      Table 5  = Reduced-Form Models for Change in Wages (wage DiD)
      Figure 1 = Distribution of Wage Rate (2 waves x 2 states)

    Table 3 reproduces the paper's FTE-only layout: columns for Pennsylvania,
    New Jersey, the NJ-PA difference, three NJ starting-wage groups, and the
    low-high / mid-high contrasts; rows for before, after, the (unbalanced)
    change, the balanced-sample change, and the change treating temporarily
    closed stores as zero.
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

    # --- Table 2: Means of Key Variables --------------------------------
    CHAIN_NAMES = {1: "Burger King", 2: "KFC", 3: "Roy Rogers", 4: "Wendy's"}
    nj_mask = df["STATE"] == 1
    pa_mask = df["STATE"] == 0

    # percentage full-time employees = store-level mean of 100 * EMPFT / FTE
    df["pctft1"] = 100 * df["EMPFT"] / df["fte1"]
    df["pctft2"] = 100 * df["EMPFT2"] / df["fte2"]

    def t2_row(panel, label, nj_vals, pa_vals):
        m1, m2 = nj_vals.mean(), pa_vals.mean()
        se = np.sqrt(nj_vals.var(ddof=1) / nj_vals.notna().sum()
                     + pa_vals.var(ddof=1) / pa_vals.notna().sum())
        t = (m1 - m2) / se if se > 0 else np.nan
        return [panel, label, m1, m2, t]

    t2 = []
    for c in [1, 2, 3, 4]:
        t2.append(t2_row("A. Store types (%)", CHAIN_NAMES[c],
                         100 * (df.loc[nj_mask, "CHAIN"] == c).astype(int),
                         100 * (df.loc[pa_mask, "CHAIN"] == c).astype(int)))
    t2.append(t2_row("A. Store types (%)", "Company-owned",
                     100 * df.loc[nj_mask, "CO_OWNED"],
                     100 * df.loc[pa_mask, "CO_OWNED"]))

    t2.append(t2_row("B. Wave 1 means", "FTE employment",
                     df.loc[nj_mask, "fte1"], df.loc[pa_mask, "fte1"]))
    t2.append(t2_row("B. Wave 1 means", "Percentage full-time employees",
                     df.loc[nj_mask, "pctft1"], df.loc[pa_mask, "pctft1"]))
    t2.append(t2_row("B. Wave 1 means", "Starting wage ($/hr)",
                     df.loc[nj_mask, "wage1"], df.loc[pa_mask, "wage1"]))
    t2.append(t2_row("B. Wave 1 means", "Wage = $4.25 (%)",
                     100 * (df.loc[nj_mask, "wage1"] == 4.25).astype(int),
                     100 * (df.loc[pa_mask, "wage1"] == 4.25).astype(int)))
    t2.append(t2_row("B. Wave 1 means", "Price of full meal ($)",
                     df.loc[nj_mask, "meal1"], df.loc[pa_mask, "meal1"]))
    t2.append(t2_row("B. Wave 1 means", "Hours open (weekday)",
                     df.loc[nj_mask, "HRSOPEN"], df.loc[pa_mask, "HRSOPEN"]))
    t2.append(t2_row("B. Wave 1 means", "Recruiting bonus (%)",
                     100 * df.loc[nj_mask, "BONUS"], 100 * df.loc[pa_mask, "BONUS"]))

    t2.append(t2_row("C. Wave 2 means", "FTE employment",
                     df.loc[nj_mask, "fte2"], df.loc[pa_mask, "fte2"]))
    t2.append(t2_row("C. Wave 2 means", "Percentage full-time employees",
                     df.loc[nj_mask, "pctft2"], df.loc[pa_mask, "pctft2"]))
    t2.append(t2_row("C. Wave 2 means", "Starting wage ($/hr)",
                     df.loc[nj_mask, "wage2"], df.loc[pa_mask, "wage2"]))
    t2.append(t2_row("C. Wave 2 means", "Wage = $4.25 (%)",
                     100 * (df.loc[nj_mask, "wage2"] == 4.25).astype(int),
                     100 * (df.loc[pa_mask, "wage2"] == 4.25).astype(int)))
    t2.append(t2_row("C. Wave 2 means", "Wage = $5.05 (%)",
                     100 * (df.loc[nj_mask, "wage2"] == 5.05).astype(int),
                     100 * (df.loc[pa_mask, "wage2"] == 5.05).astype(int)))
    t2.append(t2_row("C. Wave 2 means", "Price of full meal ($)",
                     df.loc[nj_mask, "meal2"], df.loc[pa_mask, "meal2"]))
    t2.append(t2_row("C. Wave 2 means", "Hours open (weekday)",
                     df.loc[nj_mask, "HRSOPEN2"], df.loc[pa_mask, "HRSOPEN2"]))
    t2.append(t2_row("C. Wave 2 means", "Recruiting bonus (%)",
                     100 * df.loc[nj_mask, "SPECIAL2"],
                     100 * df.loc[pa_mask, "SPECIAL2"]))

    t2_df = pd.DataFrame(t2, columns=["Panel", "Variable", "NJ", "PA", "t"])
    t2_df.to_csv("outputs/tables/table2_means_key_variables.csv", index=False)
    print("TABLE 2 — Means of Key Variables")
    print("=" * 78)
    print(t2_df.to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
    print()

    # --- Table 3: Average Employment per Store (FTE, DiD) ----------------
    def wave_mean(v, state):
        s = df.loc[df["STATE"] == state, v].dropna()
        return s.mean(), s.std() / np.sqrt(len(s)), len(s)

    def bal_change(state, data=None):
        d = (df if data is None else data)
        d = d[d["STATE"] == state].dropna(subset=["fte1", "fte2"]).copy()
        d["ch"] = d["fte2"] - d["fte1"]
        return d["ch"].mean(), d["ch"].std() / np.sqrt(len(d)), len(d)

    def nj_grp(data):
        x = data[data["STATE"] == 1].copy()
        # classify only stores with a reported wave-1 starting wage
        x = x.dropna(subset=["wage1"])
        x["wg"] = np.select([x["wage1"] == 4.25, x["wage1"] < 5.00],
                            ["low", "mid"], default="high")
        return x

    def grp_means(data, v=None, method="all"):
        x = nj_grp(data)
        out = {}
        for g in ["low", "mid", "high"]:
            s = x[x["wg"] == g]
            if method == "bal":
                s = s.dropna(subset=["fte1", "fte2"]).copy()
                s["ch"] = s["fte2"] - s["fte1"]
                out[g] = s["ch"].mean()
            else:
                out[g] = s[v].mean()
        return out

    pa_b, se_pa_b, _ = wave_mean("fte1", 0)
    nj_b, se_nj_b, _ = wave_mean("fte1", 1)
    pa_a, se_pa_a, _ = wave_mean("fte2", 0)
    nj_a, se_nj_a, _ = wave_mean("fte2", 1)
    pa_bc, se_pa_bc, n_pa_bc = bal_change(0)
    nj_bc, se_nj_bc, n_nj_bc = bal_change(1)
    did_bal = nj_bc - pa_bc
    se_did_bal = np.sqrt(se_nj_bc ** 2 + se_pa_bc ** 2)

    # row 5: wave-2 employment at temporarily closed stores set to zero
    df5 = df.copy()
    df5.loc[df5["STATUS2"].isin([0, 2, 4, 5]), "fte2"] = 0.0
    pa_tc, se_pa_tc, _ = bal_change(0, data=df5)
    nj_tc, se_nj_tc, _ = bal_change(1, data=df5)

    b_all = grp_means(df, "fte1")
    a_all = grp_means(df, "fte2")
    c_unbal = {g: a_all[g] - b_all[g] for g in ["low", "mid", "high"]}
    c_bal = grp_means(df, method="bal")
    c_tc = grp_means(df5, method="bal")

    def t3_row(label, pa, nj, diff, g_low, g_mid, g_high):
        return [label, pa, nj, diff, g_low, g_mid, g_high,
                g_low - g_high, g_mid - g_high]

    t3 = [
        t3_row("1. FTE before, all obs", pa_b, nj_b, nj_b - pa_b,
               b_all["low"], b_all["mid"], b_all["high"]),
        t3_row("2. FTE after, all obs", pa_a, nj_a, nj_a - pa_a,
               a_all["low"], a_all["mid"], a_all["high"]),
        t3_row("3. Change in mean FTE", pa_a - pa_b, nj_a - nj_b,
               (nj_a - nj_b) - (pa_a - pa_b),
               c_unbal["low"], c_unbal["mid"], c_unbal["high"]),
        t3_row("4. Change, balanced sample", pa_bc, nj_bc, did_bal,
               c_bal["low"], c_bal["mid"], c_bal["high"]),
        t3_row("5. Change, temporarily closed -> 0", pa_tc, nj_tc, nj_tc - pa_tc,
               c_tc["low"], c_tc["mid"], c_tc["high"]),
    ]
    t3_df = pd.DataFrame(t3, columns=[
        "Row", "PA", "NJ", "Diff (NJ-PA)",
        "Low ($4.25)", "Mid ($4.26-4.99)", "High (>= $5.00)",
        "Low - High", "Mid - High"])
    t3_df.to_csv("outputs/tables/table3_employment_did.csv", index=False)

    print("TABLE 3 — Average Employment per Store Before/After (FTE)")
    print("=" * 78)
    print(t3_df.round(2).to_string(index=False))
    print()
    print(f"  Balanced-sample DiD = {did_bal:+.2f} (SE {se_did_bal:.2f}, "
          f"t = {did_bal / se_did_bal:.2f})")
    print(f"  Balanced sample: NJ n = {n_nj_bc}, PA n = {n_pa_bc}")
    print(f"  NJ by starting wage (balanced change): "
          f"low {c_bal['low']:+.2f}, mid {c_bal['mid']:+.2f}, high {c_bal['high']:+.2f}")
    print()

    # --- Table 4: Reduced-Form Models for Change in Employment ----------
    # Sample = stores with employment in both waves and a wave-1 starting wage
    # (the paper uses n = 357; the public dataset yields n = 365 below). Standard
    # errors are the ordinary (homoskedastic) OLS errors, as in the paper.
    d4 = df.dropna(subset=["fte1", "fte2", "WAGE_ST"]).copy()
    d4["ch"] = d4["fte2"] - d4["fte1"]

    # Restrictions for the joint F test that all control variables are zero.
    chain_own = "C(CHAIN)[T.2] = 0, C(CHAIN)[T.3] = 0, C(CHAIN)[T.4] = 0, CO_OWNED = 0"
    chain_own_region = (chain_own
                        + ", SOUTHJ = 0, CENTRALJ = 0, NORTHJ = 0, PA1 = 0")

    # (coefficient key, formula, has chain+ownership, has region, F-test restrictions)
    specs4 = [
        ("treated", "ch ~ treated", False, False, None),
        ("treated", "ch ~ treated + C(CHAIN) + CO_OWNED", True, False, chain_own),
        ("gap", "ch ~ gap", False, False, None),
        ("gap", "ch ~ gap + C(CHAIN) + CO_OWNED", True, False, chain_own),
        ("gap", "ch ~ gap + C(CHAIN) + CO_OWNED + SOUTHJ + CENTRALJ + NORTHJ + PA1",
         True, True, chain_own_region),
    ]
    results4 = []
    for key, formula, chain, region, restr in specs4:
        r = smf.ols(formula, data=d4).fit()
        f_p = float(r.f_test(restr).pvalue) if restr is not None else None
        results4.append({"key": key, "coef": float(r.params[key]),
                         "se": float(r.bse[key]),
                         "ser": float(np.sqrt(r.scale)),
                         "f_p": f_p, "chain": chain, "region": region})

    def coef_cell(res, want):
        return f"{res['coef']:+.3f} ({res['se']:.3f})" if res["key"] == want else "—"

    def yes_no(res, attr):
        return "yes" if res[attr] else "no"

    rows4 = [
        ["1. New Jersey dummy"] + [coef_cell(res, "treated") for res in results4],
        ["2. Initial wage gap"] + [coef_cell(res, "gap") for res in results4],
        ["3. Controls for chain and ownership"] + [yes_no(res, "chain") for res in results4],
        ["4. Controls for region"] + [yes_no(res, "region") for res in results4],
        ["5. Standard error of regression"] + [f"{res['ser']:.3f}" for res in results4],
        ["6. Probability value for controls"]
        + [f"{res['f_p']:.3f}" if res["f_p"] is not None else "—" for res in results4],
    ]
    t4_df = pd.DataFrame(rows4, columns=["Independent variable",
                                         "(i)", "(ii)", "(iii)", "(iv)", "(v)"])
    t4_df.to_csv("outputs/tables/table4_reduced_form.csv", index=False)

    print("TABLE 4 — Reduced-Form Models for Change in Employment")
    print("=" * 78)
    print(f"Dependent variable: change in FTE employment (mean {d4['ch'].mean():.3f}, "
          f"SD {d4['ch'].std(ddof=1):.3f}); sample n = {len(d4)}")
    print(t4_df.to_string(index=False))
    print("Notes: Standard errors are given in parentheses. The sample consists of")
    print("  stores with available data on employment and starting wages in waves 1 and 2")
    print("  (n = 365 here; the paper reports n = 357). All models include an unrestricted")
    print("  constant (not reported).")
    print("  a. GAP = (5.05 - WAGE_ST)/WAGE_ST for NJ stores initially below $5.05; 0 otherwise.")
    print("  b. Three chain-type dummies plus a company-owned dummy.")
    print("  c. Dummies for NJ regions (South, Central, North) and eastern PA (PA1; PA2 is the")
    print("     omitted reference).")
    print("  d. P-value of the joint F test for exclusion of all control variables.")
    print()

    # --- Table 5: Changes in Wages (wage DiD) ---------------------------
    def block_rows(b):
        return {
            "Wave 1 PA": b["m1"][0], "Wave 1 NJ": b["m1"][1],
            "Wave 2 PA": b["m2"][0], "Wave 2 NJ": b["m2"][1],
            "Change PA": b["change"][0], "Change NJ": b["change"][1],
            "DiD": b["did"], "SE_DiD": b["se_did"],
            "n_bal_PA": b["n_bal"][0], "n_bal_NJ": b["n_bal"][1],
        }

    wage = did_block("wage1", "wage2")
    paper_table([("Starting wage ($/hr)", wage)], "TABLE 5 — Changes in Wages (DiD)")
    pd.DataFrame([block_rows(wage)]).to_csv("outputs/tables/table5_wage_did.csv", index=False)

    # --- Figure 1 ---------------------------------------------------------
    # Paper layout: 2 waves (rows) x 2 states (columns) of wage histograms.
    fig, axes = plt.subplots(2, 2, figsize=(9, 7), dpi=200)
    bins = np.arange(3.25, 7.55, 0.10)
    for r, (wv, wlabel) in enumerate([("wage1", "February 1992"),
                                      ("wage2", "November 1992")]):
        for c, (state, slabel) in enumerate([(1, "New Jersey"), (0, "Pennsylvania")]):
            ax = axes[r, c]
            ax.hist(df.loc[df["STATE"] == state, wv].dropna(), bins=bins,
                    color="#2e5a87" if state == 1 else "#c9a86a")
            ax.axvline(4.25, color="gray", ls="--", lw=1)
            if wv == "wage2":
                ax.axvline(5.05, color="#a33a2b", ls="--", lw=1)
            ax.set_title(f"{slabel} — {wlabel}", fontsize=10)
            ax.set_xlabel("Starting wage ($/hour)")
            ax.set_ylabel("Number of stores")
            ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Figure 1 — Distribution of Starting Wage Rates", fontsize=13, y=1.0)
    plt.tight_layout()
    plt.savefig("outputs/figures/figure1_wage_distribution.png", bbox_inches="tight")
    print("Saved outputs/figures/figure1_wage_distribution.png")


# --------------------------------------------------------------------------
# Step 3 — ownership-heterogeneity extension
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
# Step 4 — robustness checks
# --------------------------------------------------------------------------
def robustness():
    """Estimate the employment DiD under progressively richer specifications."""
    df = pd.read_csv("data/processed/wide.csv")
    os.makedirs("outputs/tables", exist_ok=True)

    def fit(formula, data):
        r = smf.ols(formula, data=data).fit(cov_type="HC1")
        return r.params["treated"], r.bse["treated"], int(r.nobs)

    # (0) baseline on the full balanced sample -- same as the Table 3 DiD
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
    rows.append({"spec": "(0) baseline (full Table 3 sample)", "DiD": est, "SE": se, "n": n})

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

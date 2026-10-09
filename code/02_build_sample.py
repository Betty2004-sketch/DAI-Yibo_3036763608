"""
Step 3 — Build the analysis sample and variables.

Constructs the full-time-equivalent (FTE) employment measure, the starting
wage, and the treatment indicator, then saves both a wide and a long panel.

FTE definition (Card & Krueger 1994): FTE = full-time + 0.5 * part-time + managers.
The script prints the wave-1 means so the definition can be checked against the
paper's Table 3/4 (NJ FTE ~20.44, PA ~23.33; NJ wage ~4.61, PA ~4.63).
"""
import pandas as pd

RAW = "data/raw/public.csv"

df = pd.read_csv(RAW)

# --- store id -------------------------------------------------------------
# SHEET is NOT unique (number 407 labels two different restaurants), so we
# use the row position as the store identifier.
df = df.reset_index().rename(columns={"index": "store_id"})

# --- treatment indicator --------------------------------------------------
# STATE == 1 -> New Jersey (treated); STATE == 0 -> Pennsylvania (control)
df["treated"] = (df["STATE"] == 1).astype(int)

# --- full-time-equivalent employment --------------------------------------
df["fte1"] = df["EMPFT"] + 0.5 * df["EMPPT"] + df["NMGRS"]
df["fte2"] = df["EMPFT2"] + 0.5 * df["EMPPT2"] + df["NMGRS2"]

# --- starting wage ---------------------------------------------------------
df["wage1"] = df["WAGE_ST"]
df["wage2"] = df["WAGE_ST2"]

# --- first differences (DiD building blocks) -------------------------------
df["d_fte"] = df["fte2"] - df["fte1"]
df["d_wage"] = df["wage2"] - df["wage1"]

# --- save processed data ---------------------------------------------------
df.to_csv("data/processed/wide.csv", index=False)

id_cols = ["store_id", "treated", "STATE", "CHAIN", "CO_OWNED",
           "SOUTHJ", "CENTRALJ", "NORTHJ", "PA1", "PA2", "SHORE"]
long = pd.concat([
    df[id_cols + ["fte1", "wage1"]].rename(columns={"fte1": "fte", "wage1": "wage"}).assign(wave=1),
    df[id_cols + ["fte2", "wage2"]].rename(columns={"fte2": "fte", "wage2": "wage"}).assign(wave=2),
], ignore_index=True)
long.to_csv("data/processed/panel.csv", index=False)

# --- verification against the paper ----------------------------------------
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

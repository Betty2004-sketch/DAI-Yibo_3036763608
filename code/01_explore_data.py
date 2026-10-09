"""
Step 2 — Explore the raw Card-Krueger data (public.csv).

Loads the raw CSV, prints its structure, missingness, and the treatment/control
group composition. No variables are modified here; this is pure exploration.
"""
import pandas as pd

RAW = "data/raw/public.csv"

df = pd.read_csv(RAW)

print("=" * 70)
print("1. 数据维度 (rows x columns)")
print("=" * 70)
print(f"{df.shape[0]} rows  x  {df.shape[1]} columns")
print()

print("=" * 70)
print("2. 全部列名（按顺序，带序号）")
print("=" * 70)
for i, c in enumerate(df.columns, 1):
    print(f"{i:2d}. {c}")

print()
print("=" * 70)
print("3. 各列数据类型 (dtypes)")
print("=" * 70)
print(df.dtypes.value_counts().to_string())
print()

print("=" * 70)
print("4. 缺失值统计（只列出有缺失的列，按缺失数降序）")
print("=" * 70)
missing = df.isna().sum()
missing = missing[missing > 0].sort_values(ascending=False)
if missing.empty:
    print("（没有任何缺失值）")
else:
    for col, n in missing.items():
        print(f"{col:12s} 缺失 {n:3d}  ({n/len(df)*100:5.1f}%)")

print()
print("=" * 70)
print("5. STATE 的取值分布（判断哪是 NJ / 哪是 PA）")
print("=" * 70)
print(df["STATE"].value_counts(dropna=False).to_string())

print()
print("=" * 70)
print("6. 门店唯一标识 SHEET 是否唯一")
print("=" * 70)
print(f"SHEET 唯一值数量: {df['SHEET'].nunique()}  (总行数 {len(df)})")

print()
print("=" * 70)
print("7. 前 3 行数据（转置显示，方便看每个变量的取值）")
print("=" * 70)
print(df.head(3).T.to_string())


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "data" / "raw" / "P1 DATA.xlsx"

raw = pd.read_excel(DATA_FILE, header=None)

# Locating the monthly data header
header_index = raw[
    raw.iloc[:, 0].astype(str).str.contains(
        r'YEAR\s+JAN', case=False, na=False
    )
].index[0]

# Extracting month names
months = str(raw.iloc[header_index, 0]).split()

# Identifying the monthly sales section
records = []

for value in raw.iloc[header_index + 1:, 0]:
    if pd.isna(value):
        continue

    row = str(value).split()


    if row[0] == "SEASONAL":
        break

    if row[0].isdigit() and len(row) >= 2:
        records.append(row)

# Convert into a structured DataFrame
sales = pd.DataFrame(records, columns=months)

# Convert values into appropriate numerical types
sales["YEAR"] = pd.to_numeric(sales["YEAR"])

for month in months[1:]:
    sales[month] = pd.to_numeric(
        sales[month], errors="coerce"
    )

# Filter the required period
sales = sales[
    (sales["YEAR"] >= 2020) &
    (sales["YEAR"] <= 2026)
].copy()

print(sales)
print("\nDataset dimensions:", sales.shape)


# Reshape from wide format to long format
monthly_sales = sales.melt(
    id_vars=["YEAR"],
    var_name="MONTH",
    value_name="SALES"
)

# Convert month names into numbers
monthly_sales["MONTH_NUMBER"] = pd.to_datetime(
    monthly_sales["MONTH"],
    format="%b"
).dt.month

# Create a proper date column
monthly_sales["DATE"] = pd.to_datetime(
    dict(
        year=monthly_sales["YEAR"],
        month=monthly_sales["MONTH_NUMBER"],
        day=1
    )
)

# Sort chronologically
monthly_sales = monthly_sales.sort_values("DATE")

# Remove missing sales observations
monthly_sales = monthly_sales.dropna(subset=["SALES"])

# Final dataset
monthly_sales = monthly_sales[
    ["DATE", "YEAR", "MONTH", "SALES"]
].reset_index(drop=True)

print(monthly_sales.head())
print(monthly_sales.tail())
print("\nFinal dimensions:", monthly_sales.shape)


# ==========================================
# STEP 2: DATA QUALITY VALIDATION
# ==========================================

print("\n========== DATA QUALITY REPORT ==========")

# 1. Check missing values
print("\n1. Missing values:")
print(monthly_sales.isnull().sum())

# 2. Check duplicate dates
print("\n2. Duplicate dates:")
print(monthly_sales["DATE"].duplicated().sum())

# 3. Check negative or zero sales
print("\n3. Invalid sales values:")
print((monthly_sales["SALES"] <= 0).sum())

# 4. Check date range
print("\n4. Date range:")
print("Start:", monthly_sales["DATE"].min())
print("End:", monthly_sales["DATE"].max())

# 5. Check chronological order
print("\n5. Chronological order:")
print(monthly_sales["DATE"].is_monotonic_increasing)

# 6. Check expected observations
print("\n6. Total observations:")
print(len(monthly_sales))

# 7. Check missing months in the sequence
expected_dates = pd.date_range(
    start=monthly_sales["DATE"].min(),
    end=monthly_sales["DATE"].max(),
    freq="MS"
)

missing_dates = expected_dates.difference(
    monthly_sales["DATE"]
)

print("\n7. Missing monthly dates:")
print(missing_dates)

print("\n========== VALIDATION COMPLETED ==========")

# ==========================================
# STEP 3.1: DESCRIPTIVE STATISTICS
# ==========================================

print("\n========== DESCRIPTIVE STATISTICS ==========")

# Calculate summary statistics
summary = monthly_sales["SALES"].describe()

print(summary)

# Additional statistical measures
print("\nAdditional measures:")

print("Median:", monthly_sales["SALES"].median())

print("Variance:", monthly_sales["SALES"].var())

print("Standard Deviation:", monthly_sales["SALES"].std())

print("Range:",
      monthly_sales["SALES"].max() -
      monthly_sales["SALES"].min())

# Coefficient of variation
cv = (
    monthly_sales["SALES"].std() /
    monthly_sales["SALES"].mean()
) * 100

print("Coefficient of Variation:", round(cv, 2), "%")

# ==========================================
# STEP 3.2: ANNUAL SALES ANALYSIS
# ==========================================

annual_sales = monthly_sales.groupby("YEAR").agg(
    Average_Sales=("SALES", "mean"),
    Total_Sales=("SALES", "sum"),
    Minimum_Sales=("SALES", "min"),
    Maximum_Sales=("SALES", "max"),
    Sales_Std=("SALES", "std")
).reset_index()

# Calculate annual average sales growth
annual_sales["Growth_Percentage"] = (
    annual_sales["Average_Sales"].pct_change() * 100
)

print("\n========== ANNUAL SALES PERFORMANCE ==========")

print(annual_sales.round(2).to_string(index=False))

# ==========================================
# STEP 3.3: MONTHLY SALES TREND
# ==========================================

plt.figure(figsize=(14, 6))

plt.plot(
    monthly_sales["DATE"],
    monthly_sales["SALES"],
    linewidth=2,
    marker="o",
    markersize=3
)

plt.title(
    "US Retail and Food Services Sales (2020–2026)",
    fontsize=15
)

plt.xlabel("Year")
plt.ylabel("Monthly Sales (Million USD)")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig("monthly_retail_sales_trend.png", dpi=300)

plt.show()

# ==========================================
# STEP 3.4: ANNUAL AVERAGE SALES
# ==========================================

plt.figure(figsize=(11, 6))

sns.barplot(
    data=annual_sales,
    x="YEAR",
    y="Average_Sales"
)

plt.title(
    "Average Monthly Retail Sales by Year",
    fontsize=15
)

plt.xlabel("Year")
plt.ylabel("Average Monthly Sales (Million USD)")

plt.tight_layout()

plt.savefig("annual_average_retail_sales.png", dpi=300)

plt.show()

# ==========================================
# STEP 4.1: MONTHLY SALES GROWTH
# ==========================================

monthly_sales["Monthly_Growth"] = (
    monthly_sales["SALES"].pct_change() * 100
)

print("\nMONTHLY SALES GROWTH")
print(
    monthly_sales[
        ["DATE", "SALES", "Monthly_Growth"]
    ].round(2).head(15)
)

print("\nAverage monthly growth:",
      round(monthly_sales["Monthly_Growth"].mean(), 2), "%")

# ==========================================
# STEP 4.2: YEAR-OVER-YEAR GROWTH
# ==========================================

monthly_sales["YoY_Growth"] = (
    monthly_sales["SALES"].pct_change(periods=12) * 100
)

print("\nYEAR-OVER-YEAR GROWTH")

print(
    monthly_sales[
        ["DATE", "SALES", "YoY_Growth"]
    ].round(2).tail(30)
)

# ==========================================
# STEP 4.3: HIGHEST AND LOWEST SALES
# ==========================================

highest_month = monthly_sales.loc[
    monthly_sales["SALES"].idxmax()
]

lowest_month = monthly_sales.loc[
    monthly_sales["SALES"].idxmin()
]

print("\nHIGHEST SALES MONTH")
print(highest_month[["DATE", "SALES"]])

print("\nLOWEST SALES MONTH")
print(lowest_month[["DATE", "SALES"]])

# ==========================================
# STEP 4.4: PERIOD COMPARISON
# ==========================================

def classify_period(year):
    if year == 2020:
        return "2020 - Pandemic"
    elif year <= 2022:
        return "2021-2022 - Recovery"
    else:
        return "2023-2026 - Recent"

monthly_sales["Period"] = (
    monthly_sales["YEAR"].apply(classify_period)
)

period_analysis = monthly_sales.groupby("Period").agg(
    Average_Sales=("SALES", "mean"),
    Median_Sales=("SALES", "median"),
    Sales_Std=("SALES", "std"),
    Observations=("SALES", "count")
).reset_index()

print("\nPERIOD COMPARISON")

print(period_analysis.round(2).to_string(index=False))

# ==========================================
# STEP 4.5: YOY GROWTH VISUALISATION
# ==========================================

plt.figure(figsize=(14, 6))

plt.plot(
    monthly_sales["DATE"],
    monthly_sales["YoY_Growth"],
    marker="o",
    linewidth=1.8
)

plt.axhline(
    y=0,
    linestyle="--"
)

plt.title(
    "Year-over-Year US Retail Sales Growth (2021-2026)"
)

plt.xlabel("Year")
plt.ylabel("YoY Growth (%)")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig("retail_yoy_growth.png", dpi=300)

plt.show()

# ==========================================
# STEP 5: CONSOLIDATED ANALYTICAL SUMMARY
# ==========================================

print("\n========== PROJECT FINDINGS ==========")

# Overall sales
print("\n1. Overall sales")
print("Average:", round(monthly_sales["SALES"].mean(), 2))
print("Median:", round(monthly_sales["SALES"].median(), 2))
print("Standard deviation:",
      round(monthly_sales["SALES"].std(), 2))

# Monthly growth
print("\n2. Monthly growth")
print("Average:",
      round(monthly_sales["Monthly_Growth"].mean(), 2), "%")

# Annual growth
print("\n3. Latest available YoY growth")
latest_yoy = monthly_sales.dropna(
    subset=["YoY_Growth"]
).iloc[-1]

print("Month:", latest_yoy["DATE"].strftime("%B %Y"))
print("Growth:", round(latest_yoy["YoY_Growth"], 2), "%")

# Highest and lowest sales
print("\n4. Sales extremes")
print("Highest:", round(monthly_sales["SALES"].max(), 2))
print("Lowest:", round(monthly_sales["SALES"].min(), 2))

# Period comparison
print("\n5. Period comparison")
print(period_analysis.round(2).to_string(index=False))

# ==========================================
# STEP 5.2: ROLLING SALES VOLATILITY
# ==========================================

monthly_sales["Rolling_Std"] = (
    monthly_sales["SALES"].rolling(window=12).std()
)

plt.figure(figsize=(14, 6))

plt.plot(
    monthly_sales["DATE"],
    monthly_sales["Rolling_Std"],
    linewidth=2
)

plt.title("12-Month Rolling Standard Deviation of Retail Sales")

plt.xlabel("Year")
plt.ylabel("Rolling Standard Deviation (Million USD)")

plt.tight_layout()

plt.savefig("retail_sales_volatility.png", dpi=300)

plt.show()


# ==========================================
# CORRECTION A: LIKE-FOR-LIKE 2026 COMPARISON
# ==========================================

comparison_data = monthly_sales[
    monthly_sales["YEAR"].isin([2025, 2026]) &
    (monthly_sales["DATE"].dt.month <= 9)
]

matched_comparison = comparison_data.groupby("YEAR").agg(
    Average_Sales=("SALES", "mean"),
    Total_Sales=("SALES", "sum")
)

print("\nJANUARY-SEPTEMBER COMPARISON")
print(matched_comparison.round(2))

# Calculate comparable growth
growth_2026 = (
    matched_comparison.loc[2026, "Total_Sales"] /
    matched_comparison.loc[2025, "Total_Sales"] - 1
) * 100

print("\n2026 Year-over-Year Growth (Jan-Sep):",
      round(growth_2026, 2), "%")

# ==========================================
# VISUALISATION: YEAR-OVER-YEAR GROWTH
# ==========================================

plt.figure(figsize=(14, 6))

sns.lineplot(
    data=monthly_sales.dropna(subset=["YoY_Growth"]),
    x="DATE",
    y="YoY_Growth",
    marker="o",
    linewidth=2
)

plt.axhline(0, linestyle="--")

plt.title(
    "US Retail Sales: Year-over-Year Growth (2021-2026)",
    fontsize=15
)

plt.xlabel("Year")
plt.ylabel("Growth (%)")

plt.tight_layout()

plt.savefig("yoy_growth_analysis.png", dpi=300)

plt.show()

# Calculate monthly sales growth
monthly_growth = monthly_sales.copy()

monthly_growth["Monthly_Growth"] = (
    monthly_growth["SALES"].pct_change() * 100
)

# Calculate year-over-year growth
monthly_growth["YoY_Growth"] = (
    monthly_growth["SALES"].pct_change(periods=12) * 100
)

print("\nMONTHLY GROWTH STATISTICS")

growth_stats = monthly_growth["Monthly_Growth"].dropna().agg(
    ["mean", "median", "std", "min", "max"]
)

print(growth_stats)
plt.figure(figsize=(12, 6))

plt.plot(
    monthly_growth["DATE"],
    monthly_growth["YoY_Growth"],
    linewidth=2,
    label="Year-over-Year Growth"
)

plt.axhline(
    y=0,
    linestyle="--",
    linewidth=1,
    label="Zero Growth"
)

plt.title("U.S. Retail Sales: Year-over-Year Growth (2021–2026)")
plt.xlabel("Date")
plt.ylabel("Growth (%)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("yoy_growth.png", dpi=300)
plt.show()

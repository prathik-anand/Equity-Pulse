import yfinance as yf

ticker = "NVDA"
stock = yf.Ticker(ticker)
info = stock.info

print(f"--- Checking EBIT vs EBITDA for {ticker} ---")

# 1. Get Capital Base (Snapshot)
balance_sheet = stock.balance_sheet
latest_date_bs = balance_sheet.columns[0]
total_assets = balance_sheet.loc["Total Assets", latest_date_bs]
current_liabilities = balance_sheet.loc["Total Current Liabilities", latest_date_bs]
capital_employed = total_assets - current_liabilities
print(f"Capital Employed (Snapshot): {capital_employed:,.0f}")

# 2. Get Income Metrics (TTM)
revenue_ttm = info.get("totalRevenue")
op_margin = info.get("operatingMargins")
ebit_ttm = revenue_ttm * op_margin

ebitda_ttm = info.get("ebitda")

print(f"\n[TTM Values]")
print(f"Revenue: {revenue_ttm:,.0f}")
print(f"EBIT (Rev * OpMargin): {ebit_ttm:,.0f}")
print(f"EBITDA (from info): {ebitda_ttm:,.0f}")

# 3. Calculate ROCE Variants
roce_ebit = ebit_ttm / capital_employed
roce_ebitda = ebitda_ttm / capital_employed if ebitda_ttm else 0

print(f"\n[ROCE Calculation]")
print(f"Standard ROCE (EBIT / CapEmployed): {roce_ebit:.4f} ({roce_ebit * 100:.2f}%)")
print(
    f"EBITDA Return (EBITDA / CapEmployed): {roce_ebitda:.4f} ({roce_ebitda * 100:.2f}%)"
)

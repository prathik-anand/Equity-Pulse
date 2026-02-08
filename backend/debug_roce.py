import yfinance as yf

ticker = "NVDA"
stock = yf.Ticker(ticker)
info = stock.info

print(f"--- Checking Data for {ticker} ---")

# 1. Annual Data (Current Implementation)
try:
    income_stmt = stock.income_stmt
    balance_sheet = stock.balance_sheet

    latest_date = income_stmt.columns[0]
    print(f"Latest Annual Report Date: {latest_date}")

    ebit_annual = (
        income_stmt.loc["EBIT", latest_date]
        if "EBIT" in income_stmt.index
        else income_stmt.loc["Operating Income", latest_date]
    )

    total_assets = balance_sheet.loc["Total Assets", latest_date]
    curr_liab = (
        balance_sheet.loc["Total Current Liabilities", latest_date]
        if "Total Current Liabilities" in balance_sheet.index
        else balance_sheet.loc["Current Liabilities", latest_date]
    )

    cap_employed_annual = total_assets - curr_liab
    roce_annual = ebit_annual / cap_employed_annual

    print(f"\n[Annual Calculation]")
    print(f"EBIT: {ebit_annual:,.0f}")
    print(f"Capital Employed: {cap_employed_annual:,.0f}")
    print(f"ROCE: {roce_annual:.4f} ({roce_annual * 100:.2f}%)")
except Exception as e:
    print(f"Annual Calc Failed: {e}")

# 2. TTM Estimate (Using Info)
try:
    revenue_ttm = info.get("totalRevenue")
    op_margin = info.get("operatingMargins")
    ebit_ttm = revenue_ttm * op_margin

    # We still have to use latest Balance Sheet for Capital Base (Standard practice if quarterly BS not easily aligned)
    # Or we can try to get quarterly balance sheet

    print(f"\n[TTM Estimate via Info]")
    print(f"Revenue TTM: {revenue_ttm:,.0f}")
    print(f"Op Margin: {op_margin}")
    print(f"EBIT TTM: {ebit_ttm:,.0f}")

    # Recalculate ROCE with TTM EBIT and same Capital Base
    roce_ttm = ebit_ttm / cap_employed_annual
    print(
        f"ROCE (TTM EBIT / Last Annual Capital): {roce_ttm:.4f} ({roce_ttm * 100:.2f}%)"
    )

except Exception as e:
    print(f"TTM Calc Failed: {e}")

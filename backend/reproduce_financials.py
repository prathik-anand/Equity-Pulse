import yfinance as yf
import json

def get_valuation_ratios(ticker: str):
    stock = yf.Ticker(ticker)
    info = stock.info
    print(f"Keys in info: {list(info.keys())}")
    metrics = {
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
        },
        "profitability": {
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "gross_margins": info.get("grossMargins"),
            "operating_margins": info.get("operatingMargins"),
            "profit_margins": info.get("profitMargins"),
        },
        "financial_health": {
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "debt_to_equity": info.get("debtToEquity"),
            "free_cashflow": info.get("freeCashflow"),
        },
        "dividends": {
            "yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
        }
    }
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    get_valuation_ratios("NVDA")

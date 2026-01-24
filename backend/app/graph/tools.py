from langchain.tools import tool
import yfinance as yf
from langchain_community.tools import DuckDuckGoSearchRun
import json

@tool
def get_stock_price(ticker: str):
    """Get current stock price and basic info for a given ticker symbol."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return json.dumps({
            "current_price": info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency")
        })
    except Exception as e:
        return json.dumps({"error": f"Error fetching price: {str(e)}", "current_price": 0})

@tool
def get_financials(ticker: str):
    """Get financial statements (balance sheet, income statement) for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        # Getting last 2 years of data to be concise
        if stock.balance_sheet.empty or stock.income_stmt.empty:
             return json.dumps({"error": "No financial data found", "balance_sheet": {}, "income_statement": {}})
             
        balance_sheet = stock.balance_sheet.iloc[:, :2].to_dict()
        income_stmt = stock.income_stmt.iloc[:, :2].to_dict()
        return json.dumps({
            "balance_sheet": balance_sheet,
            "income_statement": income_stmt
        })
    except Exception as e:
        return json.dumps({"error": f"Error fetching financials: {str(e)}", "balance_sheet": {}, "income_statement": {}})

@tool
def get_company_news(ticker: str):
    """Get recent news for a company using Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        return json.dumps(news[:5]) # Top 5 news items
    except Exception as e:
         return json.dumps([{"title": "Error fetching news", "link": "", "publisher": "System"}])

@tool
def search_governance_issues(query: str):
    """Search for governance issues, scandals, or management track record."""
    search = DuckDuckGoSearchRun()
    return search.run(query)

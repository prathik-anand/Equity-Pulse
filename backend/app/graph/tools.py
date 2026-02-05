"""
Tools for the EquityPulse analysis agents.
Each tool has:
- args_schema: Pydantic model for input validation
- Return type: Pydantic model for output structure
- Detailed docstring for LLM tool selection
"""
from langchain.tools import tool
import yfinance as yf
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List

from app.graph.schemas.tool_inputs import (
    FinancialsInput,
    CompanyNewsInput,
    GovernanceSearchInput,
    MarketTrendsSearchInput,
)
from app.graph.schemas.tool_outputs import (
    StockPriceOutput,
    FinancialsOutput,
    CompanyNewsOutput,
    NewsArticle,
    WebSearchOutput,
)






@tool(args_schema=FinancialsInput)
def get_financials(ticker: str) -> str:
    """
    Retrieve financial statements for fundamental analysis.
    
    Returns JSON with:
    - balance_sheet: Total Assets, Total Debt, Cash, Stockholders Equity (last 2 years)
    - income_statement: Total Revenue, Net Income, Operating Income, Gross Profit (last 2 years)
    
    Use this to calculate:
    - Revenue growth rate (YoY)
    - Net profit margin (Net Income / Revenue)
    - Debt levels and cash position
    - Asset efficiency
    
    Call this tool for any valuation or financial health assessment.
    """
    try:
        stock = yf.Ticker(ticker)
        
        if stock.balance_sheet.empty or stock.income_stmt.empty:
            output = FinancialsOutput(
                ticker=ticker,
                error="No financial data available for this ticker"
            )
            return output.model_dump_json()
        
        # Get last 2 years of data, convert timestamps to strings for JSON
        balance_sheet = stock.balance_sheet.iloc[:, :2]
        balance_sheet.columns = [str(col.date()) for col in balance_sheet.columns]
        
        income_stmt = stock.income_stmt.iloc[:, :2]
        income_stmt.columns = [str(col.date()) for col in income_stmt.columns]
        
        output = FinancialsOutput(
            ticker=ticker,
            balance_sheet=balance_sheet.to_dict(),
            income_statement=income_stmt.to_dict(),
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = FinancialsOutput(
            ticker=ticker,
            error=f"Error fetching financials: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=CompanyNewsInput)
def get_company_news(ticker: str) -> str:
    """
    Get the 5 most recent news articles about a company from Yahoo Finance.
    
    Returns JSON with articles containing:
    - title: Headline of the news article
    - publisher: News source (e.g., Reuters, Bloomberg)
    - link: URL to full article
    - providerPublishTime: Unix timestamp of publication
    
    Use this for:
    - Recent developments affecting the stock
    - Sentiment analysis
    - Catalyst identification
    - Management/governance news
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            output = CompanyNewsOutput(
                ticker=ticker,
                articles=[],
                error="No recent news found"
            )
            return output.model_dump_json()
        
        # Parse news into NewsArticle models
        articles = []
        for item in news[:5]:
            article = NewsArticle(
                title=item.get("title", ""),
                publisher=item.get("publisher"),
                link=item.get("link"),
                providerPublishTime=item.get("providerPublishTime"),
                type=item.get("type"),
                uuid=item.get("uuid"),
                thumbnail=item.get("thumbnail"),
                relatedTickers=item.get("relatedTickers"),
            )
            articles.append(article)
        
        output = CompanyNewsOutput(
            ticker=ticker,
            articles=articles,
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = CompanyNewsOutput(
            ticker=ticker,
            articles=[],
            error=f"Error fetching news: {str(e)}"
        )
        return output.model_dump_json()


@tool(args_schema=GovernanceSearchInput)
def search_governance_issues(query: str) -> str:
    """
    Search the web for corporate governance information, controversies, and management track record.
    
    Best search queries include:
    - "[Company] SEC enforcement actions"
    - "[Company] executive compensation controversy"
    - "[Company] board of directors independence"
    - "[Company] shareholder lawsuits settlements"
    - "[Company] CEO CFO turnover departures"
    - "[Company] accounting irregularities audit"
    
    Returns: Text summary of search results from DuckDuckGo.
    
    Use this for Management Analyst to assess leadership quality and governance risks.
    """
    try:
        max_retries = 3
        for i in range(max_retries):
            try:
                from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
                wrapper = DuckDuckGoSearchAPIWrapper(region="us-en", time="y", max_results=5)
                search = DuckDuckGoSearchRun(api_wrapper=wrapper)
                results = search.run(query)
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                import time
                time.sleep(2)
        
        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = WebSearchOutput(
            query=query,
            results="",
            error=f"Search error after retries: {str(e)}"
        )
        return output.model_dump_json()


@tool
def get_price_history_stats(ticker: str) -> str:
    """
    Get ONLY historical price performance (CAGR) and volatility.
    Use this to analyze long-term stock momentum (1y, 3y, 5y, 10y).
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch max history
        hist = stock.history(period="10y")
        price_cagr = {}
        
        if not hist.empty:
            current = float(hist['Close'].iloc[-1])
            def calc_cagr(years):
                days = years * 252
                if len(hist) > days:
                    start_price = float(hist['Close'].iloc[-(days+1)])
                    if start_price > 0:
                        cagr = (current / start_price) ** (1/years) - 1
                        return round(cagr * 100, 2)
                return None
            
            price_cagr['cagr_1y'] = calc_cagr(1)
            price_cagr['cagr_3y'] = calc_cagr(3)
            price_cagr['cagr_5y'] = calc_cagr(5)
            price_cagr['cagr_10y'] = calc_cagr(10)
            
            price_stats = {
                "current_price": round(current, 2),
                "52w_high": round(float(hist['High'].tail(252).max()), 2),
                "52w_low": round(float(hist['Low'].tail(252).min()), 2),
                "volatility_30d": round(float(hist['Close'].pct_change().std() * (252**0.5) * 100), 2),
                "growth_cagr_percent": price_cagr
            }
            import json
            return json.dumps(price_stats, default=str)
        return json.dumps({"error": "No price history found"})
    except Exception as e:
        return f"Error: {e}"

@tool
def get_fundamental_growth_stats(ticker: str) -> str:
    """
    Get ONLY fundamental growth rates (CAGR) for Revenue, Net Income, Operating Income.
    Data limited to last 3-4 years.
    """
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        fund_cagr = {}
        
        if not financials.empty:
            fin_sorted = financials.T.sort_index() 
            def get_series_cagr(row_name):
                try:
                    if row_name in fin_sorted.columns:
                        series = fin_sorted[row_name].dropna()
                        if len(series) >= 2:
                            start_val = series.iloc[0]
                            end_val = series.iloc[-1]
                            years = (series.index[-1] - series.index[0]).days / 365.25
                            if years >= 1 and start_val > 0 and end_val > 0:
                                cagr = (end_val / start_val) ** (1/years) - 1
                                return round(cagr * 100, 2)
                except:
                    pass
                return None

            fund_cagr['revenue_cagr_3y'] = get_series_cagr("Total Revenue")
            fund_cagr['net_income_cagr_3y'] = get_series_cagr("Net Income")
            fund_cagr['operating_income_cagr_3y'] = get_series_cagr("Operating Income")
            
            import json
            return json.dumps(fund_cagr, default=str)
        return json.dumps({"error": "No financials found"})
    except Exception as e:
        return f"Error: {e}"

@tool
def get_valuation_ratios(ticker: str) -> str:
    """
    Get ONLY deep investment ratios: Valuation, Profitability, Financial Health, Dividends.
    Does NOT include price history or growth rates.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Helper to safely get and normalize percentage values that YF returns as 0-100
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
             # YF returns Debt/Eq as percentage (e.g. 9.1 for 9.1%), convert to ratio (0.091)
            debt_to_equity = round(debt_to_equity / 100.0, 4)

        peg_ratio = info.get("pegRatio")
        if peg_ratio is None:
            peg_ratio = info.get("trailingPegRatio")

        dividend_yield = info.get("dividendYield")
        if dividend_yield is not None:
             # YF returns Dividend Yield as percentage number (e.g. 7.02 for 7.02%)
             # We want to keep it as percentage number for consistency with other % metrics
             pass

        # Helper to convert decimal to percentage
        def to_pct(val):
            return round(val * 100.0, 2) if val is not None else None

        metrics = {
            "valuation": {
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": peg_ratio,
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            },
            "profitability": {
                "roe": to_pct(info.get("returnOnEquity")),
                "roa": to_pct(info.get("returnOnAssets")),
                "gross_margins": to_pct(info.get("grossMargins")),
                "operating_margins": to_pct(info.get("operatingMargins")),
                "profit_margins": to_pct(info.get("profitMargins")),
            },
            "financial_health": {
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "debt_to_equity": debt_to_equity,
                "free_cashflow": info.get("freeCashflow"),
            },
            "dividends": {
                "yield": dividend_yield,
                "payout_ratio": to_pct(info.get("payoutRatio")),
            }
        }
        import json
        return json.dumps(metrics, default=str)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_price_action(ticker: str) -> str:
    """
    Get pure Price Action data: OHLC, 52-week Range, and Volatility.
    Use this to identify Support/Resistance levels.
    """
    try:
        stock = yf.Ticker(ticker)
        # We need recent intraday data for accurate OHLC
        info = stock.info
        hist = stock.history(period="1y") # Need at least 1y for 52w calc verification or volatility
        
        # Fallback to history if info is missing
        current = info.get("currentPrice") or (float(hist['Close'].iloc[-1]) if not hist.empty else None)
        
        output = {
            "ticker": ticker,
            "price": {
                "current": current,
                "previous_close": info.get("previousClose"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
            },
            "range_52w": {
                "high": info.get("fiftyTwoWeekHigh"),
                "low": info.get("fiftyTwoWeekLow"),
            },
             "volatility": {
                "beta": info.get("beta"),
                # Calculate 30d realized volatility
                "historical_volatility_30d": round(float(hist['Close'].pct_change().std() * (252**0.5) * 100), 2) if not hist.empty else None
            },
            "profile": {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
        }
        import json
        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_technical_indicators(ticker: str) -> str:
    """
    Get Technical Indicators: SMAs (20, 50, 200) and RSI (14).
    Use this to determine Trend Direction (Bull/Bear) and Momentum (Overbought/Oversold).
    """
    try:
        stock = yf.Ticker(ticker)
        # Need ~200 days for SMA200 + buffer for RSI calc
        hist = stock.history(period="1y")
        
        if hist.empty:
             return json.dumps({"error": "No history found"})
             
        # Calculate SMAs
        closes = hist['Close']
        sma_20 = float(closes.tail(20).mean()) if len(closes) >= 20 else None
        sma_50 = float(closes.tail(50).mean()) if len(closes) >= 50 else None
        sma_200 = float(closes.tail(200).mean()) if len(closes) >= 200 else None
        
        # Calculate RSI (14)
        def calc_rsi(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
            
        rsi = calc_rsi(closes)
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else None
        
        # Determine Trend State (Simple logic for helper)
        trend = "Neutral"
        if sma_20 and sma_50:
            if sma_20 > sma_50: trend = "Bullish (Golden Cross/Uptrend)"
            else: trend = "Bearish (Death Cross/Downtrend)"

        output = {
            "ticker": ticker,
            "trend_indicators": {
                "sma_20": round(sma_20, 2) if sma_20 else None,
                "sma_50": round(sma_50, 2) if sma_50 else None,
                "sma_200": round(sma_200, 2) if sma_200 else None,
                "trend_signal": trend
            },
            "momentum_indicators": {
                "rsi_14": round(current_rsi, 2) if current_rsi else None,
                "rsi_condition": "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
            }
        }
        import json
        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_volume_analysis(ticker: str) -> str:
    """
    Get Volume Analysis: Current vs Average and Relative Volume (RVOL).
    Use this to confirm the strength of price moves.
    """
    try:
        stock = yf.Ticker(ticker)
        # Need recent history
        hist = stock.history(period="3mo")
        info = stock.info
        
        if hist.empty:
             return json.dumps({"error": "No history found"})
             
        current_vol = info.get("volume")
        if not current_vol and not hist.empty:
            current_vol = int(hist['Volume'].iloc[-1])
            
        avg_vol_10d = float(hist['Volume'].tail(10).mean()) if len(hist) >= 10 else None
        avg_vol_3mo = float(hist['Volume'].mean()) # 3mo period
        
        rvol = round(current_vol / avg_vol_3mo, 2) if avg_vol_3mo and current_vol else None
        
        output = {
            "ticker": ticker,
            "volume_stats": {
                "current_volume": current_vol,
                "avg_volume_10d": int(avg_vol_10d) if avg_vol_10d else None,
                "avg_volume_3mo": int(avg_vol_3mo) if avg_vol_3mo else None,
            },
            "relative_volume": {
                "rvol": rvol,
                "interpretation": "High Interest" if rvol and rvol > 1.2 else "Low Interest"
            }
        }
        import json
        return json.dumps(output, default=str)
    except Exception as e:
        return f"Error: {e}"

@tool(args_schema=MarketTrendsSearchInput)
def search_market_trends(query: str) -> str:
    """
    Search the web for market trends, sector analysis, and competitive landscape.
    
    Best search queries include:
    - "[Sector] market trends 2024 2025 outlook"
    - "[Company] vs [Competitor] market share comparison"
    - "[Industry] regulatory changes impact"
    - "[Company] analyst upgrades downgrades price target"
    - "[Sector] AI adoption digital transformation"
    - "macro trends affecting [industry] interest rates inflation"
    
    Returns: Text summary of search results from DuckDuckGo.
    
    Use this for:
    - Sector Analyst: Industry positioning and competitive dynamics
    - Technical Analyst: Market sentiment and analyst opinions
    - Fundamental Analyst: Growth drivers and headwinds
    """
    try:
        max_retries = 3
        for i in range(max_retries):
            try:
                from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
                wrapper = DuckDuckGoSearchAPIWrapper(region="us-en", time="y", max_results=5)
                search = DuckDuckGoSearchRun(api_wrapper=wrapper)
                results = search.run(query)
                break
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                import time
                time.sleep(2)
        
        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = WebSearchOutput(
            query=query,
            results="",
            error=f"Search error after retries: {str(e)}"
        )
        return output.model_dump_json()

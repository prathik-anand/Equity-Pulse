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
    StockPriceInput,
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


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> str:
    """
    Retrieve comprehensive stock price data and technical indicators.
    
    Returns JSON with:
    - current_price, previous_close, open, day_low, day_high
    - fifty_two_week_low, fifty_two_week_high (for trend context)
    - sma_20, sma_50 (20-day and 50-day Simple Moving Averages)
    - volume, avg_volume, recent_volume_5d (for accumulation/distribution analysis)
    - pe_ratio, forward_pe (valuation metrics)
    - beta (volatility relative to market)
    - sector, industry (classification)
    
    Use this tool FIRST for any technical or price-related analysis.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for technical indicators
        hist = stock.history(period="3mo")
        
        # Calculate simple moving averages if we have data
        sma_20 = float(hist['Close'].tail(20).mean()) if len(hist) >= 20 else None
        sma_50 = float(hist['Close'].tail(50).mean()) if len(hist) >= 50 else None
        
        # Volume analysis
        avg_volume = float(hist['Volume'].mean()) if not hist.empty else None
        recent_volume = float(hist['Volume'].tail(5).mean()) if len(hist) >= 5 else None
        
        output = StockPriceOutput(
            ticker=ticker,
            current_price=info.get("currentPrice"),
            previous_close=info.get("previousClose"),
            open=info.get("open"),
            day_low=info.get("dayLow"),
            day_high=info.get("dayHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            volume=info.get("volume"),
            avg_volume=avg_volume,
            recent_volume_5d=recent_volume,
            sma_20=sma_20,
            sma_50=sma_50,
            beta=info.get("beta"),
            sector=info.get("sector"),
            industry=info.get("industry"),
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = StockPriceOutput(
            ticker=ticker,
            error=f"Error fetching price data: {str(e)}"
        )
        return output.model_dump_json()


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
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        
        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = WebSearchOutput(
            query=query,
            results="",
            error=f"Search error: {str(e)}"
        )
        return output.model_dump_json()


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
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        
        output = WebSearchOutput(
            query=query,
            results=results,
        )
        return output.model_dump_json()
        
    except Exception as e:
        output = WebSearchOutput(
            query=query,
            results="",
            error=f"Search error: {str(e)}"
        )
        return output.model_dump_json()

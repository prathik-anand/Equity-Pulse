"""
Tool Output Schemas - Pydantic models for tool return values.
These provide type safety, validation, and self-documenting code.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class StockPriceOutput(BaseModel):
    """Output schema for get_stock_price tool."""
    ticker: str = Field(description="The requested ticker symbol")
    current_price: Optional[float] = Field(None, description="Current trading price")
    previous_close: Optional[float] = Field(None, description="Previous day's closing price")
    open: Optional[float] = Field(None, description="Today's opening price")
    day_low: Optional[float] = Field(None, description="Today's low price")
    day_high: Optional[float] = Field(None, description="Today's high price")
    fifty_two_week_low: Optional[float] = Field(None, description="52-week low price")
    fifty_two_week_high: Optional[float] = Field(None, description="52-week high price")
    market_cap: Optional[float] = Field(None, description="Market capitalization in USD")
    pe_ratio: Optional[float] = Field(None, description="Trailing P/E ratio")
    forward_pe: Optional[float] = Field(None, description="Forward P/E ratio")
    volume: Optional[int] = Field(None, description="Today's trading volume")
    avg_volume: Optional[float] = Field(None, description="Average trading volume (3 months)")
    recent_volume_5d: Optional[float] = Field(None, description="Average volume last 5 days")
    sma_20: Optional[float] = Field(None, description="20-day Simple Moving Average")
    sma_50: Optional[float] = Field(None, description="50-day Simple Moving Average")
    beta: Optional[float] = Field(None, description="Beta (volatility vs market)")
    sector: Optional[str] = Field(None, description="Company sector classification")
    industry: Optional[str] = Field(None, description="Company industry classification")
    error: Optional[str] = Field(None, description="Error message if request failed")


class FinancialsOutput(BaseModel):
    """Output schema for get_financials tool."""
    ticker: str = Field(description="The requested ticker symbol")
    balance_sheet: Dict[str, Any] = Field(
        default_factory=dict,
        description="Balance sheet data: Total Assets, Total Debt, Cash, Stockholders Equity (last 2 years)"
    )
    income_statement: Dict[str, Any] = Field(
        default_factory=dict,
        description="Income statement: Total Revenue, Net Income, Operating Income, Gross Profit (last 2 years)"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class NewsArticle(BaseModel):
    """Single news article from Yahoo Finance."""
    title: str = Field(description="Headline of the news article")
    publisher: Optional[str] = Field(None, description="News source (e.g., Reuters, Bloomberg)")
    link: Optional[str] = Field(None, description="URL to full article")
    providerPublishTime: Optional[int] = Field(None, description="Unix timestamp of publication")
    type: Optional[str] = Field(None, description="Content type")
    uuid: Optional[str] = Field(None, description="Unique identifier")
    thumbnail: Optional[Dict[str, Any]] = Field(None, description="Thumbnail image data")
    relatedTickers: Optional[List[str]] = Field(None, description="Related stock tickers")


class CompanyNewsOutput(BaseModel):
    """Output schema for get_company_news tool."""
    ticker: str = Field(description="The requested ticker symbol")
    articles: List[NewsArticle] = Field(
        default_factory=list,
        description="List of recent news articles"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class WebSearchOutput(BaseModel):
    """Output schema for web search tools (governance and market trends)."""
    query: str = Field(description="The search query that was executed")
    results: str = Field(description="Text summary of search results from DuckDuckGo")
    error: Optional[str] = Field(None, description="Error message if search failed")

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
    previous_close: Optional[float] = Field(
        None, description="Previous day's closing price"
    )
    open: Optional[float] = Field(None, description="Today's opening price")
    day_low: Optional[float] = Field(None, description="Today's low price")
    day_high: Optional[float] = Field(None, description="Today's high price")
    fifty_two_week_low: Optional[float] = Field(None, description="52-week low price")
    fifty_two_week_high: Optional[float] = Field(None, description="52-week high price")
    market_cap: Optional[float] = Field(
        None, description="Market capitalization in USD"
    )
    pe_ratio: Optional[float] = Field(None, description="Trailing P/E ratio")
    peg_ratio: Optional[float] = Field(
        None, description="PEG Ratio (Price/Earnings to Growth)"
    )
    forward_pe: Optional[float] = Field(None, description="Forward P/E ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend Yield")
    dividend_rate: Optional[float] = Field(None, description="Dividend Rate (annual)")
    volume: Optional[int] = Field(None, description="Today's trading volume")
    avg_volume: Optional[float] = Field(
        None, description="Average trading volume (3 months)"
    )
    recent_volume_5d: Optional[float] = Field(
        None, description="Average volume last 5 days"
    )
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
        description="Balance sheet data: Total Assets, Total Debt, Cash, Stockholders Equity (last 2 years)",
    )
    income_statement: Dict[str, Any] = Field(
        default_factory=dict,
        description="Income statement: Total Revenue, Net Income, Operating Income, Gross Profit (last 2 years)",
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class NewsArticle(BaseModel):
    """Single news article from Yahoo Finance."""

    title: str = Field(description="Headline of the news article")
    publisher: Optional[str] = Field(
        None, description="News source (e.g., Reuters, Bloomberg)"
    )
    link: Optional[str] = Field(None, description="URL to full article")
    providerPublishTime: Optional[int] = Field(
        None, description="Unix timestamp of publication"
    )
    type: Optional[str] = Field(None, description="Content type")
    uuid: Optional[str] = Field(None, description="Unique identifier")
    thumbnail: Optional[Dict[str, Any]] = Field(
        None, description="Thumbnail image data"
    )
    relatedTickers: Optional[List[str]] = Field(
        None, description="Related stock tickers"
    )


class CompanyNewsOutput(BaseModel):
    """Output schema for get_company_news tool."""

    ticker: str = Field(description="The requested ticker symbol")
    articles: List[NewsArticle] = Field(
        default_factory=list, description="List of recent news articles"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class WebSearchOutput(BaseModel):
    """Output schema for web search tools (governance and market trends)."""

    query: str = Field(description="The search query that was executed")
    results: Optional[str] = Field(None, description="The search results text")
    error: Optional[str] = Field(None, description="Error message if search failed")


class InsiderTransaction(BaseModel):
    """Single insider transaction record."""

    date: Optional[str] = Field(None, description="Date of transaction")
    insider: Optional[str] = Field(None, description="Name of insider")
    position: Optional[str] = Field(None, description="Position/Title of insider")
    transaction: Optional[str] = Field(
        None, description="Transaction type (Buy/Sell/Grant)"
    )
    shares: Optional[int] = Field(None, description="Number of shares traded")
    value: Optional[float] = Field(None, description="Total value of transaction")


class InsiderTradesOutput(BaseModel):
    """Output schema for get_insider_trades tool."""

    ticker: str = Field(description="The requested ticker symbol")
    transactions: List[InsiderTransaction] = Field(
        default_factory=list, description="List of recent insider transactions"
    )
    summary: Optional[str] = Field(
        None, description="Summary of insider sentiment (e.g., 'Net Buying')"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class OwnershipDataOutput(BaseModel):
    """Output schema for get_ownership_data tool."""

    ticker: str = Field(description="The requested ticker symbol")
    institutional_ownership_pct: Optional[float] = Field(
        None, description="Percentage of shares held by institutions"
    )
    insider_ownership_pct: Optional[float] = Field(
        None, description="Percentage of shares held by insiders"
    )
    short_ratio: Optional[float] = Field(
        None, description="Short ratio (days to cover)"
    )
    short_percent_of_float: Optional[float] = Field(
        None, description="Short interest as percentage of float"
    )
    major_holders: Dict[str, Any] = Field(
        default_factory=dict, description="Breakdown of major holders"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")


class AdvancedRatiosOutput(BaseModel):
    """Output schema for get_advanced_ratios tool."""

    ticker: str = Field(description="The requested ticker symbol")
    return_on_capital: Optional[float] = Field(
        None,
        description="Return on Invested Capital (ROIC) - using ROE proxy if needed",
    )
    return_on_capital_employed: Optional[float] = Field(
        None,
        description="Return on Capital Employed (ROCE) = EBIT / (Total Assets - Current Liabilities)",
    )
    fcf_yield: Optional[float] = Field(None, description="Free Cash Flow Yield")
    price_to_fcf: Optional[float] = Field(None, description="Price to Free Cash Flow")
    payout_ratio: Optional[float] = Field(None, description="Dividend Payout Ratio")
    buyback_yield: Optional[float] = Field(
        None, description="Share Buyback Yield (approx)"
    )
    revenue_per_share: Optional[float] = Field(None, description="Revenue per share")
    net_income_per_share: Optional[float] = Field(None, description="EPS")
    error: Optional[str] = Field(None, description="Error message if request failed")


class RiskMetricsOutput(BaseModel):
    """Output schema for get_risk_metrics tool."""

    ticker: str = Field(description="The requested ticker symbol")
    altman_z_score: Optional[float] = Field(
        None, description="Altman Z-Score (Bankruptcy Prediction)"
    )
    beneish_m_score: Optional[float] = Field(
        None, description="Beneish M-Score (Earnings Manipulation)"
    )
    piotroski_f_score: Optional[int] = Field(
        None, description="Piotroski F-Score (0-9 Financial Health)"
    )
    days_sales_in_inventory: Optional[float] = Field(
        None, description="Days Sales in Inventory (DSI)"
    )
    dsi_change_pct: Optional[float] = Field(
        None, description="Year-over-Year change in DSI"
    )
    interest_coverage_ratio: Optional[float] = Field(
        None, description="Interest Coverage Ratio (EBIT / Interest Expense)"
    )
    current_ratio: Optional[float] = Field(
        None, description="Current Ratio (Current Assets / Current Liabilities)"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")

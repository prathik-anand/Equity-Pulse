"""
Tool Input Schemas - Pydantic models for tool parameters.
These schemas tell the LLM exactly what parameters each tool expects.
"""
from pydantic import BaseModel, Field


class FinancialsInput(BaseModel):
    """Input schema for get_financials tool."""
    ticker: str = Field(
        description="Stock ticker symbol to retrieve financial statements for"
    )


class CompanyNewsInput(BaseModel):
    """Input schema for get_company_news tool."""
    ticker: str = Field(
        description="Stock ticker symbol to get recent news articles for"
    )


class GovernanceSearchInput(BaseModel):
    """Input schema for search_governance_issues tool."""
    query: str = Field(
        description="Search query for governance research. Include company name and specific topics like 'lawsuits', 'SEC filings', 'executive departures', 'board changes', 'compensation controversy'"
    )


class MarketTrendsSearchInput(BaseModel):
    """Input schema for search_market_trends tool."""
    query: str = Field(
        description="Search query for market research. Include sector name, competitors, or macro trends like 'EV market share 2024', 'AI chip demand', 'interest rate impact on tech'"
    )

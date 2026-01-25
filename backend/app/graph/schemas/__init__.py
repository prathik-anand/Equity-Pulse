"""
Schemas package for EquityPulse.

Contains Pydantic models for:
- Tool inputs (tool_inputs.py)
- Tool outputs (tool_outputs.py)
- Agent analysis outputs (analysis.py)
"""
from app.graph.schemas.analysis import (
    TechnicalAnalysis,
    FundamentalAnalysis,
    SectorAnalysis,
    ManagementAnalysis,
)
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

__all__ = [
    # Agent outputs
    "TechnicalAnalysis",
    "FundamentalAnalysis",
    "SectorAnalysis",
    "ManagementAnalysis",
    # Tool inputs
    "FinancialsInput",
    "CompanyNewsInput",
    "GovernanceSearchInput",
    "MarketTrendsSearchInput",
    # Tool outputs
    "StockPriceOutput",
    "FinancialsOutput",
    "CompanyNewsOutput",
    "NewsArticle",
    "WebSearchOutput",
]

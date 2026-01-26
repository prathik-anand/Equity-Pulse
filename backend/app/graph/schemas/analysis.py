from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

class TechnicalMetrics(BaseModel):
    current_price: float = Field(..., description="Current trading price")
    support_level: Optional[float] = Field(None, description="Nearest support level")
    resistance_level: Optional[float] = Field(None, description="Nearest resistance level")
    rsi: Optional[float] = Field(None, description="RSI (14) value")
    macd_signal: Optional[Literal["Bullish", "Bearish", "Neutral"]] = Field(None, description="MACD signal status")
    moving_average_signals: Dict[str, Literal["Bullish", "Bearish", "Neutral"]] = Field(
        default_factory=dict, 
        description="Signals for SMA 20, 50, 200 (e.g., {'sma_50': 'Bullish'})"
    )
    volume_analysis: Optional[Literal["High", "Low", "Neutral"]] = Field(None, description="Relative volume analysis")
    trend: Literal["Uptrend", "Downtrend", "Sideways"] = Field(..., description="Primary trend direction")

class TechnicalAnalysis(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Final trading signal based on technicals")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    metrics: TechnicalMetrics = Field(..., description="Key technical indicators and price levels")
    reasoning: str = Field(..., description="Concise analysis explaining the signal")

class FundamentalDetails(BaseModel):
    financial_health: Literal["Strong", "Weak", "Stable"] = Field(..., description="Overall balance sheet health")
    growth_trajectory: Literal["Accelerating", "Decelerating", "Stagnant"] = Field(..., description="Revenue/Earnings growth trend")
    valuation: Literal["Overvalued", "Undervalued", "Fair"] = Field(..., description="Current valuation assessment")
    # Specific Metrics for Visuals
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings Ratio")
    pb_ratio: Optional[float] = Field(None, description="Price to Book Ratio")
    peg_ratio: Optional[float] = Field(None, description="Price/Earnings-to-Growth Ratio")
    debt_to_equity: Optional[float] = Field(None, description="Debt to Equity Ratio")
    revenue_growth: Optional[float] = Field(None, description="YoY Revenue Growth %")
    profit_margin: Optional[float] = Field(None, description="Net Profit Margin %")

class FundamentalAnalysis(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Final investment signal based on fundamentals")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    details: FundamentalDetails = Field(..., description="Categorical assessment of health, growth, and valuation")
    reasoning: str = Field(..., description="Detailed financial analysis citing specific numbers")

class SectorMetrics(BaseModel):
    sector_performance: str = Field(..., description="Brief description of how the sector is performing (e.g., 'Leading Market')")
    top_competitors: List[str] = Field(..., description="List of top 3 direct competitors")
    peer_comparison: Literal["Outperforming", "In-line", "Lagging"] = Field(..., description="Relative performance vs peers")

class SectorAnalysis(BaseModel):
    sector: str = Field(..., description="Name of the industry sector")
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(..., description="Sector outlook signal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    metrics: SectorMetrics = Field(..., description="Sector-specific key performance indicators")
    reasoning: str = Field(..., description="Analysis of sector trends and competitive positioning")

class ManagementAnalysis(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Governance signal: BUY=Visionary, SELL=Risky, HOLD=Stable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    summary: str = Field(..., description="Executive summary of leadership capability")
    risks: List[str] = Field(default_factory=list, description="List of specific governance risks or scandals if any")
    reasoning: str = Field(..., description="Deep dive into management quality and track record")

class PortfolioManagerOutput(BaseModel):
    """Output schema for the Aggregator (CIO) Agent."""
    final_signal: Literal["BUY", "SELL", "HOLD"] = Field(description="The final Buy/Sell/Hold decision")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0 (e.g., 0.85 for 85%). Do NOT use 0-100 scale.")
    executive_summary: str = Field(description="High-level summary (2-3 sentences) for the dashboard header")
    investment_thesis: str = Field(description="The 'Bull Case': key reasons to own this stock")
    bear_case_risks: str = Field(description="The 'Bear Case': key risks and reasons to sell")
    strategy_recommendation: str = Field(description="Actionable advice (e.g. 'Buy on dips to $200', 'Wait for earnings')")

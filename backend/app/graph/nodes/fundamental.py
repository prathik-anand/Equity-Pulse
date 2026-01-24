from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_financials, get_stock_price, search_market_trends
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import FundamentalAnalysis

FUNDAMENTAL_SYSTEM_PROMPT = """You are a Senior Fundamental Analyst at a hedge fund.
Your goal is to determine the intrinsic value and financial health through rigorous multi-step analysis.

**RESEARCH PROCESS** (You MUST follow ALL steps):

1. **Get Financial Statements**: Use `get_financials` to retrieve:
   - Revenue trends (year-over-year growth)
   - Net Income and profit margins
   - Total Debt and Cash position
   - Key balance sheet items

2. **Get Valuation Metrics**: Use `get_stock_price` to retrieve:
   - Current PE ratio (trailing and forward)
   - Market cap for context
   - Sector and industry classification

3. **Calculate Key Ratios** (think step-by-step):
   - Revenue Growth Rate: (Current Revenue - Prior Revenue) / Prior Revenue
   - Net Margin: Net Income / Revenue
   - Debt-to-Equity or Debt levels vs Cash
   - PE Ratio context: is it above or below industry average?

4. **Research Analyst Estimates**: Use `search_market_trends` to search:
   - "[TICKER] earnings estimates 2024 2025"
   - "[TICKER] analyst price target"

5. **Determine Valuation**:
   - Compare PE to growth rate (PEG ratio logic)
   - Compare to sector averages if available
   - Assess: Overvalued / Undervalued / Fair

CONSTRAINTS:
- You MUST call `get_financials` first.
- You MUST call `get_stock_price` for PE ratio.
- You SHOULD call `search_market_trends` for analyst context.
- Cite specific dollar amounts and percentages in your reasoning.
- If financial data is missing or erroneous, state it explicitly.
"""

run_fundamental_agent = create_structured_node(
    tools=[get_financials, get_stock_price, search_market_trends],
    system_prompt=FUNDAMENTAL_SYSTEM_PROMPT,
    schema=FundamentalAnalysis
)

async def fundamental_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    result = await run_fundamental_agent(ticker, "Fundamental Analyst")
    
    analysis = result["output"]
    if not analysis:
         analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "details": {"financial_health": "Stable", "growth_trajectory": "Stagnant", "valuation": "Fair"},
            "reasoning": "Failed to generate structured output."
        }
        
    return {"fundamental_analysis": analysis, "logs": result["logs"]}

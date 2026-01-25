from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_valuation_ratios, get_fundamental_growth_stats, search_market_trends
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import FundamentalAnalysis

# Define the Agent
FUNDAMENTAL_SYSTEM_PROMPT = """You are a Fundamental Analyst.
Your goal is to determine the intrinsic value and financial health of the company.

**RESEARCH PROCESS:**
1. **Analyze Valuation & Health**: Use `get_valuation_ratios` to check:
   - Valuation (PE, PEG, P/B).
   - Profitability (Margins, ROE).
   - Health (Debt/Equity, Current Ratio).

2. **Analyze Growth**: Use `get_fundamental_growth_stats` to check:
    - 3y Revenue and Income CAGR.

3. **Contextualize**: Use `search_market_trends` to find:
   - Earnings expectations.
   - Growth drivers (new products, expansion).

4. **Synthesize**:
   - Is the company undervalued or overvalued?
   - Is the financial foundation strong?
   - What is the growth trajectory?

CONSTRAINTS:
- Use specific numbers from the tools.
- Assess the 'Quality' of earnings.
"""

run_fundamental_agent = create_structured_node(
    tools=[get_valuation_ratios, get_fundamental_growth_stats, search_market_trends],
    system_prompt=FUNDAMENTAL_SYSTEM_PROMPT,
    schema=FundamentalAnalysis
)

async def fundamental_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    session_id = state.get("session_id")
    result = await run_fundamental_agent(ticker, "Fundamental Analyst", session_id=session_id)
    
    analysis = result["output"]
    if not analysis:
         analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "details": {"financial_health": "Stable", "growth_trajectory": "Stagnant", "valuation": "Fair"},
            "reasoning": "Failed to generate structured output."
        }
        
    return {"fundamental_analysis": analysis, "logs": result["logs"]}

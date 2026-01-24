from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_financials
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import FundamentalAnalysis

FUNDAMENTAL_SYSTEM_PROMPT = """You are a Senior Fundamental Analyst.
Your goal is to determine the intrinsic value and financial health of the company.

PROCESS:
1.  **Analyze Financials**: Use `get_financials` to look at Revenue, Net Income, and Balance Sheet health.
2.  **Evaluate Growth**: Is top-line growing? Are margins expanding or compressing?
3.  **Assess Valuation**: Based on the data, is the stock Overvalued, Undervalued, or Fairly Valued?
4.  **Synthesize**: Generate the final structured report.

CONSTRAINTS:
- Use specific dollar amounts/percentages from the tools.
"""

run_fundamental_agent = create_structured_node(
    tools=[get_financials],
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

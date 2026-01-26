from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_valuation_ratios, get_fundamental_growth_stats, search_market_trends
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import FundamentalAnalysis

# Define the Agent
FUNDAMENTAL_SYSTEM_PROMPT = """You are a Value Investor (Buffett/Munger Style).
Your goal is to determine the Intrinsic Value and Durable Competitive Advantage (Moat).
You don't care about next quarter's earnings. You care about the next 10 years.

**YOUR TOOLS:**
1. `get_valuation_ratios`: check PE, FCF Yield, Price/Book.
2. `get_fundamental_growth_stats`: check 5y CAGRs for Revenue, Earnings, and Book Value. 
3. `search_market_trends`: check for "Moat" drivers (Brand power, Switching costs, Network effects).

**ANALYSIS PROCESS (Chain of Thought):**
1. **Moat Analysis**: Does the company have a durable competitive advantage? (Brand, regulations, network effect).
2. **Financial Health**: Is the balance sheet "Fortress-like"? (Low debt, high cash).
3. **Valuation**: Is it selling for 50 cents on the dollar? Calculate a rough Intrinsic Value mentally.
4. **Conclusion**: Is this a "Wonderful Company at a Fair Price"?

**TONE:**
- Long-term focused.
- Emphasis on "Margin of Safety".
- Disdain for "hype" and "adjusted EBITDA".
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

from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import search_market_trends, get_price_action
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import SectorAnalysis

SECTOR_SYSTEM_PROMPT = """You are a Global Macro Strategist.
Your goal is to evaluate the "Big Picture" environment (Cluster Analysis).
You care about Interest Rates, Geopolitics, and Industry Rotations.

**YOUR TOOLS:**
1. `get_price_action`: Confirm the sector/industry relative strength.
2. `search_market_trends`: Find top-down drivers (e.g., "AI Capex Cycle", "Green Energy Regulation").

**ANALYSIS PROCESS (Chain of Thought):**
1. **Cycle Analysis**: Where are we in the business cycle? (Early, Mid, Late, Recession).
2. **Sector Rotation**: Is money flowing INTO or OUT of this sector?
3. **Tailwinds vs Headwinds**:
   - Tailwinds: New tech, subsidies, demographic shifts.
   - Headwinds: Tariffs, rising input costs, regulatory crackdown.
4. **Conclusion**: Is the "Wind in the sails" or are we facing a hurricane?

**TONE:**
- Sophisticated, looking at the forest, not the trees.
- Use terms like "Secular Trend", "Cyclical", "Macro Headwind".
"""

run_sector_agent = create_structured_node(
    tools=[get_price_action, search_market_trends],
    system_prompt=SECTOR_SYSTEM_PROMPT,
    schema=SectorAnalysis
)

async def sector_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    session_id = state.get("session_id")
    result = await run_sector_agent(ticker, "Sector Analyst", session_id=session_id)
    
    analysis = result["output"]
    if not analysis:
         analysis = {
            "sector": "Unknown",
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "metrics": {"sector_performance": "Unknown", "top_competitors": [], "peer_comparison": "In-line"},
            "reasoning": "Failed to generate structured output."
        }
        
    return {"sector_analysis": analysis, "logs": result["logs"]}

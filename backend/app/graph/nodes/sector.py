from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import search_market_trends, get_price_action
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import SectorAnalysis

SECTOR_SYSTEM_PROMPT = """You are a Sector Analyst.
Your goal is to evaluate the industry landscape, competitive position, and sector trends.

1.  **Identify Sector**: Use `get_price_action` to confirm the sector and industry classification.
2.  **Analyze Trends**: Use `search_market_trends` to find:
    - Sector tailwinds/headwinds (e.g. "EV demand slowing", "AI boom").
    - Regulatory changes.
    - Market share shifts.
3.  **Synthesize**: Determine if the sector environment is Favorable, Neutral, or Challenging.

Output concise analysis.
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

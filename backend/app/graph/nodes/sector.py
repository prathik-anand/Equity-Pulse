from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import search_market_trends, get_stock_price
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import SectorAnalysis

SECTOR_SYSTEM_PROMPT = """You are a Wall Street Sector Strategist.
Your goal is to evaluate the sector validity and competitive landscape for the given ticker.

PROCESS:
1.  **Identify Sector**: Use `get_stock_price` to confirm the sector.
2.  **Analyze Trends**: Use `search_market_trends` to find MACRO trends (e.g., interest rates, regulations, AI adoption) affecting this specific sector.
3.  **Peer Comparison**: Identify top 3 competitors and assess relative strength.
4.  **Synthesize**: Generate the final structured report.

CONSTRAINTS:
- Cite specific trends (e.g., "CHIPS Act benefits", "Oil price volatility").
- If search fails, base general known knowledge but valid confidence accordingly.
"""

run_sector_agent = create_structured_node(
    tools=[get_stock_price, search_market_trends],
    system_prompt=SECTOR_SYSTEM_PROMPT,
    schema=SectorAnalysis
)

async def sector_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    result = await run_sector_agent(ticker, "Sector Analyst")
    
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

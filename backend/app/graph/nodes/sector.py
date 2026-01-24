from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import search_market_trends, get_stock_price
from app.graph.agent_factory import create_agent, run_agent_and_log
import json

SECTOR_SYSTEM_PROMPT = """You are a Sector Strategist.
Your job is to analyze the industry sector of the given ticker.

1. First, use `get_stock_price` to confirm the company and its sector (often in the summary/info, or just infer it).
2. Use `search_market_trends` to find how this sector is performing YTD (Year to Date) and any major trends (AI boom, rate cuts, etc.).
3. Compare the company to its peers/competitors.

Return a JSON object with:
- sector: "Technology", "Healthcare", etc.
- signal: "BULLISH", "BEARISH", or "NEUTRAL"
- confidence: float
- metrics: { "sector_performance_ytd": "approx %", "peer_comparison": "Outperforming/Lagging" }
- reasoning: "Explanation of sector tailwinds or headwinds."

IMPORTANT: Return ONLY the JSON object.
"""

sector_agent = create_agent([get_stock_price, search_market_trends], SECTOR_SYSTEM_PROMPT)

async def sector_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    result = await run_agent_and_log(sector_agent, ticker, "Sector Analyst")
    
    try:
        clean_json = result["output"].replace("```json", "").replace("```", "").strip()
        analysis = json.loads(clean_json)
    except Exception as e:
        result["logs"].append(f"Sector Analyst: Error parsing JSON - {e}")
        analysis = {
            "sector": "Unknown",
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "metrics": {},
            "reasoning": f"Failed to parse output. Raw: {result['output'][:100]}..."
        }
        
    return {"sector_analysis": analysis, "logs": result["logs"]}

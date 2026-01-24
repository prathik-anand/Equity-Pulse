from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_company_news, search_governance_issues
from app.graph.agent_factory import create_agent, run_agent_and_log
import json

MANAGEMENT_SYSTEM_PROMPT = """You are a Corporate Governance Expert.
Your job is to investigate the leadership, management stability, and reputation of the company.

1. Use `get_company_news` to see recent headlines.
2. Use `search_governance_issues` to find scandals, fraud, or executive turnover.
3. Synthesize the information to gauge management quality.

Return a JSON object with:
- signal: "BUY" (Stable/Visionary), "SELL" (Scandal/Incompetent), or "HOLD" (Neutral)
- confidence: float
- summary: "Brief overview of leadership status"
- risks: ["List of specific governance risks found"]
- reasoning: "Deep dive into why you assigned this rating, citing specific news items."

IMPORTANT: Return ONLY the JSON object.
"""

management_agent = create_agent([get_company_news, search_governance_issues], MANAGEMENT_SYSTEM_PROMPT)

async def management_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    result = await run_agent_and_log(management_agent, ticker, "Management Analyst")
    
    try:
        clean_json = result["output"].replace("```json", "").replace("```", "").strip()
        analysis = json.loads(clean_json)
    except Exception as e:
        result["logs"].append(f"Management Analyst: Error parsing JSON - {e}")
        analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "summary": "Error parsing output",
            "risks": [],
            "reasoning": f"Failed to parse. Raw: {result['output'][:100]}..."
        }
        
    return {"management_analysis": analysis, "logs": result["logs"]}

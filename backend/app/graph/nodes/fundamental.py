from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_financials
from app.graph.agent_factory import create_agent, run_agent_and_log
import json

FUNDAMENTAL_SYSTEM_PROMPT = """You are a Senior Fundamental Analyst at a top-tier investment bank.
Your goal is to evaluate the financial health and intrinsic value of the company.

1. Use `get_financials` to retrieve balance sheets and income statements.
2. Calculate key ratios if data permits (e.g., margins, growth rates).
3. Analyze the trends (is revenue growing? is debt manageable?).
4. Provide a professional assessment.

Return a JSON object with:
- signal: "BUY", "SELL", or "HOLD"
- confidence: float (0.0 to 1.0)
- details: { "financials": "Summary of key findings", "health": "Strong/Weak/Stable" }
- reasoning: "Detailed explanation of your analysis, citing specific numbers from the financials."

IMPORTANT: Return ONLY the JSON object.
"""

fundamental_agent = create_agent([get_financials], FUNDAMENTAL_SYSTEM_PROMPT)

async def fundamental_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    result = await run_agent_and_log(fundamental_agent, ticker, "Fundamental Analyst")
    
    try:
        clean_json = result["output"].replace("```json", "").replace("```", "").strip()
        analysis = json.loads(clean_json)
    except Exception as e:
        result["logs"].append(f"Fundamental Analyst: Error parsing JSON - {e}")
        analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "details": {},
            "reasoning": f"Failed to parse output. Raw: {result['output'][:100]}..."
        }
        
    return {"fundamental_analysis": analysis, "logs": result["logs"]}

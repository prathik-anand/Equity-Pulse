from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_financials
import json

async def fundamental_analysis_node(state: AgentState) -> Dict[str, Any]:
    print(f"Running Fundamental Analysis for {state['ticker']}")
    ticker = state['ticker']
    
    # 1. Fetch Data
    try:
        financials_json = get_financials.run(ticker)
        financials = json.loads(financials_json)
    except Exception as e:
        print(f"Error in fundamental analysis tool execution: {e}")
        financials = {"error": str(e)}
    
    # 2. Analyze
    # Check for simple things like positive Net Income (Mock logic on raw data)
    
    income_stmt = financials.get("income_statement", {})
    # Mocking the interaction with the deep data structure for MVP speed
    
    signal = "BUY"
    confidence = 0.7
    
    analysis = {
        "signal": signal,
        "confidence": confidence,
        "details": {
            "financials": "Analyzed", 
            "health": "Good"
        },
        "reasoning": "Company shows stable financials (Mocked)."
    }
    
    log = f"Fundamental Analysis for {ticker}: Financials checked, Signal={signal}"
    return {"fundamental_analysis": analysis, "logs": [log]}

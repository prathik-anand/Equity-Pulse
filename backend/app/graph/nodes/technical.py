from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_stock_price
import json

async def technical_analysis_node(state: AgentState) -> Dict[str, Any]:
    print(f"Running Technical Analysis for {state['ticker']}")
    ticker = state['ticker']
    
    # 1. Fetch Data
    try:
        price_data_json = get_stock_price.run(ticker)
        price_data = json.loads(price_data_json)
    except Exception as e:
        print(f"Error in technical analysis tool execution: {e}")
        price_data = {"current_price": 0, "error": str(e)}
    
    # 2. Analyze (Mocking complex logic for MVP)
    # In a real scenario, we'd use TA-Lib or pandas_ta here
    # For now, we simulate an analysis based on mocked logic or simple heuristics
    
    current_price = price_data.get("current_price", 0)
    
    signal = "HOLD"
    confidence = 0.5
    
    # Simple Heuristic Mock: 
    # If we had history, we'd check SMA50 > SMA200.
    # For MVP, let's just return the data structure.
    
    analysis = {
        "signal": signal,
        "confidence": confidence,
        "metrics": {
            "current_price": current_price,
            "rsi": 55.0, # Mocked
            "macd": "Neutral"
        },
        "reasoning": f"Current price is {current_price}. Momentum indicators are neutral."
    }
    
    log = f"Technical Analysis for {ticker}: Price={current_price}, Signal={signal}"
    return {"technical_analysis": analysis, "logs": [log]}

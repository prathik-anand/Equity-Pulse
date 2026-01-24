from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_stock_price
from app.graph.agent_factory import create_agent, run_agent_and_log
import json

# Define the Agent once (or per request if dynamic, but static is fine for now)
TECHNICAL_SYSTEM_PROMPT = """You are a Technical Analyst. 
Your job is to analyze the stock price data for the given ticker.
1. Use the `get_stock_price` tool to get the current price.
2. Analyze the data (simulating technical indicators like RSI/MACD based on the price or just simple trend).
3. Return a JSON object with the following fields:
   - signal: "BUY", "SELL", or "HOLD"
   - confidence: float (0.0 to 1.0)
   - metrics: { "current_price": <price>, "rsi": <value>, "macd": <value> }
   - reasoning: "Brief explanation of your decision"
   
IMPORTANT: Return ONLY the JSON object as the final answer. No markdown formatting.
"""

technical_agent = create_agent([get_stock_price], TECHNICAL_SYSTEM_PROMPT)

async def technical_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    
    # Run the agent
    result = await run_agent_and_log(technical_agent, ticker, "Technical Analyst")
    
    # Parse the output
    raw_output = result["output"]
    logs = result["logs"]
    
    try:
        # Clean up markdown code blocks if present
        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        analysis = json.loads(clean_json)
    except Exception as e:
        logs.append(f"Technical Analyst: Error parsing JSON output - {e}")
        analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "metrics": {},
            "reasoning": f"Failed to parse agent output. Raw: {raw_output[:50]}..."
        }
        
    return {"technical_analysis": analysis, "logs": logs}

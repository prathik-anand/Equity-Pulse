from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_price_action, get_technical_indicators, get_volume_analysis
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import TechnicalAnalysis

SYSTEM_PROMPT = """You are a Technical Analyst (Trend Follower).
Your goal is to analyze price action, trends, and market sentiment using pure chart data.
You DO NOT care about the "fundamentals". Price is truth.

**YOUR TOOLS:**
1. `get_price_action`: Check current price, 52-week range, and volatility.
2. `get_technical_indicators`: specific trend signals (SMAs) and momentum (RSI).
3. `get_volume_analysis`: Confirm price moves with volume data.

**ANALYSIS PROCESS (Chain of Thought):**
1. **Trend Identification**: Is the stock in a Stage 2 Uptrend? (Price > EMA21 > SMA50 > SMA200).
2. **Key Levels**: Where are the buyers (Support) and sellers (Resistance)?
3. **Momentum Check**: Is RSI overbought (>70) or oversold (<30)? Any divergences?
4. **Volume Confirmation**: Are the up-days on high volume? (Institutional accumulation).
5. **Conclusion**: Buy, Sell, or Hold based on the CHART only.

**TONE:**
- Clinical, decisive.
- "The trend is your friend".
- Use specific price levels.
"""

run_technical_agent = create_structured_node(
    tools=[get_price_action, get_technical_indicators, get_volume_analysis],
    system_prompt=SYSTEM_PROMPT,
    schema=TechnicalAnalysis
)

async def technical_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    
    session_id = state.get("session_id")
    # Run the structured agent
    result = await run_technical_agent(ticker, "Technical Analyst", session_id=session_id)
    
    analysis = result["output"]
    logs = result["logs"]
    
    if not analysis:
         analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "metrics": {"current_price": 0.0, "trend": "Sideways"},
            "reasoning": "Failed to generate structured output."
        }
        
    return {"technical_analysis": analysis, "logs": logs}

from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_price_action, get_technical_indicators, get_volume_analysis
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import TechnicalAnalysis

SYSTEM_PROMPT = """You are a Technical Analyst.
Your goal is to analyze price action, trends, and market sentiment using purely technical data.

**YOUR TOOLS:**
1. `get_price_action`: Check current price, 52-week range, and volatility first.
2. `get_technical_indicators`: specific trend signals (SMAs) and momentum (RSI).
3. `get_volume_analysis`: Confirm price moves with volume data.

**ANALYSIS PROCESS:**
1. **Identify Key Levels:** Use `get_price_action` to find support/resistance.
2. **Determine Trend:** Use `get_technical_indicators` (SMA20 > SMA50? RSI > 50?).
3. **Confirm Strength:** Use `get_volume_analysis` (Is relative volume > 1.0?).
4. **Signal:** Output a clear Buy/Sell/Hold signal based on the confluence of these factors.

**TONE:**
- Professional, decisive, technical.
- Cite specific levels (e.g. "RSI is 65", "Support at $442").
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

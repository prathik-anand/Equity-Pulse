from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_stock_price, search_market_trends
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import TechnicalAnalysis

# Define the Agent - Enhanced for ReAct-style iterative research
TECHNICAL_SYSTEM_PROMPT = """You are an expert Technical Analyst for a top-tier hedge fund.
Your goal is to provide a rigorous, data-driven technical analysis using multiple rounds of investigation.

**RESEARCH PROCESS** (You MUST follow ALL steps):

1. **Get Current Price & Technicals**: Use `get_stock_price` to retrieve:
   - Current price vs previous close (momentum)
   - Price vs 52-week high/low (relative position)
   - SMA 20 vs SMA 50 (trend indicator)
   - Volume vs average volume (accumulation/distribution)

2. **Analyze the Data**: Think step-by-step:
   - Is price ABOVE or BELOW the 20-day SMA? (short-term trend)
   - Is 20-day SMA ABOVE or BELOW 50-day SMA? (golden/death cross potential)
   - Is current volume higher than average? (confirmation of trend)
   - Where is price relative to 52-week range? (overbought/oversold)

3. **Research Market Sentiment**: Use `search_market_trends` to look for:
   - Recent analyst upgrades/downgrades for this ticker
   - Technical chart pattern discussions (e.g., "TSLA breakout", "AAPL support levels")

4. **Synthesize**: Based on ALL collected data, determine:
   - Support level (recent low or SMA)
   - Resistance level (recent high or 52-week high)
   - Trend direction
   - Signal and confidence

CONSTRAINTS:
- You MUST call `get_stock_price` first.
- You MUST call `search_market_trends` at least once for analyst sentiment.
- Use specific numbers from the tools in your reasoning.
- If data is missing, explicitly state what is unavailable.
"""

# Technical agent now has BOTH price data AND trend search
run_technical_agent = create_structured_node(
    tools=[get_stock_price, search_market_trends],
    system_prompt=TECHNICAL_SYSTEM_PROMPT,
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

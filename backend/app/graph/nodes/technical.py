from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_stock_price
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import TechnicalAnalysis

# Define the Agent
TECHNICAL_SYSTEM_PROMPT = """You are an expert Technical Analyst for a top-tier hedge fund. 
Your goal is to provide a highly accurate, data-driven technical analysis for the given ticker.

PROCESS:
1.  **Retrieve Price**: Use `get_stock_price` to get the current trading data.
2.  **Estimate Trends**: Based on the data, ESTIMATE the immediate trend (Bullish/Bearish) and key levels. Since you only have current price, look for recent 52-week highs/lows if available in the data, or infer volatility to Determine Support and Resistance.
3.  **Strict Output**: Return the final structured report as requested by the schema.

CONSTRAINTS:
- Use specific numbers in your reasoning.
- Do not hallucinate historical data if you don't have it (just state 'insufficient historical data' for those specific metrics).
"""

# We now create a specialized runner instead of a generic agent + parsing
run_technical_agent = create_structured_node(
    tools=[get_stock_price],
    system_prompt=TECHNICAL_SYSTEM_PROMPT,
    schema=TechnicalAnalysis
)

async def technical_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    
    # Run the structured agent
    result = await run_technical_agent(ticker, "Technical Analyst")
    
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

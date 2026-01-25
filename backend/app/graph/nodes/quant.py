from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_price_history_stats, get_fundamental_growth_stats, get_valuation_ratios
from app.graph.agent_factory import create_structured_node
from pydantic import BaseModel, Field

# Define Output Schema
class QuantAnalysisOutput(BaseModel):
    """Structured output for the Quant Analyst."""
    valuation_score: int = Field(description="Score 1-10 based on PE, PEG, P/B")
    growth_score: int = Field(description="Score 1-10 based on Revenue/Earnings CAGR")
    financial_health_score: int = Field(description="Score 1-10 based on Debt/Equity, Current Ratio")
    key_metrics: Dict[str, Any] = Field(description="Selected key metrics extracted from data")
    summary: str = Field(description="Quantitative summary of the company's financial position")

QUANT_SYSTEM_PROMPT = """You are a Quant Analyst, a master of financial mathematics.
Your goal is to purely analyze the 'hard numbers'—Financial Statements, Ratios, and Growth Rates.
You DO NOT care about 'stories', 'rumors', or 'management promises'. You strictly trust the data.

**YOUR TOOLS:**
1. `get_price_history_stats`: Fetch 10y price history & CAGR.
2. `get_fundamental_growth_stats`: Fetch 3y Revenue/Income CAGR.
3. `get_valuation_ratios`: Fetch deep ratios (ROE, PEG, Solvency).

**ANALYSIS PROCESS:**
1. **Execute Step-by-Step:** Call all three tools to build a complete dataset.
2. **Analyze Growth (CAGR):**
   - Is Price CAGR (e.g., 5y) supported by Fundamental CAGR (e.g., Revenue)?
   - Divergence (e.g., Price up 100%, Revenue flat) is a RED FLAG.
3. **Analyze Valuation:**
   - Compare PE and PEG. Is it overvalued relative to growth?
4. **Analyze Health:**
   - Check Solvency (Debt/Equity) and Liquidity (Current Ratio).
5. **Score & Output:**
   - Assign objective scores (1-10) for Valuation, Growth, and Health.

**TONE:**
- Objective, Mathematical, Concise.
- Use explicit numbers from the tools.
"""

run_quant_agent = create_structured_node(
    tools=[get_price_history_stats, get_fundamental_growth_stats, get_valuation_ratios],
    system_prompt=QUANT_SYSTEM_PROMPT,
    schema=QuantAnalysisOutput
)

async def quant_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    session_id = state.get("session_id")
    
    # Run the structured agent
    result = await run_quant_agent(ticker, "Quant Analyst", session_id=session_id)
    
    analysis = result["output"]
    logs = result["logs"]
    
    if not analysis:
         analysis = {
            "valuation_score": 0,
            "growth_score": 0,
            "financial_health_score": 0,
            "key_metrics": {},
            "summary": "Failed to generate quantitative analysis."
        }
        
    return {"quant_analysis": analysis, "logs": logs}

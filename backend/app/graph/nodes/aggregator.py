from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import PortfolioManagerOutput

CIO_SYSTEM_PROMPT = """You are the Chief Investment Officer (CIO) of a prestigious hedge fund.
Your goal is to synthesize reports from your Quant, Technical, Fundamental, Sector, and Management analysts into a cohesive Investment Memo.

**YOUR TEAM'S REPORTS:**
You will receive JSON outputs from each analyst.

**YOUR JOB:**
1.  **Arbitrate Conflicts**: If Quant says "Bearish" (High Valuation) but Technical says "Bullish" (Breakout), you must decide the strategy (e.g., "Wait for pullback" or "Momentum buy").
2.  **Synthesize, Don't Summarize**: Do not just list what others said. specific insights to build a narrative.
3.  **Risk Management**: Highlight the single biggest risk to the trade.

**OUTPUT FORMAT:**
- **Signal**: BUY, SELL, or HOLD.
- **Confidence**: 0-100%.
- **Executive Summary**: 2-3 sentences for the CEO level.
- **Investment Thesis**: The "Bull Case" narrative.
- **Bear Case**: The "Bear Case" and key risks.
- **Strategy**: Specific action (e.g. "Accumulate under $200").
"""

# No tools needed for Aggregator, it just reads context
run_cio_agent = create_structured_node(
    tools=[], 
    system_prompt=CIO_SYSTEM_PROMPT,
    schema=PortfolioManagerOutput
)

async def aggregator_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    print(f"Aggregating results for {ticker}")
    
    # Contextualize inputs for the CIO
    quant = state.get("quant_data", {})
    tech = state.get("technical_analysis", {})
    fund = state.get("fundamental_analysis", {})
    sect = state.get("sector_analysis", {})
    mgmt = state.get("management_analysis", {})
    
    context = f"""
    ANALYSIS REPORTS FOR {ticker}:
    
    1. QUANT ANALYST:
    {quant}
    
    2. TECHNICAL ANALYST:
    {tech}
    
    3. FUNDAMENTAL ANALYST:
    {fund}
    
    4. SECTOR ANALYST:
    {sect}
    
    5. MANAGEMENT ANALYST:
    {mgmt}
    
    Generate the Final Investment Memo.
    """
    
    session_id = state.get("session_id")
    # We pass the context as a "HumanMessage" implicitly via the agent runner
    # The runner expects `ticker` but here we want to pass the whole context.
    # Actually `create_structured_node` usually takes `ticker`. 
    # Hack: We format the "ticker" argument to be the whole context prompt for this specific node?
    # Or better, we rely on the fact that `create_structured_node` creates a ReAct agent that sees the message history.
    # The `agent_factory` injects `Analyze {ticker}`. 
    # I should update `agent_factory` to accept custom input, OR I can just instruct the agent in the `input` message.
    
    # In my agent_factory.py, `run_structured_agent` creates a message: `Analyze {ticker}...`. 
    # I cannot easily override that without changing the factory.
    # HOWEVER, the agent has NO tools. So it will just use its internal knowledge? No, it needs the data.
    # The data is NOT in the history because this is a new agent instance.
    
    # CRITICAL FIX: The `aggregator` needs to pass this context to the LLM.
    # Since `create_structured_node`'s inner `run_structured_agent` takes `ticker`, I will pass the HUGE string as `ticker`? 
    # No, that's messy logging.
    # Better: I will prepend the context to the system prompt dynamically? No, factory compiles it.
    
    # BEST APPROACH GIVEN CONSTRAINTS:
    # Pass the context string as the "ticker" argument. 
    # The factory says: HumanMessage(content=f"...Analyze {ticker}...")
    # So if ticker is the context, it works. It just looks ugly in logs "Analyze REPORT 1...".
    # I will do that for now as it's the robust way to get data in without refactoring the factory.
    
    result = await run_cio_agent(context, "Portfolio Manager", session_id=session_id)
    
    final_report = result["output"]
    logs = result["logs"]
    
    if not final_report:
        # Fallback
        final_report = {
            "final_signal": "HOLD",
            "confidence_score": 0.0,
            "executive_summary": "Error generating report.",
            "investment_thesis": "N/A",
            "bear_case_risks": "N/A",
            "strategy_recommendation": "Review logs."
        }
    
    # Transform to match frontend expectations if needed, but the Schema is new.
    # I will wrap it in "final_report" key structure similar to before but with richer data.
    
    # Preserving the old structure for safety while adding new fields
    formatted_report = {
        "ticker": ticker,
        "final_signal": final_report.get("final_signal", "HOLD"),
        "overall_confidence": final_report.get("confidence_score", 0.0),
        "summary": final_report.get("executive_summary", ""), # Mapping new field to old 'summary'
        "detailed_breakdown": {
            "technical": tech,
            "fundamental": fund,
            "sector": sect,
            "management": mgmt,
            "quant": quant # Added quant
        },
        # NEW FIELDS
        "investment_thesis": final_report.get("investment_thesis"),
        "bear_case_risks": final_report.get("bear_case_risks"),
        "strategy_recommendation": final_report.get("strategy_recommendation")
    }

    return {"final_report": formatted_report, "logs": logs}

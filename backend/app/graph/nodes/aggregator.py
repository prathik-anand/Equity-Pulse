from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import PortfolioManagerOutput

CIO_SYSTEM_PROMPT = """You are the Portfolio Manager (PM).
Your goal is to make the final "high-conviction" investment decision.
You must synthesize reports from 6 different analysts, including a "Risk Manager" who is trying to kill the trade.

**YOUR TEAM:**
1. Quant (Math)
2. Technical (Charts)
3. Fundamental (Value)
4. Sector (Macro)
5. Management (Forensic)
6. Risk (Devil's Advocate)

**DECISION PROCESS (Chain of Thought):**
1. **The Debate**:
   - What is the strongest Bull argument? (e.g. "Undervalued with catalysts").
   - What is the strongest Bear argument? (e.g. "Accounting irregularities" or "Technical breakdown").
   - *Directly address the Risk Manager's points.* Do not ignore them.
2. **Reconciliation**:
   - If Technicals say SELL but Fundamentals say BUY, who is right in this context? (e.g. "Fundamentals look good but waiting for technical entry").
3. **The Verdict**:
   - Assign a Signal (BUY/SELL/HOLD).
   - Assign Confidence (0.0 to 1.0). Do NOT use percentages.
4. **Final Memo**:
   - Write a clear, executive-level summary.

**TONE:**
- Decisive, Balanced, Executive.
- "We are allocating capital, not writing a wiki page".
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
    risk = state.get("risk_analysis", {})

    context = f"""
    ANALYSIS REPORTS FOR {ticker}:
    
    1. QUANT REPORT:
    {quant}
    
    2. TECHNICAL REPORT:
    {tech}
    
    3. FUNDAMENTAL REPORT:
    {fund}
    
    4. SECTOR/MACRO REPORT:
    {sect}
    
    5. MANAGEMENT/FORENSIC REPORT:
    {mgmt}
    
    6. RISK/BEAR CASE REPORT:
    {risk}
    
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
            "quant": quant,
            "risk": risk
        },
        # NEW FIELDS
        "investment_thesis": final_report.get("investment_thesis"),
        "bear_case_risks": final_report.get("bear_case_risks"),
        "strategy_recommendation": final_report.get("strategy_recommendation")
    }

    return {"final_report": formatted_report, "logs": logs}

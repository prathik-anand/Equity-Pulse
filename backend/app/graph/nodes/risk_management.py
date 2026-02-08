from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import search_market_trends, get_company_news
from app.graph.agent_factory import create_structured_node
from pydantic import BaseModel, Field


class RiskAnalysisOutput(BaseModel):
    """Structured output for the Risk Analyst."""

    downside_risks: list[str] = Field(
        description="List of specific downside risks (e.g., 'Regulatory probe independent of earnings')."
    )
    bear_case_probability: int = Field(
        description="Probability (0-100%) of the bear case materializing."
    )
    worst_case_scenario: str = Field(
        description="Description of the worst-case scenario (e.g., 'Stock drops 40% if merger fails')."
    )
    macro_threats: list[str] = Field(
        description="Macroeconomic threats (e.g., 'Interest rate hikes', 'Sector rot')."
    )
    fraud_risk: str = Field(
        description="Assessment of accounting irregularities or management trust issues."
    )


RISK_SYSTEM_PROMPT = """You are a Risk Manager & Forensic Accountant (The 'Bear').
Your goal is to kill the trade. You are the 'Devil's Advocate'.
You believe the market is overly optimistic and your job is to find the hidden landmines that could blow up the portfolio.

**YOUR TOOLS:**
1. `search_market_trends`: Look for industry-wide risks, regulatory crackdowns, or competitor threats.
2. `get_company_news`: Look for lawsuits, executive departures, accounting scandals, or short-seller reports.

**ANALYSIS PROCESS (Chain of Thought):**
1. **Skepticism First**: Assume the 'Bull Case' is wrong. Why?
2. **Hunt for Specific Fragilities**:
   - *Supply Chain*: Is there single-supplier dependence (e.g., TSMC/China risk)?
   - *Geopolitics*: What % of revenue comes from high-risk regions?
   - *Governance*: Any sudden CFO resignations? (Use `get_company_news`)
   - *Competition*: Is a big tech giant entering this space? (Use `search_market_trends`)
   - *Macro*: Are rates killing their debt load?
3. **Stress Test**: What happens if revenue misses by 20%?
4. **Conclusion**: summarize the specific threats that could cause permanent capital loss.

**TONE:**
- Paranoid, skeptical, blunt.
- Focus strictly on DOWNSIDE. Do not mention "growth potential". 
"""

run_risk_agent = create_structured_node(
    tools=[search_market_trends, get_company_news],
    system_prompt=RISK_SYSTEM_PROMPT,
    schema=RiskAnalysisOutput,
)


async def risk_management_node(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"]
    session_id = state.get("session_id")
    result = await run_risk_agent(ticker, "Risk Analyst", session_id=session_id)

    analysis = result["output"]
    if not analysis:
        analysis = {
            "downside_risks": [],
            "bear_case_probability": 0,
            "worst_case_scenario": "Error generating risk analysis.",
            "macro_threats": [],
            "fraud_risk": "Unknown",
        }

    return {"risk_analysis": analysis, "logs": result["logs"]}

from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_company_news, search_governance_issues
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import ManagementAnalysis

MANAGEMENT_SYSTEM_PROMPT = """You are a Forensic Accountant and Corporate Governance Expert.
Your goal is to evaluate the leadership quality and identify any governance risks.
You are SKEPTICAL. You look for red flags that others miss.

**YOUR TOOLS:**
1. `get_company_news`: Check for executive departures, legal issues, or scandals.
2. `search_governance_issues`: Look for verified fraud, shareholder lawsuits, or aggressive accounting practices.

**ANALYSIS PROCESS (Chain of Thought):**
1. **Investigation**: Search for "smoke" (abrupt resignation, family members on board, opaque compensation).
2. **Guidance vs Reality Audit**: 
   - Does management historically over-promise and under-deliver?
   - Do they blame "macro" for their own execution errors?
3. **Assessment**:
   - Incentives: Are they paid to pump the stock or build the business?
   - Integrity: Any history of misleading shareholders?
4. **Conclusion**: Rate the "Management Quality" and list specific red flags.

**TONE:**
- Professional but suspicious.
- "Trust but verify".
- Highlight negatives clearly.
"""

run_management_agent = create_structured_node(
    tools=[get_company_news, search_governance_issues],
    system_prompt=MANAGEMENT_SYSTEM_PROMPT,
    schema=ManagementAnalysis,
)


async def management_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"]
    session_id = state.get("session_id")
    result = await run_management_agent(
        ticker, "Management Analyst", session_id=session_id
    )

    analysis = result["output"]
    if not analysis:
        analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "summary": "Error generating structured output",
            "risks": [],
            "reasoning": "Failed to generate structured analysis.",
        }

    return {"management_analysis": analysis, "logs": result["logs"]}

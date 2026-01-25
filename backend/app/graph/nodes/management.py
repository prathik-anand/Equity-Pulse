from typing import Dict, Any
from app.graph.state import AgentState
from app.graph.tools import get_company_news, search_governance_issues
from app.graph.agent_factory import create_structured_node
from app.graph.schemas.analysis import ManagementAnalysis

MANAGEMENT_SYSTEM_PROMPT = """You are a Corporate Governance Expert.
Your goal is to evaluate the leadership quality and governance risks.

PROCESS:
1.  **News Scan**: Use `get_company_news` for recent executive changes.
2.  **Risk Check**: Use `search_governance_issues` to screen for fraud, lawsuits, or scandals.
3.  **Evaluate**: Are leaders aligned with shareholders? Is there a history of poor capital allocation?
4.  **Synthesize**: Generate the final structured report.

CONSTRAINTS:
- **CRITICAL**: Do NOT hallucinate scandals. Only report issues found by the tools.
- If no data confirms a risk, state "No significant governance risks detected."
"""

run_management_agent = create_structured_node(
    tools=[get_company_news, search_governance_issues],
    system_prompt=MANAGEMENT_SYSTEM_PROMPT,
    schema=ManagementAnalysis
)

async def management_analysis_node(state: AgentState) -> Dict[str, Any]:
    ticker = state['ticker']
    session_id = state.get("session_id")
    result = await run_management_agent(ticker, "Management Analyst", session_id=session_id)
    
    analysis = result["output"]
    if not analysis:
         analysis = {
            "signal": "HOLD",
            "confidence": 0.0,
            "summary": "Error generating structured output",
            "risks": [],
            "reasoning": "Failed to generate structured analysis."
        }
        
    return {"management_analysis": analysis, "logs": result["logs"]}

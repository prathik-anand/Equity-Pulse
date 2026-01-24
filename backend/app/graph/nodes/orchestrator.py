from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.graph.state import AgentState

async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    print(f"Orchestrating analysis for: {state['ticker']}")
    # Since we want a full report, we don't need complex conditional logic here yet.
    # We just log and pass through. The Graph edges will define the parallel execution.
    
    return {"messages": [HumanMessage(content=f"Starting analysis for {state['ticker']}")]}

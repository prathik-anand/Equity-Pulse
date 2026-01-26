from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.graph.state import AgentState

async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    print(f"Orchestrating parallelel analysis for: {state['ticker']}")
    # Fan-out happens here implicitly by the graph edges
    return {"messages": [HumanMessage(content=f"Starting analysis for {state['ticker']}")]}

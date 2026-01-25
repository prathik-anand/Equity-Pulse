from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.orchestrator import orchestrator_node
from app.graph.nodes.technical import technical_analysis_node
from app.graph.nodes.fundamental import fundamental_analysis_node
from app.graph.nodes.sector import sector_analysis_node
from app.graph.nodes.management import management_analysis_node
from app.graph.nodes.aggregator import aggregator_node

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("technical", technical_analysis_node)
workflow.add_node("fundamental", fundamental_analysis_node)
workflow.add_node("sector", sector_analysis_node)
workflow.add_node("management", management_analysis_node)
workflow.add_node("aggregator", aggregator_node)

# Set Entry Point
workflow.set_entry_point("orchestrator")

# Define Edges: Sequential execution for cleaner logging
workflow.add_edge("orchestrator", "technical")
workflow.add_edge("technical", "fundamental")
workflow.add_edge("fundamental", "sector")
workflow.add_edge("sector", "management")
workflow.add_edge("management", "aggregator")

# End
workflow.add_edge("aggregator", END)

app = workflow.compile()

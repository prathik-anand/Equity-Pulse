from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.orchestrator import orchestrator_node
from app.graph.nodes.technical import technical_analysis_node
from app.graph.nodes.fundamental import fundamental_analysis_node
from app.graph.nodes.sector import sector_analysis_node
from app.graph.nodes.management import management_analysis_node
from app.graph.nodes.aggregator import aggregator_node
from app.graph.nodes.quant import quant_analysis_node
from app.graph.nodes.risk_management import risk_management_node

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("technical", technical_analysis_node)
workflow.add_node("fundamental", fundamental_analysis_node)
workflow.add_node("sector", sector_analysis_node)
workflow.add_node("management", management_analysis_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("quant", quant_analysis_node)
workflow.add_node("risk", risk_management_node)

# Set Entry Point
workflow.set_entry_point("orchestrator")

# Define Edges: Parallel execution (Scatter-Gather)
workflow.add_edge("orchestrator", "quant")
workflow.add_edge("orchestrator", "technical")
workflow.add_edge("orchestrator", "fundamental")
workflow.add_edge("orchestrator", "sector")
workflow.add_edge("orchestrator", "management")
workflow.add_edge("orchestrator", "risk")

# Fan-in: All nodes connect to aggregator
workflow.add_edge("quant", "aggregator")
workflow.add_edge("technical", "aggregator")
workflow.add_edge("fundamental", "aggregator")
workflow.add_edge("sector", "aggregator")
workflow.add_edge("management", "aggregator")
workflow.add_edge("risk", "aggregator")

# End
workflow.add_edge("aggregator", END)

app = workflow.compile()

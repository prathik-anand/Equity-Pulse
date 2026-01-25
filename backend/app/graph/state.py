from typing import TypedDict, Annotated, List, Dict, Any, Union
import operator

class AgentState(TypedDict):
    ticker: str
    session_id: str
    messages: Annotated[List[Dict[str, Any]], operator.add]
    logs: Annotated[List[str], operator.add]
    
    # Sub-agent outputs
    quant_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    fundamental_analysis: Dict[str, Any]
    sector_analysis: Dict[str, Any]
    management_analysis: Dict[str, Any]
    
    # Final Report
    final_report: Dict[str, Any]
    errors: List[str]

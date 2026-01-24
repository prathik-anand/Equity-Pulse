from typing import Dict, Any
from app.graph.state import AgentState

async def aggregator_node(state: AgentState) -> Dict[str, Any]:
    print(f"Aggregating results for {state['ticker']}")
    
    # Collect all outputs
    tech = state.get("technical_analysis", {})
    fund = state.get("fundamental_analysis", {})
    sect = state.get("sector_analysis", {})
    mgmt = state.get("management_analysis", {})
    
    # Simple Mock Aggregation Logic (Weighted Average of Confidences)
    # Technical: 30%, Fundamental: 40%, Sector: 20%, Management: 10%
    
    # Parse signals to scores (Buy=1, Hold=0, Sell=-1)
    def signal_to_score(sig):
        m = {"BUY": 1, "BULLISH": 1, "HOLD": 0, "NEUTRAL": 0, "SELL": -1, "BEARISH": -1}
        return m.get(str(sig).upper(), 0)
        
    s_tech = signal_to_score(tech.get("signal", "HOLD"))
    s_fund = signal_to_score(fund.get("signal", "HOLD"))
    s_sect = signal_to_score(sect.get("signal", "HOLD"))
    s_mgmt = signal_to_score(mgmt.get("signal", "HOLD"))
    
    weighted_score = (s_tech * 0.3) + (s_fund * 0.4) + (s_sect * 0.2) + (s_mgmt * 0.1)
    
    final_signal = "HOLD"
    if weighted_score > 0.3:
        final_signal = "BUY"
    elif weighted_score < -0.3:
        final_signal = "SELL"
    
    # Calculate weighted confidence from individual agents
    c_tech = tech.get("confidence", 0.5)
    c_fund = fund.get("confidence", 0.5)
    c_sect = sect.get("confidence", 0.5)
    c_mgmt = mgmt.get("confidence", 0.5)
    
    # Same weights as signal: Tech 30%, Fund 40%, Sector 20%, Mgmt 10%
    overall_confidence = (c_tech * 0.3) + (c_fund * 0.4) + (c_sect * 0.2) + (c_mgmt * 0.1)
    
    final_report = {
        "ticker": state['ticker'],
        "final_signal": final_signal,
        "overall_confidence": round(overall_confidence, 2),
        "summary": f"Our AI Agents have analyzed {state['ticker']} and recommend a {final_signal}. Technical indicators is {tech.get('signal')}, Fundamental is {fund.get('signal')}.",
        "detailed_breakdown": {
            "technical": tech,
            "fundamental": fund,
            "sector": sect,
            "management": mgmt
        }
    }
    
    return {"final_report": final_report, "logs": [f"Aggregator: Generated final report. Signal={final_signal}"]}

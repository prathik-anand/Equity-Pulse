
import asyncio
import os
from dotenv import load_dotenv

# Load env before imports to ensure keys are present
load_dotenv()

from app.graph.graph import app

async def run_test():
    print("------------------------------------------------------------------")
    print("🚀 STARTING AGENT GRAPH VERIFICATION")
    print("------------------------------------------------------------------")
    
    # Run the graph
    inputs = {"ticker": "AAPL", "session_id": "test-session-001"}
    
    # We use ainvoke as defined in the compiled graph
    result = await app.ainvoke(inputs)
    
    print("\n------------------------------------------------------------------")
    print("✅ EXECUTION COMPLETE")
    print("------------------------------------------------------------------")
    
    final_report = result.get("final_report", {})
    
    # 1. Check if Risk Analysis exists
    risk = final_report.get("detailed_breakdown", {}).get("risk", {})
    if risk:
        print("\n[PASS] Risk Analysis Found:")
        print(f"   - Bear Case Prob: {risk.get('bear_case_probability')}%")
        print(f"   - Worst Case: {risk.get('worst_case_scenario')}")
    else:
        print("\n[FAIL] Risk Analysis MISSING!")

    # 2. Check Aggregator Summary
    summary = final_report.get("summary", "")
    print(f"\n[INFO] CIO Executive Summary:\n   {summary[:200]}...")
    
    # 3. Check for specific CoT artifacts in logs (Hard to trace here without streamer, but we check structure)
    print("\n[INFO] Full Detailed Breakdown Keys:", final_report.get("detailed_breakdown", {}).keys())

    # 4. Check if we have the new fields
    print(f"\n[INFO] Investment Thesis: {final_report.get('investment_thesis')}")
    print(f"[INFO] Bear Case Risks: {final_report.get('bear_case_risks')}")
    
if __name__ == "__main__":
    asyncio.run(run_test())

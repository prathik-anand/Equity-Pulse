import asyncio
from app.graph.nodes.fundamental import run_fundamental_agent
from app.graph.schemas.analysis import FundamentalAnalysis
from app.graph.state import AgentState


async def test_fundamental_agent():
    print("--- Testing Fundamental Agent & Schema Persistence ---")
    ticker = "NVDA"

    # Mock State
    state = {
        "ticker": ticker,
        "session_id": "test_session",
    }

    print(f"Running Fundamental Agent for {ticker}...")
    try:
        # Note: We are running the agent node logic directly or via the graph hook?
        # Let's try to invoke the chain directly if possible, or verify schema instantiation
        from app.graph.nodes.fundamental import fundamental_analysis_node

        result = await fundamental_analysis_node(state)
        analysis = result.get("fundamental_analysis")

        if not analysis:
            print("FAILED: No analysis returned.")
            return

        details = analysis.get("details", {})

        # Check for new keys
        new_keys = ["altman_z_score", "beneish_m_score", "return_on_capital_employed"]
        print("\nChecking for New Metrics in Output:")
        for key in new_keys:
            val = getattr(details, key, "MISSING")
            # If it's a dict (from model_dump), it might be access via string
            if val == "MISSING" and isinstance(details, dict):
                val = details.get(key, "MISSING")
            elif hasattr(details, key):
                val = getattr(details, key)

            print(f"- {key}: {val}")

        print("\n✅ Schema Verification Complete")

    except Exception as e:
        print(f"FAILED with error: {e}")


if __name__ == "__main__":
    asyncio.run(test_fundamental_agent())

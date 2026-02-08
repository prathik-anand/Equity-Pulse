import asyncio
from app.graph.tools import get_risk_metrics


async def test_tools():
    ticker = "NVDA"
    print(f"\n--- Verifying Risk Metrics for {ticker} ---")

    # 1. Test get_risk_metrics
    print("\n1. Testing get_risk_metrics...")
    try:
        res = get_risk_metrics.invoke({"ticker": ticker})
        print(res[:2000])  # Print full output
    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(test_tools())

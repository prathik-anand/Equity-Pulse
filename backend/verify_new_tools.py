import asyncio
from app.graph.tools import get_insider_trades, get_ownership_data, get_advanced_ratios


async def verify_tools():
    ticker = "NVDA"
    print(f"--- Verifying Tools for {ticker} ---")

    print("\n1. Testing get_insider_trades...")
    try:
        # tool is synchronous
        res = get_insider_trades.invoke({"ticker": ticker})
        print(res[:500] + "...")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n2. Testing get_ownership_data...")
    try:
        res = get_ownership_data.invoke({"ticker": ticker})
        print(res[:500] + "...")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n3. Testing get_advanced_ratios...")
    try:
        res = get_advanced_ratios.invoke({"ticker": ticker})
        print(res[:1000] + "...")
    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(verify_tools())

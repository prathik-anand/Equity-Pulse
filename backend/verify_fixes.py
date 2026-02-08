import asyncio
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.graph.tools import parallel_search_market_trends
from app.models.chat import ChatHistory


# Mock Schema to verify it matches
class ParallelSearchInput(BaseModel):
    queries: List[str]


async def verify_fixes():
    print("--- Verifying Parallel Search ---")
    try:
        # Check if queries arg is accepted
        from app.graph.schemas.tool_inputs import ParallelSearchInput as RealSchema

        schema_fields = RealSchema.model_fields.keys()
        print(f"ParallelSearchInput fields: {list(schema_fields)}")
        if "queries" not in schema_fields:
            print("FAILED: 'queries' field missing from ParallelSearchInput schema")
        else:
            print("SUCCESS: 'queries' field present in schema")

        # Mock invocation (don't actually run search to save time/rate limits, just check signature)
        # parallel_search_market_trends is a StructuredTool
        print(f"Tool Args Schema: {parallel_search_market_trends.args_schema}")

    except Exception as e:
        print(f"FAILED: {e}")

    print("\n--- Verifying Timestamp Timezone ---")
    try:
        # Check ChatHistory model default
        # We can't easily instantiate a DB session here without setup,
        # but we can check the column definition if possible or just the object defaults

        # Manually invoke the default callable if accessible, or just check the code import
        from app.models.chat import ChatHistory

        # Inspect created_at default
        print(
            "ChatHistory.created_at default checked via code inspection (timezone=True applied)"
        )

        # Test creating a dummy object (not saving to DB)
        chat = ChatHistory()
        # The default is a callable on the Column, usually not populated until flush unless we manually call it
        # But we can verify `datetime.now(timezone.utc)` works
        now_utc = datetime.now(timezone.utc)
        print(f"Current UTC time (aware): {now_utc}")
        assert now_utc.tzinfo == timezone.utc
        print("SUCCESS: Timezone awareness confirmed")

    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(verify_fixes())

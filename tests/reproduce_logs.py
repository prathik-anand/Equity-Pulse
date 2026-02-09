import asyncio
import json
import sys
import os

import sys
from unittest.mock import MagicMock

# Mock langfuse before importing logger
sys.modules["langfuse"] = MagicMock()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from app.core.log_stream import stream_manager
from app.graph.logger import AgentLogger


async def reproduce():
    session_id = "test_session"
    agent_name = "TestAgent"

    logger = AgentLogger(agent_name, session_id=session_id)

    print(f"--- Simulating Log Event ---")
    # Simulate a log event
    await logger.stream_event("info", "Test message", {"foo": "bar"})

    # Check what's stored in stream_manager
    logs = stream_manager.get_logs(session_id)

    print(f"Stored Logs Count: {len(logs)}")
    if len(logs) > 0:
        first_log = logs[0]
        print(f"Log Type: {type(first_log)}")
        print(f"Log Content: {first_log}")

        if isinstance(first_log, str):
            print("\nFAIL: Log is stored as a STRING (double-encoded JSON).")
            try:
                parsed = json.loads(first_log)
                print(f"Parsed Content: {parsed}")
            except:
                print("Could not parse string as JSON")
        elif isinstance(first_log, dict):
            print("\nSUCCESS: Log is stored as a DICT (structured object).")
        else:
            print(f"\nUNKNOWN: Log is type {type(first_log)}")


if __name__ == "__main__":
    asyncio.run(reproduce())

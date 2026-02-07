import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath("/home/prathik/personal/projects/EquityPulse/backend"))

from app.db.session import async_session
from app.models.chat import ChatHistory
from sqlalchemy import select, desc


async def main():
    async with async_session() as db:
        # Get the most recent assistant message
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.role == "assistant")
            .order_by(desc(ChatHistory.created_at))
            .limit(1)
        )
        msg = result.scalar_one_or_none()

        if msg:
            print(f"Message ID: {msg.id}")
            print(f"Content Preview: {msg.content[:50]}...")
            print(f"Tool Calls (Thoughts): {msg.tool_calls}")
        else:
            print("No assistant messages found.")


if __name__ == "__main__":
    asyncio.run(main())

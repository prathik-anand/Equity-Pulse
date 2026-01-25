import asyncio
from typing import AsyncGenerator
from collections import defaultdict
import logging

class LogStreamManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogStreamManager, cls).__new__(cls)
            cls._instance.active_streams = defaultdict(list)
            cls._instance.logger = logging.getLogger("LogStreamManager")
        return cls._instance

    async def broadcast(self, session_id: str, message: str):
        """
        Push a message to all active queues for the given session_id.
        """
        if session_id in self.active_streams:
            # We copy the list to avoid modification issues during iteration if a client disconnects
            # though disconnect usually happens in the get_stream loop.
            queues = self.active_streams[session_id]
            for q in queues:
                try:
                    await q.put(message)
                except Exception as e:
                    self.logger.error(f"Failed to put message in queue for session {session_id}: {e}")

    async def get_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        Yields messages for the given session_id using SSE format.
        """
        queue = asyncio.Queue()
        self.active_streams[session_id].append(queue)
        
        try:
            while True:
                message = await queue.get()
                # Server-Sent Events format: "data: <content>\n\n"
                # We assume message is a simple string for now.
                # If we want JSON, we should json.dumps it before.
                yield f"data: {message}\n\n"
                queue.task_done()
        except asyncio.CancelledError:
            self.logger.info(f"Stream cancelled for session {session_id}")
        finally:
            if session_id in self.active_streams:
                try:
                    self.active_streams[session_id].remove(queue)
                    if not self.active_streams[session_id]:
                        del self.active_streams[session_id]
                except ValueError:
                    pass

stream_manager = LogStreamManager()

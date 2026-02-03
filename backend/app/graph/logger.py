from datetime import datetime
from enum import IntEnum
import logging
import os
import asyncio
import json
from langfuse import Langfuse
from app.core.log_stream import stream_manager

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

class AgentLogger:
    _langfuse = None

    def __init__(self, agent_name: str, level: int = LogLevel.INFO, session_id: str = None):
        self.agent_name = agent_name
        self.level = level
        self.session_id = session_id
        self.logs = []
        # Get standard python logger
        self.sys_logger = logging.getLogger(f"agent.{agent_name}")
        
        # Try to capture the event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

        # Initialize Langfuse singleton if not already done
        if AgentLogger._langfuse is None:
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
            
            if public_key and secret_key:
                AgentLogger._langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
            else:
                self.sys_logger.warning("Langfuse credentials not found. Observability will be disabled.")

    async def stream_event(self, event_type: str, content: str, payload: dict = None):
        """
        Directly streams a structured event to the frontend and Langfuse.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 1. Prepare Payload
        full_payload = {
            "type": event_type,
            "timestamp": timestamp,
            "agent": self.agent_name,
            "content": content,
            # Merge additional details
            **(payload or {})
        }
        
        # Also append to local memory for legacy compatibility
        # We serialize it to JSON string so it survives passing around in state
        json_str = json.dumps(full_payload)
        self.logs.append(json_str)

        if not self.session_id:
            return

        # 2. Broadcast to Frontend
        coro = stream_manager.broadcast(self.session_id, json_str)
        try:
             # Try using the captured loop if it matches the current context or if we are in a thread
            if self.loop and self.loop.is_running():
                try:
                    # if we are in the loop, create_task
                    if asyncio.get_running_loop() is self.loop:
                        self.loop.create_task(coro)
                    else:
                        # we are in another thread, allow threadsafe
                        asyncio.run_coroutine_threadsafe(coro, self.loop)
                except RuntimeError:
                        # in a thread with no loop, use threadsafe
                        asyncio.run_coroutine_threadsafe(coro, self.loop)
            else:
                    # Fallback
                    asyncio.get_running_loop().create_task(coro)
        except Exception:
            pass

        # 3. Send to Langfuse
        if AgentLogger._langfuse:
            try:
                sanitized_trace_id = self.session_id.replace("-", "")
                AgentLogger._langfuse.create_event(
                    name=f"{self.agent_name}-{event_type}",
                    trace_context={"trace_id": sanitized_trace_id},
                    level="INFO",
                    metadata=full_payload,
                    input=content
                )
            except Exception as e:
                self.sys_logger.error(f"Langfuse error: {e}")

    def log_tool_start(self, tool_name: str, args: dict):
        # Sync wrapper for async stream
        # This is a hack because our logger interface is sync in parts of the code
        # We use the captured loop to schedule the async event
        msg = f"Using {tool_name}..."
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.stream_event("tool", msg, {"tool_name": tool_name, "args": args, "status": "start"}), 
                self.loop
            )

    def log_thought(self, thought_text: str):
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.stream_event("thought", thought_text), 
                self.loop
            )

    def _log(self, level_name: str, level_val: int, message: str):
        # Legacy/Standard Logger Support
        # We try to infer structure if it comes from the old calls
        if level_val >= self.level:
            # Check if this is arguably a lifecycle event
            if "Activated" in message or "Analysis Completed" in message:
                 if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.stream_event("lifecycle", message),
                        self.loop
                    )
            elif "Starting analysis" in message:
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.stream_event("info", message),
                        self.loop
                    )
            
            # Emit to Console always
            self.sys_logger.log(level_val, message)

    def debug(self, message: str):
        self._log("DEBUG", LogLevel.DEBUG, message)

    def info(self, message: str):
        self._log("INFO", LogLevel.INFO, message)

    def warning(self, message: str):
        self._log("WARNING", LogLevel.WARNING, message)

    def error(self, message: str, exc: Exception = None):
        if exc:
            import traceback
            tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
            # Get the last meaningful line of code context if possible
            message = f"{message} | {exc} | Trace: {tb_lines[-1].strip()}"
        self._log("ERROR", LogLevel.ERROR, message)

    def get_logs(self):
        return self.logs


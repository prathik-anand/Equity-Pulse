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

    def _log(self, level_name: str, level_val: int, message: str):
        # 1. Capture for Frontend/History (Locally kept for compatibility if needed, but primary is Langfuse)
        if level_val >= self.level:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{self.agent_name}] {level_name}: {message}"
            self.logs.append(log_entry)
            
            # Stream to Frontend (Hybrid Mode)
            # Stream to Frontend (Hybrid Mode)
            if self.session_id:
                # Detect Type for Rich UI
                msg_type = "info"
                clean_content = message
                
                if "Tool Usage:" in message: 
                    msg_type = "tool"
                    clean_content = message.replace("Tool Usage:", "").strip()
                elif "Insight:" in message: 
                    msg_type = "thought" 
                    clean_content = message.replace("Insight:", "").strip()
                elif "Activated" in message or "Analysis Completed" in message:
                    msg_type = "lifecycle"

                payload = {
                    "type": msg_type,
                    "timestamp": timestamp,
                    "agent": self.agent_name,
                    "message": message,
                    "content": clean_content
                }

                coro = stream_manager.broadcast(self.session_id, json.dumps(payload))
                try:
                    # 1. Try using the captured loop if it matches the current context or if we are in a thread
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
                         # 2. Fallback: try to get current loop (if we didn't capture one in init)
                         asyncio.get_running_loop().create_task(coro)
                except Exception as e:
                    pass

            # 2. Send to Langfuse
            if AgentLogger._langfuse and self.session_id:
                try:
                    # Sanitize trace_id: Langfuse expects 32-char hex, so remove hyphens from UUID
                    sanitized_trace_id = self.session_id.replace("-", "")
                    
                    # Use create_event directly (v3 SDK)
                    AgentLogger._langfuse.create_event(
                        name=f"log-{level_name.lower()}",
                        trace_context={"trace_id": sanitized_trace_id},
                        level=level_name if level_name in ['DEBUG', 'WARNING', 'ERROR'] else 'DEFAULT',
                        metadata={
                            "message": message,
                            "agent": self.agent_name,
                            "level_val": level_val,
                            "type": msg_type
                        },
                        input=message
                    )
                except Exception as e:
                    self.sys_logger.error(f"Failed to send log to Langfuse: {e}")
            
        # 3. Emit to System/Console (Standard Logging)
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


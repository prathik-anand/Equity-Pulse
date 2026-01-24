from datetime import datetime
from enum import IntEnum
import logging

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

class AgentLogger:
    def __init__(self, agent_name: str, level: int = LogLevel.INFO):
        self.agent_name = agent_name
        self.level = level
        self.logs = []
        # Get standard python logger
        self.sys_logger = logging.getLogger(f"agent.{agent_name}")

    def _log(self, level_name: str, level_val: int, message: str):
        # 1. Capture for Frontend
        if level_val >= self.level:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] [{self.agent_name}] {level_name}: {message}")
            
        # 2. Emit to System/Console (Standard Logging)
        # Map our IntEnum to standard logging levels (they match mostly: DEBUG=10, INFO=20, WARN=30, ERROR=40)
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

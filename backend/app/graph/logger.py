from datetime import datetime
from enum import IntEnum

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

    def _log(self, level_name: str, level_val: int, message: str):
        if level_val >= self.level:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs.append(f"[{timestamp}] [{self.agent_name}] {level_name}: {message}")

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

# Backend Developer & Agent Guide

This document outlines the architectural standards, coding conventions, and best practices for the **EquityPulse** backend. All developers (human and AI) are expected to follow these guidelines to ensure maintainability, scalability, and code quality.

## 1. Code Organization & Architecture

We follow a layered architecture using **FastAPI**.

*   **`app/api/endpoints/`**: **Controllers/Routers**.
    *   *Responsibility:* Handle HTTP requests/responses, validate inputs (via Pydantic), and delegate work to Services.
    *   *Rule:* Keep logic minimal here. No SQL queries or complex business logic.
*   **`app/services/`**: **Business Logic Layer**.
    *   *Responsibility:* Orchestrate workflows, handle complex business rules, interact with the Database or external APIs (via Utils).
    *   *Example:* `analysis_runner.py` orchestrates the graph execution and DB updates.
*   **`app/graph/`**: **Agent/AI Logic**.
    *   *Responsibility:* LangGraph nodes, workflows, and state management. This is a specialized "Service" layer for AI.
*   **`app/core/`**: **Infrastructure**.
    *   *Responsibility:* Database connections (`database.py`), Configuration (`config.py`), Logging setup.
*   **`app/models/`**: **Data Access Layer (ORM)**.
    *   *Responsibility:* SQLAlchemy table definitions.
*   **`app/schemas/`**: **Data Transfer Objects (DTOs)**.
    *   *Responsibility:* Pydantic models for request/response validation.
*   **`app/utils/`**: **Helpers**.
    *   *Responsibility:* Pure functions, formatting, simple data manipulation.

## 2. SOLID Principles in Practice

*   **Single Responsibility Principle (SRP):**
    *   **Scope:** Applies to EVERYTHING. From architectural layers down to individual functions.
    *   *Bad (Layer Level):* A route function that validates input, queries the DB, calculates results, and formats the JSON response.
    *   *Good (Layer Level):* A route function that calls a Service. The Service calls a Repo (or uses DB session) and a Utility for calculation.
    *   *Bad (Function Level):* A function `process_data(data)` that cleans the data, calculates metrics, logs to DB, and sends an email.
    *   *Good (Function Level):* Break it down!
        ```python
        def process_data(data):
            cleaned = clean_data(data)
            metrics = calculate_metrics(cleaned)
            save_metrics(metrics)
            notify_user(metrics)
        ```
    *   **Small Functions:** Don't be afraid to write small helper functions (5-10 lines) inside a file if they do one specific thing well. This makes code readable and testable.
*   **Dependency Injection (DI):**
    *   Use FastAPI's `Depends` for everything external (DB sessions, Settings, Services).
    *   *Why:* Makes testing easier (we can mock the DB).
    *   *Example:*
        ```python
        @router.post("/analyze")
        async def analyze(request: Request, db: AsyncSession = Depends(get_db)):
            # ...
        ```

## 3. Writing Utilities & Reusable Functions

Utilities should be **stateless** and **pure** (same input = same output) whenever possible.

*   **Location:** `app/utils/`
*   **Naming:** Verb-noun phrases (e.g., `format_currency`, `calculate_moving_average`).

### Example: Date Formatter
*Bad:*
```python
# In the middle of a route handler
date_str = datetime.now().strftime("%Y-%m-%d")
```

*Good (`app/utils/date_utils.py`):*
```python
from datetime import datetime

def to_iso_date(dt: datetime) -> str:
    """Converts a datetime object to YYYY-MM-DD string."""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d")
```

## 4. Logging Standards

**DO NOT USE `print()`**. Use the Python `logging` module.
We have a custom configuration in `logging.conf`.

*   **How to Log:**
    ```python
    import logging
    
    # Get the logger (preferably 'agent' or __name__)
    logger = logging.getLogger("agent") 

    async def my_function():
        logger.info(f"Starting process for session {session_id}")
        try:
            # ... logic ...
            logger.debug("Intermediate step calculated: %s", value)
        except Exception as e:
            logger.error(f"Process failed: {e}", exc_info=True)
    ```
*   **Levels:**
    *   `DEBUG`: detailed info for diagnostics (loop variables, huge payloads).
    *   `INFO`: confirmation that things are working as expected (start/end of jobs).
    *   `WARNING`: something unexpected happened but the app can continue.
    *   `ERROR`: operation failed.

## 5. Engineering Design Principles

### High-Level Design (HLD)
*   **Async First:** Since we use FastAPI and LangGraph, block usage of synchronous I/O (like `time.sleep` or standard `requests` library) inside async endpoints. Use `asyncio.sleep` and `httpx` (or run sync code in thread pools).
*   **Event-Driven:** For long-running agent tasks (like `analysis_runner`), do not make the HTTP request wait. Return a `session_id` immediately and process in the background. (Pattern: Asynchronous Request-Reply).

### Low-Level Design (LLD)
*   **Type Hinting:** All function signatures must have type hints.
*   **Error Handling:** Catch specific exceptions, not just `Exception`. Use Pydantic for validation errors.
*   **Configuration:** No hardcoded secrets. Use `app.core.config.Settings`.

## 6. What Developers/Architects Do Here
*   **Refactoring:** Continuously move logic from Routes -> Services -> Utils.
*   **Testing:** Write `pytest` tests for Services and Utils.
*   **Documentation:** Update this file and docstrings when patterns change.

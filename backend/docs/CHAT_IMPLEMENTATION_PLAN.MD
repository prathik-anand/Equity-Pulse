# Interactive Chat System Implementation Plan

## Goal Description
Implement an interactive chat interface that allows users to ask questions about the generated financial report. The system supports "Context Selection" (annotating/highlighting text) and can update report sections based on user feedback. It leverages Gemini 3's larger context window instead of external vector memory (Mem0) for session management.

## Architecture Decisions
1.  **LangGraph vs LangChain**: We will use **LangGraph**. It is superior for stateful, multi-step agent flows.
2.  **Planner & Orchestration**: We will implement a **Plan-and-Execute** pattern.
    *   **Planner Node**: Acts as the "Context Resolver".
        *   *Input*: User Query ("Why is this risky?") + Context (Tab: "Risk", Selection: "Debt covenants...").
        *   *Action*: Rewrites query to be self-contained: "Explain why the 'Debt covenants' mentioned in the Risk Analysis tab are considered risky."
        *   *Decomposition*: If complex, breaks it down (e.g., "Check News" + "Check Financials").
    *   **Executor Node**: Iterates through steps.
3.  **IDs & Context**: We will require both `report_id` (AnalysisSession.id) and `session_id` (Client Chat Session).
4.  **Persistence**: Chat history will be saved in a **separate PostgreSQL table** `ChatHistory`.
5.  **Tools**: The Executor will have "Expert Tools" (delegating to existing agent nodes) + standard tools.

## Proposed Changes

### Backend
#### [NEW] [models/chat.py](file:///home/prathik/personal/projects/EquityPulse/backend/app/models/chat.py)
 - `ChatHistory` table:
   - `id`: UUID (PK)
   - `session_id`: String (Indexed, groups messages)
   - `report_id`: UUID (FK to AnalysisSession)
   - `role`: String (user/assistant)
   - `content`: Text
   - `timestamp`: DateTime

#### [NEW] [endpoints/chat.py](file:///home/prathik/personal/projects/EquityPulse/backend/app/api/endpoints/chat.py)
 - `POST /chat/send`: Accepts `{report_id, session_id, message, active_tab, selected_text}`.
 - **Flow**:
   1. Save user message to `ChatHistory`.
   2. Load `AnalysisSession` (Report) via `report_id`.
   3. Invoke Chat Graph.
   4. Stream response.
   5. Save assistant response to `ChatHistory`.

#### [NEW] [graph/chat_graph.py](file:///home/prathik/personal/projects/EquityPulse/backend/app/graph/chat_graph.py)
 - `ChatState`: `messages`, `report_context`, `plan`: List[str], `current_step`: int.
 - **Nodes**:
   - `planner`: Analyzes history + query -> Generates `plan`.
   - `executor`: Executes current step. Can invoke `fundamental_agent`, `technical_agent` (reusing existing nodes), or raw tools.
   - `responder`: Synthesizes execution results into final answer.
 - **Edges**: `planner` -> `executor` -> (loop) -> `responder`.

### Frontend
#### [MODIFY] [Dashboard.tsx](file:///home/prathik/personal/projects/EquityPulse/frontend/src/components/Dashboard.tsx)
 - Track `activeTab` state.
 - Pass `reportId` (AnalysisSession.id) and client-generated `chatSessionId` to `ChatWidget`.
 - Text Selection: Capture selected text + "Ask AI" tooltip.

#### [NEW] [ChatWidget.tsx](file:///home/prathik/personal/projects/EquityPulse/frontend/src/components/ChatWidget.tsx)
 - Prop: `reportId`, `sessionId`, `context` ({ tab, selection }).
 - UI: Chat stream viewer (markdown support).
 - API: Calls `/chat/send` with both IDs.

## Verification Plan

### Automated Tests
*   Run backend tests for the new chat node (to be added if time permits, otherwise manual).

### Manual Verification
1.  **Start Analysis**: Run analysis for `NVDA`.
2.  **Highlight Text**: Select a risk factor in the "Risk Analysis" tab.
3.  **Ask Question**: Click "Ask AI", type "Why is this a high risk?".
4.  **Verify Context**: Ensure the answer references the specific text selected.
5.  **History**: Ask a follow-up "What about AMD?", verify it remembers the previous context.
6.  **Report Update**: Ask "Rewrite the summary to be more bearish". Verify the UI updates the summary text.

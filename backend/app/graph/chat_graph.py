"""
Chat Graph - Advanced Multi-Agent Orchestration
Architecture: image_analyzer → query_rewriter → planner → executor → responder
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings
import json
import operator

settings = get_settings()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
)


# Define Chat State (Extended)
class ChatState(TypedDict):
    # Core state
    messages: Annotated[List[BaseMessage], operator.add]
    report_context: Dict[str, Any]
    user_metadata: Dict[str, Any]

    # NEW: Image pre-analysis result
    image_summary: Optional[str]

    # NEW: Rewritten query
    rewritten_query: Optional[str]
    sub_queries: Optional[List[str]]
    needs_web_search: bool
    needs_report_data: bool

    # Planner state
    plan: Optional[List[Dict[str, Any]]]  # Changed to list of tool dicts
    current_step: int
    execution_results: Dict[str, Any]

    # Flags and Loop Control
    needs_clarification: bool
    feedback: Optional[str]  # Feedback from validator to planner
    validator_status: Optional[
        str
    ]  # "sufficient", "insufficient", "needs_clarification"
    validation_attempts: int  # Track number of validation loops


# ============================================
# NODE 1: Image Pre-Analyzer (Early Fusion)
# ============================================
async def image_analyzer_node(state: ChatState):
    """Analyze images BEFORE query planning for better context."""
    print("--- Image Analyzer Node ---")
    image_urls = state.get("user_metadata", {}).get("image_urls", [])

    if not image_urls:
        return {"image_summary": None}

    # Build multimodal prompt for image description
    content_parts = [
        {
            "type": "text",
            "text": """Analyze these images and provide a structured summary:
1. **Content Type**: What is shown? (news article, chart, screenshot, document, etc.)
2. **Key Information**: Main text, data, numbers, or statistics visible
3. **Subject/Topic**: What is the main topic? (company name, event, product, etc.)
4. **Relevant Context**: Any dates, sources, or context that would help answer questions

Be concise but comprehensive. This will help plan how to answer the user's question.""",
        }
    ]

    for url in image_urls:
        content_parts.append({"type": "image_url", "image_url": {"url": url}})

    try:
        response = await llm.ainvoke([HumanMessage(content=content_parts)])
        print(f"Image Summary: {response.content[:200]}...")
        return {"image_summary": response.content}
    except Exception as e:
        print(f"Image analysis error: {e}")
        return {"image_summary": f"(Could not analyze image: {str(e)})"}


# ============================================
# NODE 2: Query Rewriter (with decomposition)
# ============================================
async def query_rewriter_node(state: ChatState):
    """Rewrite and decompose queries with image context."""
    print("--- Query Rewriter Node ---")
    messages = state.get("messages", [])
    image_summary = state.get("image_summary")
    report_context = state.get("report_context", {})

    user_query = messages[-1].content if messages else ""

    # Build conversation history summary
    history_summary = ""
    # Use all messages except the last one (which is the current user query)
    previous_messages = messages[:-1] if messages else []

    if previous_messages:
        history_summary = "\n".join(
            [
                f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
                for m in previous_messages
            ]
        )

    user_metadata = state.get("user_metadata", {})
    active_tab = user_metadata.get("active_tab", "Summary")
    selected_text = user_metadata.get("selected_text", None)

    rewriter_prompt = f"""You are a Query Rewriter for a financial analysis assistant.

USER'S QUERY: "{user_query}"

CONVERSATION HISTORY (if any):
{history_summary if history_summary else "(New conversation)"}

IMAGE CONTEXT (if any):
{image_summary if image_summary else "(No images attached)"}

CURRENT UI CONTEXT:
- Active Tab: {active_tab}
- Selected Text: {selected_text if selected_text else "(None)"}

AVAILABLE REPORT SECTIONS:
{list(report_context.keys()) if report_context else "(No report data)"}

YOUR TASK:
1. **Detect Ambiguity**: If the query is gibberish (e.g., "RRZZ"), highly ambiguous acronyms without context, or completely unclear, set `needs_clarification` to true.
2. **Diverse Decomposition**: If searching is needed, generate 3-4 DISTINCT sub-queries covering:
   - Competitor status/news
   - Relevant Industry Trends
   - Regulatory or Macroeconomic impacts
   - Specific entity news
   *Goal*: Maximize information gain in a single parallel search pass.
3. **Clarify Context**: Use Active Tab and Selected Text to resolve "this" or "it".
4. **Data Sources**: Determine if web search or report data is needed.

OUTPUT JSON:
{{
    "rewritten_query": "Clear, specific version of the query",
    "sub_queries": ["Competitor X news", "Industry Trend Y", "Regulatory Update Z"],
    "needs_web_search": true/false,
    "needs_report_data": true/false,
    "needs_clarification": true/false,
    "clarification_reason": "Explanation of what is unclear (only if needs_clarification is true)",
    "reasoning": "Brief explanation"
}}

Examples:
- "RRZZ" ->
  {{"rewritten_query": "RRZZ", "sub_queries": [], "needs_web_search": false, "needs_report_data": false, "needs_clarification": true, "clarification_reason": "RRZZ is an unknown term. Did you mean a specific ticker or acronym?"}}
- "How will this impact NVDA?" + image of Rubin article ->
  {{"rewritten_query": "How will NVIDIA's Rubin platform announcement impact NVDA stock?", "sub_queries": ["NVIDIA Rubin platform details", "Analyst reactions to NVIDIA Rubin", "AMD vs NVIDIA AI chip roadmap", "AI hardware market trends 2025"], "needs_web_search": true, "needs_report_data": true, "needs_clarification": false}}
"""

    try:
        response = await llm.ainvoke(rewriter_prompt)
        # Parse JSON from response
        content = response.content
        # Extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        print(f"Rewritten: {result.get('rewritten_query', user_query)[:100]}...")

        # Mapping clarification reason to specific feedback if needed
        clarification_reason = result.get("clarification_reason", "")

        return {
            "rewritten_query": result.get("rewritten_query", user_query),
            "sub_queries": result.get("sub_queries", []),
            "needs_web_search": result.get("needs_web_search", False),
            "needs_report_data": result.get("needs_report_data", True),
            "needs_clarification": result.get("needs_clarification", False),
            "feedback": clarification_reason
            if result.get("needs_clarification")
            else state.get("feedback"),
        }
    except Exception as e:
        print(f"Query rewriter error: {e}")
        return {
            "rewritten_query": user_query,
            "sub_queries": [],
            "needs_web_search": False,
            "needs_report_data": True,
            "needs_clarification": False,
        }


# ============================================
# NODE 3: Planner (with tool selection)
# ============================================
async def planner_node(state: ChatState):
    """Create execution plan with specific tool calls."""
    print("--- Planner Node ---")
    rewritten_query = state.get("rewritten_query") or (
        state["messages"][-1].content if state["messages"] else ""
    )
    sub_queries = state.get("sub_queries", [])
    needs_web = state.get("needs_web_search", False)
    needs_report = state.get("needs_report_data", True)
    image_summary = state.get("image_summary")
    report_context = state.get("report_context", {})
    metadata = state.get("user_metadata", {})

    # REPLANNING CONTEXT
    feedback = state.get("feedback", "")
    is_replanning = state.get("validator_status") == "insufficient"

    # Determine if we should use parallel search
    use_parallel_search = needs_web and sub_queries and len(sub_queries) > 1

    replanning_instruction = ""
    if is_replanning:
        print(f"!!! REPLANNING TRIGGERED !!! Feedback: {feedback}")
        replanning_instruction = f"""
## REPLANNING MODE ACTIVE
The previous plan FAILED or produced insufficient results.
FEEDBACK: "{feedback}"
CRITICAL INSTRUCTION: You MUST try a DIFFERENT strategy than the previous attempt.
- If report search failed, try `web_search` or `get_company_news`.
- If precise data is missing, try broader search terms or look for proxy metrics.
- Do NOT repeat the exact same tool calls.
"""

    planner_prompt = f"""You are a Senior Financial Analyst Planner.

## WORKFLOW INSTRUCTIONS (Level 1)
- For simple/conversational queries → direct_answer
- For questions about attached images → image context already available
- For questions needing report data → use read_report tool
- For questions needing current news/trends:
    - If multiple sub-queries are listed → use `parallel_search_market_trends` (PREFERRED for acquiring diverse data)
    - If single query → use `web_search` or `get_company_news`
- For complex queries → combine multiple tools in sequence

## AVAILABLE TOOLS (Level 2)
1. **read_report(section)**: Read from financial report. Sections: {list(report_context.keys())}
2. **web_search(query)**: Search web via DuckDuckGo for current news/trends (Single Query)
3. **parallel_search_market_trends(queries)**: Run multiple searches at once. Input is a LIST of strings.
   - Use this when 'Sub-queries' list has multiple items.
4. **get_company_news(ticker)**: Get latest news for a specific stock
5. **direct_answer**: Answer directly without tools (for simple questions)

## CURRENT CONTEXT
- Rewritten Query: "{rewritten_query}"
- Sub-queries: {sub_queries} (Multiple search queries? {use_parallel_search})
- Needs Web Search: {needs_web}
- Needs Report Data: {needs_report}
- Image Summary: {image_summary[:300] if image_summary else "None"}
- Active Tab: {metadata.get("active_tab", "Summary")}

{replanning_instruction}

## OUTPUT FORMAT (JSON)
{{
    "intent": "analysis" | "search" | "conversational",
    "plan": [
        {{"tool": "tool_name", "args": {{"key": "value"}}}},
        {{"tool": "another_tool", "args": {{...}}}}
    ]
}}

## EXAMPLES
Query: "What are the risks?" → {{"plan": [{{"tool": "read_report", "args": {{"section": "Risk"}}}}]}}
Query: "Latest news about NVDA Rubin" → {{"plan": [{{"tool": "web_search", "args": {{"query": "NVIDIA Rubin 2024 announcement"}}}}]}}
Query: "Hi" → {{"plan": [{{"tool": "direct_answer", "args": {{}}}}]}}
Complex: "How will this news affect the stock?" → {{"plan": [{{"tool": "web_search", "args": {{"query": "..."}}}}, {{"tool": "read_report", "args": {{"section": "Summary"}}}}]}}
"""

    try:
        response = await llm.ainvoke(planner_prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        plan = result.get("plan", [{"tool": "direct_answer", "args": {}}])

        # Reset execution state for new plan
        return {
            "plan": plan,
            "current_step": 0,
            "execution_results": {},  # Clear previous results to avoid confusion
            "validator_status": None,  # Reset status
            "feedback": None,
        }

    except Exception as e:
        print(f"Planner error: {e}")
        return {
            "plan": [{"tool": "direct_answer", "args": {}}],
            "current_step": 0,
        }

        return {
            "plan": plan,
            "current_step": 0,
            "execution_results": {},
        }
    except Exception as e:
        print(f"Planner error: {e}")
        return {"plan": [{"tool": "direct_answer", "args": {}}], "current_step": 0}


# ============================================
# NODE 4: Tool Executor
# ============================================
async def executor_node(state: ChatState):
    """Execute tools from the plan."""
    print("--- Executor Node ---")
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    report_context = state.get("report_context", {})

    if not plan or current_step >= len(plan):
        return {}

    step = plan[current_step]
    tool_name = step.get("tool", "direct_answer")
    args = step.get("args", {})
    print(f"Executing: {tool_name} with args: {args}")

    execution_result = ""

    try:
        if tool_name == "direct_answer":
            execution_result = "(Direct answer - no tool execution needed)"

        elif tool_name == "read_report":
            section = args.get("section", "")
            found_data = []
            for sec_name, content in report_context.items():
                if section.lower() in sec_name.lower():
                    found_data.append({"section": sec_name, "content": content})
            if found_data:
                # Return valid JSON string of the list
                execution_result = json.dumps(found_data)
            else:
                execution_result = json.dumps(
                    {
                        "error": f"Section '{section}' not found",
                        "available_sections": list(report_context.keys()),
                    }
                )

        elif tool_name == "web_search":
            query = args.get("query", "")
            try:
                from app.graph.tools import search_market_trends

                # search_market_trends is a StructuredTool, need to use .invoke
                result = search_market_trends.invoke({"query": query})
                execution_result = f"Web Search Results for '{query}':\n{result}"
            except Exception as e:
                execution_result = f"Web search error: {e}"

        elif tool_name == "get_company_news":
            ticker = args.get("ticker", "")
            try:
                from app.graph.tools import get_company_news

                # get_company_news is a StructuredTool, need to use .invoke
                result = get_company_news.invoke({"ticker": ticker})
                execution_result = f"News for {ticker}:\n{result}"
            except Exception as e:
                execution_result = f"News fetch error: {e}"

        else:
            execution_result = f"Unknown tool: {tool_name}"

    except Exception as e:
        execution_result = f"Execution error: {e}"

    result_key = f"step_{current_step}_{tool_name}"
    print(f"Result: {execution_result[:200]}...")

    return {
        "execution_results": {result_key: execution_result},
        "current_step": current_step + 1,
    }


# ============================================
# NODE 5: Responder (Final Answer)
# ============================================
# ============================================
# NODE 5: Validator (Human-Like Output Check)
# ============================================
async def validator_node(state: ChatState):
    """Reflect on execution results: Are they sufficient?"""
    print("--- Validator Node ---")

    # Check attempts
    current_attempts = state.get("validation_attempts", 0) + 1
    if current_attempts > 2:
        print(
            f"Validation: Max retries ({current_attempts}) reached. Forcing completion."
        )
        return {
            "validator_status": "sufficient",
            "feedback": "Max validation retries reached. Proceeding with best available info.",
            "validation_attempts": current_attempts,
        }
    messages = state.get("messages", [])
    user_query = messages[-1].content if messages else ""
    rewritten_query = state.get("rewritten_query") or user_query

    plan = state.get("plan", [])
    execution_results = state.get("execution_results", {})

    # Format results for validation
    results_str = ""
    has_valid_search_results = False

    for key, val in execution_results.items():
        results_str += f"\n[Step {key}]: {val}\n"
        # Simple heuristic: if we ran a search and got results without error -> trust it
        if "web_search" in key or "parallel_search" in key:
            if (
                "search error" not in str(val).lower()
                and "no results found" not in str(val).lower()
            ):
                has_valid_search_results = True

    # OPTIMIZATION: Relaxed Validation
    # If we have valid search results, assume sufficiency to save time/tokens
    # unless the query was very complex or required multi-step reasoning that isn't obvious.
    if has_valid_search_results and len(plan) <= 2:
        print("Validation: Skipping LLM check (High confidence in search results)")
        return {
            "validator_status": "sufficient",
            "feedback": "Auto-validated: Search results found.",
            "validation_attempts": current_attempts,
        }

    validator_prompt = f"""You are a Senior Financial Analyst Team Lead validating your junior's work.

ORIGINAL REQUEST: "{user_query}"
CLARIFIED INTENT: "{rewritten_query}"

THE PLAN EXECUTED:
{json.dumps(plan, indent=2)}

THE RESULTS FOUND:
{results_str if results_str else "(No results found)"}

YOUR TASK:
Determine if the results exist and are sufficient to answer the request.
- If data is missing or error occurred -> "insufficient"
- If data is good enough -> "sufficient"
- If the request is impossible/ambiguous given data -> "needs_clarification"

OUTPUT JSON:
{{
    "status": "sufficient" | "insufficient" | "needs_clarification",
    "feedback": "Strict feedback on what is missing or why it failed. Suggest a NEW strategy (e.g., 'Report search failed, try web search for [Entity]')."
}}
"""
    try:
        response = await llm.ainvoke(validator_prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        status = result.get("status", "sufficient")
        feedback = result.get("feedback", "")

        print(f"Validation: {status} - {feedback}")

    except Exception as e:
        print(f"Validator error: {e}")
        status = "sufficient"  # Fallback to answering
        feedback = ""

    return {
        "validator_status": status,
        "feedback": feedback,
        "validation_attempts": current_attempts,
    }


# ============================================
# NODE 6: Responder (Final Answer)
# ============================================
async def responder_node(state: ChatState):
    """Synthesize final answer OR ask for clarification."""
    print("--- Responder Node ---")

    # Check if we need to ask user for help
    if state.get("validator_status") == "needs_clarification":
        feedback = state.get("feedback", "")
        return {
            "messages": [HumanMessage(content=f"I need a bit more clarity. {feedback}")]
        }

    results = state.get("execution_results", {})
    report_context = state.get("report_context", {})
    image_summary = state.get("image_summary")
    rewritten_query = state.get("rewritten_query")
    user_metadata = state.get("user_metadata", {})
    image_urls = user_metadata.get("image_urls", [])
    messages = state.get("messages", [])

    user_query = messages[-1].content if messages else ""

    # Callbacks for Langfuse
    callbacks = []
    try:
        from langfuse.callback import CallbackHandler

        if hasattr(settings, "LANGFUSE_PUBLIC_KEY") and settings.LANGFUSE_PUBLIC_KEY:
            callbacks.append(CallbackHandler())
    except Exception:
        pass

    # Build context string from execution results
    context_str = ""
    for key, val in results.items():
        context_str += f"\n### {key}\n{val}\n"

    # Build final prompt
    summary_prompt = f"""You are a Senior Financial Analyst helping a portfolio manager.

## USER'S ORIGINAL QUESTION
"{user_query}"

## CLARIFIED QUESTION
"{rewritten_query if rewritten_query else user_query}"

## IMAGE ANALYSIS (if applicable)
{image_summary if image_summary else "(No images)"}

## TOOL EXECUTION RESULTS
{context_str if context_str.strip() else "(No tool execution data)"}

## REPORT CONTEXT (Reference)
{str(report_context)[:1500] if report_context else "(No report data)"}

## INSTRUCTIONS
1. **DIRECTLY answer the user's question** - this is your #1 priority
2. Use information from the image analysis if relevant
3. Incorporate tool results (web search, report data)
4. Cite specific facts, numbers, and sources
5. If information is missing, acknowledge it honestly
6. Format with Markdown for readability
7. Keep response focused and concise
"""

    # Handle multimodal if images present (for visual reference)
    if image_urls:
        content_parts = [{"type": "text", "text": summary_prompt}]
        for url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": url}})
        msg = HumanMessage(content=content_parts)
        response = await llm.ainvoke([msg], config={"callbacks": callbacks})
    else:
        response = await llm.ainvoke(summary_prompt, config={"callbacks": callbacks})

    return {"messages": [response]}


# ============================================
# GRAPH CONSTRUCTION
# ============================================
chat_workflow = StateGraph(ChatState)

# Add all nodes
chat_workflow.add_node("image_analyzer", image_analyzer_node)
chat_workflow.add_node("query_rewriter", query_rewriter_node)
chat_workflow.add_node("planner", planner_node)
chat_workflow.add_node("executor", executor_node)
chat_workflow.add_node("validator", validator_node)  # NEW
chat_workflow.add_node("responder", responder_node)


# Conditional entry: if images → analyze first, else → rewriter
def route_entry(state: ChatState):
    image_urls = state.get("user_metadata", {}).get("image_urls", [])
    if image_urls:
        return "image_analyzer"
    return "query_rewriter"


chat_workflow.set_conditional_entry_point(
    route_entry,
    {"image_analyzer": "image_analyzer", "query_rewriter": "query_rewriter"},
)


# Conditional edge from Query Rewriter (New: Ambiguity Check)
def route_query_rewrite(state: ChatState):
    if state.get("needs_clarification"):
        print("--- Routing to Responder (Needs Clarification) ---")
        # Set validator status to trigger clarification message in responder
        state["validator_status"] = "needs_clarification"
        return "responder"
    return "planner"


chat_workflow.add_conditional_edges(
    "query_rewriter",
    route_query_rewrite,
    {"planner": "planner", "responder": "responder"},
)

# Edges
chat_workflow.add_edge("image_analyzer", "query_rewriter")
# chat_workflow.add_edge("query_rewriter", "planner") # Replaced with conditional edge above
chat_workflow.add_edge("planner", "executor")


# Conditional edge: loop executor or proceed to VALIDATOR
def should_continue_execution(state: ChatState):
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    if current_step < len(plan):
        return "executor"
    return "validator"  # Changed from "responder" to "validator"


chat_workflow.add_conditional_edges(
    "executor",
    should_continue_execution,
    {"executor": "executor", "validator": "validator"},
)


# Conditional edge: Validation Logic
def route_validation(state: ChatState):
    status = state.get("validator_status", "sufficient")

    if status == "insufficient":
        print(">>> Validation Failed: Re-planning execution strategy.")
        return "planner"

    return "responder"  # Covers "sufficient" and "needs_clarification"


chat_workflow.add_conditional_edges(
    "validator", route_validation, {"planner": "planner", "responder": "responder"}
)

chat_workflow.add_edge("responder", END)

# Compile
chat_app = chat_workflow.compile()

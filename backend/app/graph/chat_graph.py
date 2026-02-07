"""
Chat Graph - Advanced Multi-Agent Orchestration
Architecture: image_analyzer → query_rewriter → planner → executor → responder
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
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

    # Flags
    needs_clarification: bool


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

    rewriter_prompt = f"""You are a Query Rewriter for a financial analysis assistant.

USER'S QUERY: "{user_query}"

CONVERSATION HISTORY (if any):
{history_summary if history_summary else "(New conversation)"}

IMAGE CONTEXT (if any):
{image_summary if image_summary else "(No images attached)"}

AVAILABLE REPORT SECTIONS:
{list(report_context.keys()) if report_context else "(No report data)"}

YOUR TASK:
1. Clarify vague references (e.g., "this" → the specific subject from image/context)
2. Decompose complex queries into sub-questions
3. Determine what data sources are needed

OUTPUT JSON:
{{
    "rewritten_query": "Clear, specific version of the query",
    "sub_queries": ["sub-question 1", "sub-question 2"],
    "needs_web_search": true/false,
    "needs_report_data": true/false,
    "reasoning": "Brief explanation"
}}

Examples:
- "How will this impact NVDA?" + image of Rubin article → 
  {{"rewritten_query": "How will NVIDIA's Rubin platform announcement impact NVDA stock?", "sub_queries": ["What is the Rubin announcement?", "How might this affect stock price?"], "needs_web_search": true, "needs_report_data": true}}
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

        return {
            "rewritten_query": result.get("rewritten_query", user_query),
            "sub_queries": result.get("sub_queries", []),
            "needs_web_search": result.get("needs_web_search", False),
            "needs_report_data": result.get("needs_report_data", True),
        }
    except Exception as e:
        print(f"Query rewriter error: {e}")
        return {
            "rewritten_query": user_query,
            "sub_queries": [],
            "needs_web_search": False,
            "needs_report_data": True,
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

    planner_prompt = f"""You are a Senior Financial Analyst Planner.

## WORKFLOW INSTRUCTIONS (Level 1)
- For simple/conversational queries → direct_answer
- For questions about attached images → image context already available
- For questions needing report data → use read_report tool
- For questions needing current news/trends → use web_search tool
- For complex queries → combine multiple tools in sequence

## AVAILABLE TOOLS (Level 2)
1. **read_report(section)**: Read from financial report. Sections: {list(report_context.keys())}
2. **web_search(query)**: Search web via DuckDuckGo for current news/trends
3. **get_company_news(ticker)**: Get latest news for a specific stock
4. **direct_answer**: Answer directly without tools (for simple questions)

## CURRENT CONTEXT
- Rewritten Query: "{rewritten_query}"
- Sub-queries: {sub_queries}
- Needs Web Search: {needs_web}
- Needs Report Data: {needs_report}
- Image Summary: {image_summary[:300] if image_summary else "None"}
- Active Tab: {metadata.get("active_tab", "Summary")}

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
        print(f"Plan: {plan}")

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
async def responder_node(state: ChatState):
    """Synthesize final answer from all context."""
    print("--- Responder Node ---")
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

# Edges
chat_workflow.add_edge("image_analyzer", "query_rewriter")
chat_workflow.add_edge("query_rewriter", "planner")
chat_workflow.add_edge("planner", "executor")


# Conditional edge: loop executor or proceed to responder
def should_continue(state: ChatState):
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    if current_step < len(plan):
        return "executor"
    return "responder"


chat_workflow.add_conditional_edges(
    "executor",
    should_continue,
    {"executor": "executor", "responder": "responder"},
)

chat_workflow.add_edge("responder", END)

# Compile
chat_app = chat_workflow.compile()

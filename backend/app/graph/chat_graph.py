from typing import List, Dict, Any, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings
import json
import operator

settings = get_settings()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL_NAME, # Use Pro for planning/reasoning
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0
)

# Define Chat State
class ChatState(TypedDict):
    # Core state
    messages: Annotated[List[BaseMessage], operator.add]
    report_context: Dict[str, Any] # Full financial report data
    user_metadata: Dict[str, Any] # {active_tab: str, selected_text: str}
    
    # Planner state
    plan: Optional[List[str]]
    current_step: int
    execution_results: Dict[str, Any] # Store results from executor steps
    
    # Flags
    needs_clarification: bool

# Planner Prompt
planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Financial Analyst Planner.
Your goal is to understand the User's Query and the Context (what tab they are on) to create a step-by-step Execution Plan.

CONTEXT:
Active Tab: {active_tab}
Selected Text: {selected_text}

Available Capabilities:
1. `read_report`: Read specific sections of the financial report. (Use this for MOST queries).
2. `direct_answer`: If the query is simple, conversational, or the data is already in context.

NOTE: You do NOT have access to external tools, live search, or other agents. You MUST retrieve information from the `report_context` using `read_report`.

OUTPUT FORMAT (JSON):
{{
    "intent": "analysis" | "clarification" | "conversational",
    "plan": [
        "step 1 description",
        "step 2 description"
    ],
    "needs_clarification": false
}}

Example:
User: "What are the risks?" -> Plan: ["read_report(section='Risk')", "Synthesize risk factors"]
User: "Summary of management" -> Plan: ["read_report(section='Management')", "Summarize leadership"]

Keep plans concise (max 3 steps).
"""),
    ("user", "{messages}")
])

async def planner_node(state: ChatState):
    print("--- Planner Node ---")
    messages = state['messages']
    metadata = state.get('user_metadata', {})
    
    # Extract metadata
    active_tab = metadata.get('active_tab', 'Summary')
    selected_text = metadata.get('selected_text', 'None')
    
    # Format prompt
    chain = planner_prompt | llm | JsonOutputParser()
    
    try:
        # Get the last message content
        last_message = messages[-1].content if messages else ""
        
        result = await chain.ainvoke({
            "messages": last_message,
            "active_tab": active_tab,
            "selected_text": selected_text
        })
        
        return {
            "plan": result.get("plan", []),
            "current_step": 0,
            "execution_results": {}
        }
    except Exception as e:
        print(f"Planner Error: {e}")
        # Fallback plan
        return {"plan": ["direct_answer"], "current_step": 0}

# Node 3: Executor
async def executor_node(state: ChatState):
    print("--- Executor Node ---")
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    report_context = state.get("report_context", {})
    
    if not plan or current_step >= len(plan):
        return {} # Done
        
    step_description = plan[current_step]
    print(f"Executing: {step_description}")
    
    execution_result = ""
    
    # SIMPLE EXECUTOR LOGIC
    # 1. Check if step requires reading report data
    lower_step = step_description.lower()
    
    if "read" in lower_step or "check" in lower_step or "analyze" in lower_step or "summarize" in lower_step:
        # Naive keyword matching to find relevant sections
        found_data = []
        for section, content in report_context.items():
            # If the section name is in the step (e.g. "Risk")
            if section.lower() in lower_step:
                found_data.append(f"--- Section: {section} ---\n{str(content)[:3000]}...") # Limit context size
            # If "summary" requested, try to find Summary section
            if "summary" in lower_step and "summary" in section.lower():
                found_data.append(f"--- Section: {section} ---\n{str(content)[:3000]}...")
        
        if found_data:
            execution_result = "\n".join(found_data)
        elif report_context:
            # Fallback: Provide keys if specific section not found but data exists
             execution_result = f"Available Report Sections: {list(report_context.keys())}."
        else:
             execution_result = "No report data found in context."
            
    else:
        # General reasoning step
        execution_result = "Proceeding with reasoning based on previous context."

    result_key = f"step_{current_step}"
    
    return {
        "execution_results": {result_key: f"Step: {step_description}\nResult: {execution_result}"},
        "current_step": current_step + 1
    }

# Node 4: Responder (Consolidator)
async def responder_node(state: ChatState):
    print("--- Responder (Consolidator) Node ---")
    # Consolidates execution results and formulates final answer
    results = state.get("execution_results", {})
    plan = state.get("plan", [])
    report_context = state.get("report_context", {})
    
    # Verify Langfuse
    callbacks = []
    try:
        from langfuse.callback import CallbackHandler
        settings = get_settings()
        if hasattr(settings, "LANGFUSE_PUBLIC_KEY") and settings.LANGFUSE_PUBLIC_KEY:
             callbacks.append(CallbackHandler())
    except ImportError:
        pass
    except Exception:
        pass # Graceful degradation
        
    
    # If direct answer, just answer
    if plan == ["direct_answer"]:
        response = await llm.ainvoke(state['messages'], config={"callbacks": callbacks})
        return {"messages": [response]}

    # Construct a rich context prompt
    context_str = ""
    for key, val in results.items():
        context_str += f"\n{val}\n"
        
    summary_prompt = f"""
    You are a Senior Financial Analyst interacting with a portfolio manager.
    
    USER QUERY: {state['messages'][-1].content}
    
    EXECUTION PLAN & RESULTS:
    {context_str}
    
    REPORT DATA (Partial Context):
    {str(report_context)[:2000]}
    
    INSTRUCTIONS:
    1. Synthesize the findings into a clear, professional answer.
    2. USE DATA from the Execution Results. cite specific numbers/risks.
    3. If the data is missing, admit it. Do not hallucinate.
    4. Format with Markdown (headers, bullet points).
    5. **CRITICAL**: Do NOT output the internal JSON plan, "intent", or "steps". Only provide the final natural language response to the user.
    """
    
    response = await llm.ainvoke(summary_prompt, config={"callbacks": callbacks})
    
    return {"messages": [response]}

# Build Graph
chat_workflow = StateGraph(ChatState)

chat_workflow.add_node("planner", planner_node)
chat_workflow.add_node("executor", executor_node)
chat_workflow.add_node("responder", responder_node)

chat_workflow.set_entry_point("planner")

# Conditional edge: Loop executor until plan is done
def should_continue(state: ChatState):
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    if current_step < len(plan):
        return "executor"
    return "responder"

chat_workflow.add_edge("planner", "executor")
chat_workflow.add_conditional_edges(
    "executor",
    should_continue,
    {
        "executor": "executor",
        "responder": "responder"
    }
)
chat_workflow.add_edge("responder", END)

chat_app = chat_workflow.compile()

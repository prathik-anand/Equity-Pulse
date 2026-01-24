from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Any, Dict
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure API Key is set
if "GOOGLE_API_KEY" not in os.environ:
    print("WARNING: GOOGLE_API_KEY not found in environment.")

try:
    llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0)
except Exception as e:
    print(f"Error initializing LLM: {e}")
    # Fallback to avoid crash on import if key is missing
    llm = None

async def run_agent_and_log(agent_executor, ticker: str, agent_name: str) -> Dict[str, Any]:
    """
    Runs a LangGraph ReAct agent and extracts logs from the messages.
    """
    # Create the input message
    inputs = {"messages": [HumanMessage(content=f"Analyze {ticker}.")]}
    
    logs = []
    final_response = {}
    
    logs.append(f"{agent_name}: Starting analysis for {ticker}...")
    
    # We invoke the agent. The results contains 'messages'.
    # Note: create_react_agent returns a CompiledGraph.
    result = await agent_executor.ainvoke(inputs)
    
    # Extract logs from the message history
    # We skip the first human message
    messages = result.get("messages", [])
    
    for msg in messages:
        if isinstance(msg, AIMessage):
            # If it has tool_calls, log them
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc['name']
                    args = tc['args']
                    # Pretty print for search tools
                    if "search" in name or "news" in name:
                        query = args.get("query") or args.get("ticker", "")
                        logs.append(f"{agent_name} -> Searching: \"{query}\" ({name})")
                    elif "get_stock_price" in name:
                         logs.append(f"{agent_name} -> Checking Price for: {args.get('ticker')}")
                    elif "get_financials" in name:
                         logs.append(f"{agent_name} -> Fetching Financials for: {args.get('ticker')}")
                    else:
                        logs.append(f"{agent_name} -> Tool Call: {name} args={args}")
            
            # If it has content (thought or final answer), log it
            if msg.content:
                text_content = ""
                if isinstance(msg.content, list):
                    for part in msg.content:
                        if isinstance(part, dict) and "text" in part:
                            text_content += part["text"]
                        elif isinstance(part, str):
                            text_content += part
                else:
                    text_content = str(msg.content)

                 # Clean up newlines for cleaner logs
                content_preview = text_content[:100].replace('\n', ' ') + "..." if len(text_content)>100 else text_content.replace('\n', ' ')
                logs.append(f"{agent_name}: {content_preview}")
                
        # We could also log ToolMessage (outputs) if we want detailed dataLogs
        # but that might be too verbose. Let's stick to AI thoughts for now.
    
    # The last message is usually the final answer
    if messages and isinstance(messages[-1], AIMessage):
        content = messages[-1].content
        if isinstance(content, list):
            # Extract text from multimodal content list
            final_text = ""
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    final_text += part["text"]
                elif isinstance(part, str):
                    final_text += part
            final_response = final_text
        else:
            final_response = str(content)
             
    logs.append(f"{agent_name}: Analysis complete.")
    
    return {
        "output": final_response,
        "logs": logs
    }

def create_agent(tools: List[Any], system_prompt: str):
    """
    Factory to create a ReAct agent properly configured.
    """
    return create_react_agent(llm, tools, prompt=system_prompt)

def create_structured_node(tools: List[Any], system_prompt: str, schema: Any):
    # ... imports ...
    from langgraph.prebuilt import create_react_agent
    from langchain_core.prompts import ChatPromptTemplate
    from app.graph.logger import AgentLogger
    import asyncio
    
    # 1. Create the base ReAct agent for tool usage
    research_agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    async def retry_with_backoff(coro_func, *args, max_retries=3, **kwargs):
        for i in range(max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except Exception as e:
                if "503" in str(e) or "overloaded" in str(e).lower():
                    wait_time = (2 ** i) * 1  # 1s, 2s, 4s
                    print(f"Warning: Model overloaded (503). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
        raise Exception("Max retries exceeded for model call.")

    async def run_structured_agent(ticker: str, agent_name: str) -> Dict[str, Any]:
        """
        Custom runner using AgentLogger with Retries.
        """
        logger = AgentLogger(agent_name)
        logger.info(f"Starting analysis for {ticker}")
        
        # Proper State Initialization for ReAct Agent
        # LangGraph ReAct expects 'messages' in the state.
        inputs = {"messages": [HumanMessage(content=f"Analyze {ticker}. Gather all necessary data using tools.")]}
        
        try:
            # Step 1: Run Reasoning Loop (with Retry)
            # We wrap the invoke in a retry block for 503s
            result = await retry_with_backoff(research_agent.ainvoke, inputs)
            messages = result["messages"]
            
            # Log the journey
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                             tool_name = tc['name']
                             args = tc['args']
                             logger.info(f"Tool Call: {tool_name} {args}")
                    
                    if msg.content:
                         # Log full thought without truncation
                         thought_text = str(msg.content).strip()
                         logger.info(f"Thought: {thought_text}")

            # Step 2: Synthesis with Structured Output (with Retry)
            structured_llm = llm.with_structured_output(schema)
            final_prompt = messages + [HumanMessage(content="Based on the above research, generate the final structured report.")]
            
            logger.info("Generating final structured report...")
            analysis_object = await retry_with_backoff(structured_llm.ainvoke, final_prompt)
            
            final_output = analysis_object.model_dump()
            logger.info("Analysis generated successfully.")
            
        except Exception as e:
            logger.error("Analysis failed", exc=e)
            final_output = None
            
        return {
            "output": final_output,
            "logs": logger.get_logs()
        }
        
    return run_structured_agent

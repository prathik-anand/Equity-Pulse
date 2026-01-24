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
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
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

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from typing import List, Any, Dict
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure API Key is set
if "GOOGLE_API_KEY" not in os.environ:
    print("WARNING: GOOGLE_API_KEY not found in environment.")

try:
    llm = ChatGoogleGenerativeAI(model=os.environ.get("GEMINI_MODEL_NAME", "gemini-3-flash-preview"), temperature=0)
except Exception as e:
    print(f"Error initializing LLM: {e}")
    # Fallback to avoid crash on import if key is missing
    llm = None

async def run_agent_and_log(agent_executor, ticker: str, agent_name: str, session_id: str = None) -> Dict[str, Any]:
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
    
    async def run_structured_agent(ticker: str, agent_name: str, session_id: str = None) -> Dict[str, Any]:
        """
        Custom runner using AgentLogger with Retries.
        """
        logger = AgentLogger(agent_name, session_id=session_id)
        logger.info(f"Starting analysis for {ticker}")
        
        async def retry_with_backoff(coro_func, *args, max_retries=3, **kwargs):
            for i in range(max_retries):
                try:
                    return await coro_func(*args, **kwargs)
                except Exception as e:
                    if "503" in str(e) or "overloaded" in str(e).lower():
                        wait_time = (2 ** i) * 1  # 1s, 2s, 4s
                        logger.info(f"AI is thinking... (Model overloaded, retrying in {wait_time}s)")
                        await asyncio.sleep(wait_time)
                    else:
                        raise e
            raise Exception("Max retries exceeded for model call.")
        
        # Proper State Initialization for ReAct Agent
        # LangGraph ReAct expects 'messages' in the state.
        from datetime import datetime
        date_context = f"Current Date: {datetime.now().strftime('%A, %B %d, %Y')}"
        inputs = {"messages": [HumanMessage(content=f"{date_context}\n\nAnalyze {ticker}. Gather all necessary data using tools.")]}
        
        try:
            # Wrapper for descriptive logging
            class StreamLoggingHandler(BaseCallbackHandler):
                def __init__(self, logger):
                    self.logger = logger
                
                def on_tool_start(self, serialized, input_str, **kwargs):
                    tool_name = serialized.get("name")
                    if tool_name in ["unknown", "LanguageModel"]:
                        return
                        
                    # Parse input_str to dict if possible
                    args = {}
                    try:
                        args = eval(input_str) if isinstance(input_str, str) else input_str
                    except:
                        args = input_str
                    
                    # LOG FULL DETAILS AS REQUESTED
                    self.logger.log_tool_start(tool_name, args)

                def on_llm_end(self, response, **kwargs):
                    import ast
                    if response.generations and response.generations[0]:
                        generation = response.generations[0][0]
                        text = generation.text or ""
                        
                        # Handle multimodal/complex content
                        message = getattr(generation, "message", None)
                        if message and hasattr(message, "content"):
                            if isinstance(message.content, list):
                                parts = []
                                for part in message.content:
                                    if isinstance(part, dict) and "text" in part:
                                        parts.append(part["text"])
                                    elif isinstance(part, str):
                                        parts.append(part)
                                text = "".join(parts)
                            elif isinstance(message.content, str):
                                text = message.content
                                
                        # This section is just cleaning up artifacts, not truncating
                        msg_str = text.strip()
                        if (msg_str.startswith("[") and ("type" in msg_str or "text" in msg_str)) or msg_str.startswith("{"):
                            try:
                                data = ast.literal_eval(msg_str)
                                if isinstance(data, list):
                                    text = "".join([d.get("text", "") for d in data if isinstance(d, dict) and "text" in d])
                                elif isinstance(data, dict):
                                    text = data.get("text", "")
                            except:
                                pass

                        clean_text = text.strip()
                        if clean_text:
                            # LOG FULL CONTENT - NO TRUNCATION
                            self.logger.log_thought(clean_text)

            
            # Step 1: Run Reasoning Loop (Sequentially via ReAct)
            # We ONLY run invoke. We do NOT run astream_events beforehand, preventing double execution.
            stream_handler = StreamLoggingHandler(logger)
            
            # Log Start
            logger.info(f"[{agent_name}] -> Activated. Beginning research phase.")
            
            result = await retry_with_backoff(research_agent.ainvoke, inputs, config={"callbacks": [stream_handler]})
            messages = result["messages"]

            # Step 2: Synthesis with Structured Output
            # We use include_raw=True to handle cases where the model wraps JSON in markdown
            structured_llm = llm.with_structured_output(schema, include_raw=True)
            
            # Clean System Prompt (No "Prompt Engineering" hacks needed if we parse correctly)
            json_system_prompt = SystemMessage(content="You are a data conversion agent. Extract the findings from the conversation above and format them into the requested JSON schema.")
            
            # Filter out old SystemMessage (usually index 0)
            cleaned_messages = [m for m in messages if not isinstance(m, SystemMessage)]
            
            final_prompt = [json_system_prompt] + cleaned_messages + [HumanMessage(content="Generate the final JSON output.")]
            
            import json
            import re
            
            def clean_json_string(text: str) -> str:
                """Removes markdown code blocks and whitespace."""
                text = text.strip()
                # Remove ```json and ``` patterns
                text = re.sub(r'^```json\s*', '', text)
                text = re.sub(r'^```\s*', '', text)
                text = re.sub(r'\s*```$', '', text)
                return text.strip()

            # Helper to extract text from potential list content
            def extract_text_from_message(content: Any) -> str:
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                        elif isinstance(part, str):
                            text_parts.append(part)
                    return "".join(text_parts)
                return str(content)

            try:
                logger.info(f"[{agent_name}] -> Generating final structured report...")
                # Response will be {"parsed": BaseModel | None, "raw": BaseMessage, "parsing_error": ...}
                response = await retry_with_backoff(structured_llm.ainvoke, final_prompt)
                
                if response['parsed'] is not None:
                    final_output = response['parsed'].model_dump()
                else:
                    # Parsing failed automatically, likely due to markdown. Let's fix it manually.
                    logger.warning(f"[{agent_name}] -> Automatic parsing failed. Attempting manual cleanup.")
                    raw_content = extract_text_from_message(response['raw'].content)
                    cleaned_json = clean_json_string(raw_content)
                    
                    # Manual Validation using the Pydantic Schema
                    # schema is the Pydantic class passed in arguments
                    try:
                        # First load into dict
                        data_dict = json.loads(cleaned_json)
                        # Then validate via Pydantic
                        validated_obj = schema(**data_dict)
                        final_output = validated_obj.model_dump()
                        logger.info(f"[{agent_name}] -> Manual cleanup successful.")
                    except Exception as validation_error:
                         # Last Resort: Retry Loop (but cleaner)
                        logger.warning(f"[{agent_name}] -> Manual cleanup failed: {validation_error}. Retrying execution...")
                        repair_prompt = [json_system_prompt] + cleaned_messages + [HumanMessage(content=f"Previous attempt produced invalid JSON:\n{raw_content}\n\nError: {str(validation_error)}\n\nPlease generate ONLY the raw valid JSON.")]
                        retry_response = await retry_with_backoff(structured_llm.ainvoke, repair_prompt)
                        
                        if retry_response['parsed']:
                            final_output = retry_response['parsed'].model_dump()
                        else:
                            # Final desperation: try to parse the retry raw output
                            final_output = json.loads(clean_json_string(extract_text_from_message(retry_response['raw'].content)))

            except Exception as e:
                logger.error(f"[{agent_name}] -> Critical Failure in JSON Generation", exc=e)
                final_output = None
            
            logger.info(f"[{agent_name}] -> Analysis Completed.")
            
        except Exception as e:
            logger.error("Analysis failed", exc=e)
            final_output = None
            
        return {
            "output": final_output,
            "logs": logger.get_logs()
        }
        
    return run_structured_agent

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
        inputs = {"messages": [HumanMessage(content=f"Analyze {ticker}. Gather all necessary data using tools.")]}
        
        try:
            # Step 1: Run Reasoning Loop (with Streaming)
            messages = []
            
            # Use astream_events to get real-time feedback
            # We filter for relevant events to log
            async for event in research_agent.astream_events(inputs, version="v2"):
                kind = event["event"]
                
                # Log Tool Calls
                if kind == "on_tool_start":
                    tool_name = event['name']
                    # Some internal tools might not need logging or have different args structure
                    if tool_name not in ["__start__", "__end__", "LanguageModel", "CompiledGraph"]: 
                        args = event['data'].get('input')
                        logger.info(f"Tool Call: {tool_name} {args}")

                # Log Thoughts (Chat Model Stream)
                elif kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # We stream chunks, maybe we want to accumulate line by line or just log chunks?
                        # Logging every token is too much. 
                        # Better approach for "Thoughts":
                        # The ReAct agent in LangGraph emits state updates. 
                        # But astream_events gives us fine-grained control.
                        # For cleanliness, let's log when a full message is generated (on_chat_model_end) 
                        # OR if we want *true* streaming of thoughts, we'd need to emit tokens. 
                        # For now, let's stick to logging *completed* thoughts to avoid log spam, 
                        # BUT we do it *as soon as* the thought completes, not after the whole agent finishes.
                        pass
                
                elif kind == "on_chat_model_end":
                    import ast
                    # A model call finished. It might be a thought or a tool call request.
                    output = event['data'].get('output')
                    if output and isinstance(output, AIMessage):
                        text = output.content
                        if text:
                            # Handle multimodal content list
                            if isinstance(text, list):
                                parts = []
                                for part in text:
                                    if isinstance(part, dict) and "text" in part:
                                        parts.append(part["text"])
                                    elif isinstance(part, str):
                                        parts.append(part)
                                text = "".join(parts)
                            else:
                                text = str(text)

                            # Clean JSON artifacts
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
                                # Hueristic: If it's a very long final report (markdown), hide it from scratchpad
                                if len(clean_text) > 500 or "###" in clean_text:
                                    logger.info("Insight: Synthesizing gathered data into report...")
                                else:
                                    logger.info(f"Insight: {clean_text}")

            # After streaming is done, we need the final state to get the full history for synthesis
            # Since astream_events doesn't easily return the final state, we might need to rely on
            # the fact that the agent execution is done. 
            # We can re-invoke to get state or (better) just use a standard invoke but catch events via a callback?
            # Actually, astream_events returns events. To get the final state messages, we can run invoke OR
            # simpler: The ReAct agent is a graph. We can just use ".invoke" but with a custom CallbackHandler 
            # that writes to our AgentLogger. 
            
            # Let's try the Callback approach as it is cleaner for "Intercepting" logs without changing execution flow.
            # But AgentLogger is async-ish (fire and forget).
            
            # Alternative: Keep astream_events but just re-run invoke? No that's waste.
            # State extraction from astream_events is tricky.
            
            # Let's revert to a simpler "step-by-step" execution if possible?
            # LangGraph graphs are iterable.
            
            # ACTUALLY, simpler fix: 
            # Use `astream` which yields state updates.
            # As the state updates (new messages added), we log the new message.
            
            final_state = None
            async for state_update in research_agent.astream(inputs, stream_mode="values"):
                # state_update is the full state (dict with "messages").
                # We need to detect *new* messages.
                current_messages = state_update.get("messages", [])
                if current_messages:
                    last_msg = current_messages[-1]
                    # We only log if we haven't seen this message ID or it's a new step
                    # But message objects might be recreated.
                    
                    # Heuristic: If it's an AIMessage with tool_calls, log it.
                    if isinstance(last_msg, AIMessage):
                         if last_msg.tool_calls:
                             for tc in last_msg.tool_calls:
                                 # Avoid dupes? The stream yields every step. 
                                 # We need to be careful not to re-log.
                                 # Simple hack: Keep track of logged message IDs or content hashes.
                                 pass
            
            # Okay, "astream_events" is definitely the most robust for "events" (logs).
            # We just need to capture the final messages for the synthesis step.
            # We can accumulate messages from "on_chain_end" of the top level graph?
            
            # Let's go with the CallbackHandler approach. It is the standard way to inspect execution.
            # We will define a local callback handler class that wraps logger.
            
            # Setup Handler
            from langchain_core.callbacks import BaseCallbackHandler
            import ast

            class StreamLoggingHandler(BaseCallbackHandler):
                def __init__(self, logger):
                    self.logger = logger
                
                def on_tool_start(self, serialized, input_str, **kwargs):
                    tool_name = serialized.get("name")
                    if tool_name in ["unknown", "LanguageModel"]:
                        return
                        
                    # Parse input_str to dict if possible for cleaner logging
                    args = {}
                    try:
                        args = eval(input_str) if isinstance(input_str, str) else input_str
                    except:
                        args = input_str

                    # Human-readable formatting
                    log_msg = f"Using tool: {tool_name}"
                    
                    if "search" in tool_name or "trends" in tool_name:
                        query = args.get('query') if isinstance(args, dict) else str(args)
                        log_msg = f"Searching market trends: \"{query}\""
                    elif "news" in tool_name:
                        log_msg = f"Scanning latest news for {args.get('ticker', 'ticker')}"
                    elif "stock_price" in tool_name:
                        log_msg = f"Checking real-time price for {args.get('ticker', 'ticker')}"
                    elif "financials" in tool_name:
                        log_msg = f"Retrieving financial statements for {args.get('ticker', 'ticker')}"
                    elif "governance" in tool_name:
                        query = args.get('query') if isinstance(args, dict) else str(args)
                        log_msg = f"Investigating governance issues: \"{query}\""
                    else:
                        # Fallback
                        log_msg = f"Tool Call: {tool_name} {args}"
                        
                    self.logger.info(log_msg)
                         
                def on_llm_end(self, response, **kwargs):
                    # This captures thoughts (generations)
                    if response.generations and response.generations[0]:
                        generation = response.generations[0][0]
                        text = generation.text or ""
                        
                        # Try to get cleaner content from message if available
                        message = getattr(generation, "message", None)
                        if message and hasattr(message, "content"):
                            if isinstance(message.content, str):
                                text = message.content
                            elif isinstance(message.content, list):
                                # Combine text parts
                                text_parts = []
                                for part in message.content:
                                    if isinstance(part, dict) and "text" in part:
                                        text_parts.append(part["text"])
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                text = "".join(text_parts)

                        # Deep Clean: Remove generic JSON artifacts if the model output them literally
                        # Some models output `[{'type': 'text', 'text': '...'}]` as the string content
                        msg_str = text.strip()
                        if (msg_str.startswith("[") and ("type" in msg_str or "text" in msg_str)) or msg_str.startswith("{"):
                            try:
                                data = ast.literal_eval(msg_str)
                                if isinstance(data, list):
                                    text = "".join([d.get("text", "") for d in data if isinstance(d, dict) and "text" in d])
                                elif isinstance(data, dict):
                                    text = data.get("text", "")
                            except:
                                # If parsing fails, it's likely broken JSON.
                                pass

                        clean_text = text.strip()
                        if clean_text:
                            # Hueristic: If it's a very long final report (markdown), hide it from scratchpad
                            # The user can see the final report in the main UI
                            if len(clean_text) > 500 or "###" in clean_text:
                                self.logger.info("Insight: Synthesizing gathered data into report...")
                            else:
                                self.logger.info(f"Insight: {clean_text}")
                            
            stream_handler = StreamLoggingHandler(logger)
            
            # Run with callback
            result = await retry_with_backoff(research_agent.ainvoke, inputs, config={"callbacks": [stream_handler]})
            messages = result["messages"]

            # Step 2: Synthesis with Structured Output (with Retry)
            structured_llm = llm.with_structured_output(schema)
            final_prompt = messages + [HumanMessage(content="Based on the above research, generate the final structured report.")]
            
            logger.info("Generating final structured report...")
            analysis_object = await retry_with_backoff(structured_llm.ainvoke, final_prompt)
            
            final_output = analysis_object.model_dump()
            logger.info(f"{agent_name} Analysis Completed.")
            
        except Exception as e:
            logger.error("Analysis failed", exc=e)
            final_output = None
            
        return {
            "output": final_output,
            "logs": logger.get_logs()
        }
        
    return run_structured_agent

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat import ChatHistory
from app.repositories.chat import ChatRepository
from app.graph.chat_graph import chat_app
from langchain_core.messages import HumanMessage
from uuid import UUID
import json
import logging
from typing import AsyncGenerator

# Get logger
logger = logging.getLogger("agent")

class ChatService:
    def __init__(self, repo: ChatRepository):
        self.repo = repo

    async def get_report_context(self, report_id: str) -> dict:
        try:
            report_uuid = UUID(report_id)
        except ValueError:
            logger.warning(f"Invalid report ID format: {report_id}")
            return None
            
        report_session = await self.repo.get_report_by_id(report_uuid)
        
        if not report_session:
            logger.warning(f"Report not found: {report_id}")
            return None
            
        return report_session.report_data or {}

    async def save_message(self, session_id: str, report_id: str, role: str, content: str):
        try:
             report_uuid = UUID(report_id)
             await self.repo.create_message(session_id, report_uuid, role, content)
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)

    async def get_history(self, session_id: str):
        return await self.repo.get_history_by_session(session_id)

    async def stream_chat(
        self,
        session_id: str,
        message: str,
        report_context: dict,
        active_tab: str = "Summary",
        selected_text: str = None
    ) -> AsyncGenerator[str, None]:
        config = {"configurable": {"thread_id": session_id}}
        
        # Yield immediate keep-alive to flush headers
        yield json.dumps({"type": "ping"})

        # Prepare state
        input_state = {
            "messages": [HumanMessage(content=message)],
            "report_context": report_context,
            "user_metadata": {
                "active_tab": active_tab,
                "selected_text": selected_text
            }
        }
        
        logger.info(f"Starting Chat Graph for session {session_id}")
        final_answer = ""
        try:
             async for event in chat_app.astream_events(input_state, config=config, version="v1"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    # key fix: only stream tokens from the final responder node
                    # filter out planner/executor thoughts
                    node_name = event.get("metadata", {}).get("langgraph_node", "")
                    if node_name == "responder":
                        content = event["data"]["chunk"].content
                        if content:
                            final_answer += content
                            yield json.dumps({"type": "token", "content": content})
                
                elif kind == "on_chain_end" and event["name"] == "planner":
                     output = event["data"].get("output")
                     if output and "plan" in output:
                         yield json.dumps({"type": "plan", "content": output["plan"]})
                         
                elif kind == "on_chain_end" and event["name"] == "executor":
                    output = event["data"].get("output")
                    if output and "execution_results" in output:
                         yield json.dumps({"type": "execution", "content": output["execution_results"]})
                
                elif kind == "on_chain_end" and event["name"] == "responder":
                    # Capture final answer if stream was missed
                    output = event["data"].get("output")
                    if output and "messages" in output:
                        msg = output["messages"][0]
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        if content and content != final_answer:
                            # If we haven't streamed this content yet, send it now
                            yield json.dumps({"type": "token", "content": content})
                            final_answer = content

             yield json.dumps({"type": "done", "full_response": final_answer})
             
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)})

from app.repositories.chat import ChatRepository
from app.graph.chat_graph import chat_app
from langchain_core.messages import HumanMessage, AIMessage
from uuid import UUID
import json
import logging
from typing import AsyncGenerator
from datetime import datetime

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

    async def save_message(
        self,
        session_id: str,
        report_id: str,
        role: str,
        content: str,
        image_urls: list[str] = None,
        tool_calls: list[dict] = None,
    ):
        try:
            report_uuid = UUID(report_id)
            await self.repo.create_message(
                session_id, report_uuid, role, content, image_urls, tool_calls
            )
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)

    async def get_history(self, session_id: str):
        return await self.repo.get_history_by_session(session_id)

    async def get_history_by_report(self, report_id: str):
        """Fetch chat history for a specific report."""
        try:
            report_uuid = UUID(report_id)
            return await self.repo.get_history_by_report(report_uuid)
        except ValueError:
            logger.warning(f"Invalid report ID: {report_id}")
            return []

    async def get_sessions(self, report_id: str) -> list[dict]:
        """Fetch all chat sessions for a specific report."""
        try:
            report_uuid = UUID(report_id)
            return await self.repo.get_sessions_by_report(report_uuid)
        except ValueError:
            logger.warning(f"Invalid report ID: {report_id}")
            return []

    async def stream_chat(
        self,
        session_id: str,
        report_id: str,  # NEW: need report_id for history
        message: str,
        report_context: dict,
        active_tab: str = "Summary",
        selected_text: str = None,
        image_urls: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        config = {"configurable": {"thread_id": session_id}}

        # Yield immediate keep-alive to flush headers
        yield json.dumps({"type": "ping"})

        # NEW: Fetch conversation history (last 10 messages)
        history_messages = []
        try:
            history = await self.get_history_by_report(report_id)
            # Take last 10 messages (excluding current message we just saved)
            recent_history = history[-11:-1] if len(history) > 1 else []
            for msg in recent_history:
                if msg.role == "user":
                    history_messages.append(HumanMessage(content=msg.content))
                else:
                    history_messages.append(AIMessage(content=msg.content))
        except Exception as e:
            logger.warning(f"Could not fetch history: {e}")

        # Add current message
        history_messages.append(HumanMessage(content=message))

        # Prepare state with conversation history
        input_state = {
            "messages": history_messages,  # Now includes history!
            "report_context": report_context,
            "user_metadata": {
                "active_tab": active_tab,
                "selected_text": selected_text,
                "image_urls": image_urls,  # Pass images to agent
            },
        }

        # Track reasoning traces
        thoughts = []

        logger.info(
            f"Starting Chat Graph for session {session_id} with {len(history_messages)} messages"
        )
        final_answer = ""
        try:
            async for event in chat_app.astream_events(
                input_state, config=config, version="v1"
            ):
                kind = event["event"]
                node_name = event.get("metadata", {}).get("langgraph_node", "")

                if kind == "on_chat_model_stream":
                    if node_name == "responder":
                        content = event["data"]["chunk"].content
                        if content:
                            final_answer += content
                            yield json.dumps({"type": "token", "content": content})
                    elif node_name in ["planner", "query_rewriter", "image_analyzer"]:
                        content = event["data"]["chunk"].content
                        if content:
                            # We don't save raw tokens of thoughts to DB structure yet,
                            # we rely on the structured events below.
                            yield json.dumps(
                                {
                                    "type": "thought",
                                    "node": node_name,
                                    "content": content,
                                }
                            )

                elif kind == "on_tool_start":
                    name = event["name"]
                    inputs = event["data"].get("input")
                    # Capture tool start
                    thoughts.append(
                        {
                            "type": "tool",
                            "toolName": name,
                            "toolInput": inputs,
                            "status": "running",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    yield json.dumps(
                        {"type": "tool_start", "tool": name, "input": inputs}
                    )

                elif kind == "on_tool_end":
                    name = event["name"]
                    output = event["data"].get("output")
                    # Capture tool end (update last running tool)
                    # Simple heuristic: update the last tool entry
                    for t in reversed(thoughts):
                        if (
                            t.get("type") == "tool"
                            and t.get("toolName") == name
                            and t.get("status") == "running"
                        ):
                            t["status"] = "completed"
                            t["toolOutput"] = str(output)
                            break

                    yield json.dumps(
                        {"type": "tool_end", "tool": name, "output": str(output)}
                    )

                # NEW: Stream image analysis result
                elif kind == "on_chain_end" and event["name"] == "image_analyzer":
                    output = event["data"].get("output")
                    if output and "image_summary" in output:
                        content = output["image_summary"]
                        thoughts.append(
                            {
                                "type": "image_analysis",
                                "content": content,
                                "status": "completed",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        yield json.dumps(
                            {
                                "type": "image_analysis",
                                "content": content,
                            }
                        )

                # NEW: Stream query rewriter result
                elif kind == "on_chain_end" and event["name"] == "query_rewriter":
                    output = event["data"].get("output")
                    if output and "rewritten_query" in output:
                        content_obj = {
                            "rewritten_query": output.get("rewritten_query"),
                            "sub_queries": output.get("sub_queries", []),
                            "needs_web_search": output.get("needs_web_search", False),
                        }
                        thoughts.append(
                            {
                                "type": "query_rewrite",
                                "content": json.dumps(content_obj),
                                "status": "completed",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        yield json.dumps({"type": "query_rewrite", **content_obj})

                elif kind == "on_chain_end" and event["name"] == "planner":
                    output = event["data"].get("output")
                    if output and "plan" in output:
                        plan_content = output["plan"]
                        thoughts.append(
                            {
                                "type": "plan",
                                "content": json.dumps(
                                    {"plan": plan_content}
                                ),  # consistent with frontend
                                "status": "completed",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        yield json.dumps({"type": "plan", "content": plan_content})

                elif kind == "on_chain_end" and event["name"] == "executor":
                    output = event["data"].get("output")
                    if output and "execution_results" in output:
                        exec_results = output["execution_results"]
                        thoughts.append(
                            {
                                "type": "execution",
                                "content": json.dumps(
                                    {"execution_results": exec_results}
                                ),
                                "status": "completed",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        yield json.dumps(
                            {
                                "type": "execution",
                                "content": exec_results,
                            }
                        )

                elif kind == "on_chain_end" and event["name"] == "responder":
                    output = event["data"].get("output")
                    if output and "messages" in output:
                        msg = output["messages"][0]
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        if content and content != final_answer:
                            yield json.dumps({"type": "token", "content": content})
                            final_answer = content

            if final_answer:
                try:
                    await self.save_message(
                        session_id=session_id,
                        report_id=report_id,
                        role="assistant",
                        content=final_answer,
                        tool_calls=thoughts,  # Save collected traces
                    )
                except Exception as e:
                    logger.error(f"Failed to save assistant message: {e}")

            yield json.dumps({"type": "done", "full_response": final_answer})

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)})

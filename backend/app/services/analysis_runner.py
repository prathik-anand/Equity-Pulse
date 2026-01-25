from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.report import AnalysisSession
from app.graph.graph import app as graph_app
from app.core.database import AsyncSessionLocal
from app.core.database import AsyncSessionLocal
import json
from app.core.log_stream import stream_manager
import asyncio

async def run_analysis_workflow(session_id: str, ticker: str):
    print(f"Starting Background Analysis for {ticker} (Session: {session_id})")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Initialize Graph State
            initial_state = {
                "ticker": ticker,
                "session_id": str(session_id),
                "messages": [],
                "technical_analysis": {},
                "fundamental_analysis": {},
                "sector_analysis": {},
                "management_analysis": {},
                "final_report": {},
                "errors": []
            }
            
            # 2. Invoke Graph
            # invoke is sync or async? langgraph CompiledGraph is async if compiled with async nodes?
            # actually app.invoke is sync by default unless async is used.
            # But our nodes are async def. So we should use ainvoke.
            
            final_state = await graph_app.ainvoke(initial_state)
            
            # 3. Update DB with results
            result = await db.execute(select(AnalysisSession).where(AnalysisSession.session_id == session_id))
            session_obj = result.scalar_one_or_none()
            
            if session_obj:
                session_obj.status = "completed"
                session_obj.report_data = final_state.get("final_report", {})
                session_obj.summary = final_state.get("final_report", {}).get("summary", "")
                session_obj.logs = final_state.get("logs", [])
                await db.commit()
                await db.commit()
                # Notify stream of completion
                await stream_manager.broadcast(session_id, "STATUS: COMPLETED")
                print(f"Analysis completed for {ticker}")
                
        except Exception as e:
            print(f"Error in analysis workflow: {str(e)}")
            # Fetch session again to update error state
            # (In a real app, handle transaction rollback carefully)
            try:
                result = await db.execute(select(AnalysisSession).where(AnalysisSession.session_id == session_id))
                session_obj = result.scalar_one_or_none()
                if session_obj:
                    session_obj.status = "failed"
                    await db.commit()
            except:
                pass

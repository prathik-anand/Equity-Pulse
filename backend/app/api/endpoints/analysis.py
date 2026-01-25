from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.api.deps import SessionDep
from app.models.report import AnalysisSession
from app.services.analysis_runner import run_analysis_workflow
from sqlalchemy import select
from uuid import UUID
from fastapi.responses import StreamingResponse
from app.core.log_stream import stream_manager

router = APIRouter()

class AnalysisRequest(BaseModel):
    ticker: str

class AnalysisResponse(BaseModel):
    session_id: UUID
    status: str
    ticker: str

@router.post("/analysis", response_model=AnalysisResponse)
async def trigger_analysis(
    request: AnalysisRequest, 
    db: SessionDep, 
    background_tasks: BackgroundTasks
):
    """
    Trigger a new analysis session for a ticker.
    """
    # Create DB Session
    new_session = AnalysisSession(ticker=request.ticker, status="processing")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Start Background Task
    background_tasks.add_task(run_analysis_workflow, new_session.session_id, request.ticker)
    
    return AnalysisResponse(
        session_id=new_session.session_id,
        status=new_session.status,
        ticker=new_session.ticker
    )

@router.get("/analysis/{session_id}")
async def get_analysis_result(session_id: UUID, db: SessionDep):
    """
    Get the status and result of an analysis session.
    """
    result = await db.execute(select(AnalysisSession).where(AnalysisSession.session_id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
        
    return {
        "session_id": session.session_id,
        "ticker": session.ticker,
        "status": session.status,
        "created_at": session.created_at,
        "summary": session.summary,
        "report": session.report_data,
        "logs": session.logs
    }

@router.get("/analysis/{session_id}/stream")
async def stream_analysis_logs(session_id: str):
    """
    Stream logs for a specific analysis session using Server-Sent Events (SSE).
    """
    return StreamingResponse(
        stream_manager.get_stream(session_id),
        media_type="text/event-stream"
    )

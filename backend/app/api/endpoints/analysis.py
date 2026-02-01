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
    user_session_id: str

class AnalysisResponse(BaseModel):
    id: UUID
    status: str
    ticker: str
    user_session_id: str | None


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
    new_session = AnalysisSession(
        ticker=request.ticker, 
        user_session_id=request.user_session_id,
        status="processing"
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Start Background Task
    background_tasks.add_task(run_analysis_workflow, str(new_session.id), request.ticker)
    
    return AnalysisResponse(
        id=new_session.id,
        status=new_session.status,
        ticker=new_session.ticker,
        user_session_id=new_session.user_session_id
    )

@router.get("/analysis/{id}")
async def get_analysis_result(id: UUID, db: SessionDep):
    """
    Get the status and result of an analysis session.
    Returns live logs from memory during processing, or DB logs when completed.
    """
    result = await db.execute(select(AnalysisSession).where(AnalysisSession.id == id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    # Get logs: from memory if processing, from DB if completed
    if session.status == "processing":
        logs = stream_manager.get_logs(str(session.id))
    else:
        logs = session.logs or []
        
    return {
        "id": session.id,
        "ticker": session.ticker,
        "status": session.status,
        "created_at": session.created_at,
        "summary": session.summary,
        "report": session.report_data,
        "logs": logs
    }

@router.get("/analysis/{id}/stream")
async def stream_analysis_logs(id: str):
    """
    Stream logs for a specific analysis session using Server-Sent Events (SSE).
    """
    return StreamingResponse(
        stream_manager.get_stream(id),
        media_type="text/event-stream"
    )

@router.get("/history/{user_session_id}")
async def get_user_history(user_session_id: str, db: SessionDep):
    """
    Get all analysis sessions for a specific user session ID.
    """
    result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.user_session_id == user_session_id)
        .order_by(AnalysisSession.created_at.desc())
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": session.id,
            "ticker": session.ticker,
            "status": session.status,
            "created_at": session.created_at,
            "summary": session.summary
        }
        for session in sessions
    ]

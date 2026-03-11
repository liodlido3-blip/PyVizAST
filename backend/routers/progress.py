"""
Progress tracking API routes

@author: Chidc
@link: github.com/chidcGithub
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..utils.progress import progress_tracker

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{task_id}")
async def get_progress(task_id: str):
    """Get current progress state for a task"""
    state = progress_tracker.get_state(task_id)
    if not state:
        return {"error": "Task not found", "task_id": task_id}
    return state.to_dict()


@router.get("/{task_id}/stream")
async def progress_stream(task_id: str):
    """
    SSE endpoint for real-time progress updates
    Returns Server-Sent Events stream
    """
    async def event_generator():
        # First, send current state if exists
        current_state = progress_tracker.get_state(task_id)
        if current_state:
            yield current_state.to_sse()
        
        # Then stream updates
        async for event in progress_tracker.progress_generator(task_id):
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

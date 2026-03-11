"""
Frontend log receiving API routes

@author: Chidc
@link: github.com/chidcGithub
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


class FrontendLogEntry(BaseModel):
    """Frontend log entry model"""
    timestamp: str
    level: str
    message: str
    userAgent: Optional[str] = None
    url: Optional[str] = None
    reason: Optional[str] = None
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    filename: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None


class FrontendLogsRequest(BaseModel):
    """Frontend logs request model"""
    logs: List[FrontendLogEntry]


# Ensure log directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"


def ensure_logs_dir():
    """Ensure log directory exists"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/frontend")
async def receive_frontend_logs(request: FrontendLogsRequest):
    """Receive frontend logs and save to file"""
    ensure_logs_dir()
    
    # Generate log filename (by date)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"frontend-{today}.log"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            for log_entry in request.logs:
                # Format log entry
                log_line = (
                    f"[{log_entry.timestamp}] "
                    f"[{log_entry.level.upper()}] "
                    f"{log_entry.message}"
                )
                
                # Add extra info
                extras = []
                if log_entry.url:
                    extras.append(f"url={log_entry.url}")
                if log_entry.filename:
                    extras.append(f"file={log_entry.filename}:{log_entry.lineno}:{log_entry.colno}")
                if log_entry.stack:
                    extras.append(f"stack={log_entry.stack[:500]}")  # Limit stack length
                if log_entry.componentStack:
                    extras.append(f"componentStack={log_entry.componentStack[:500]}")
                
                if extras:
                    log_line += f" | {' | '.join(extras)}"
                
                f.write(log_line + "\n")
        
        logger.debug(f"Saved {len(request.logs)} frontend log entries")
        return {"status": "ok", "count": len(request.logs)}
    
    except Exception as e:
        logger.error(f"Failed to save frontend logs: {e}")
        return {"status": "error", "message": str(e)}

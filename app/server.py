from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from .session_manager import SessionManager

app = FastAPI(title="Terminal Access API")
sess_manager = SessionManager()

# --- Data Models ---
class CreateSessionRequest(BaseModel):
    name: Optional[str] = None
    distro: Optional[str] = "kali-linux" # Convenience field
    shell_command: Optional[str] = None # Advanced override
    cols: int = 120
    rows: int = 30

class CommandRequest(BaseModel):
    command: str

class SessionInfo(BaseModel):
    id: str
    name: str
    alive: bool
    created_at: float
    log_path: str = None

class HistoryItem(BaseModel):
    command: str
    timestamp: float

# --- Endpoints ---

@app.post("/sessions", response_model=SessionInfo)
def create_session(req: CreateSessionRequest):
    """Create a new terminal session."""
    # Determine shell command
    cmd = req.shell_command
    # Handle Swagger UI default value "string"
    if cmd == "string":
        cmd = None
        
    if not cmd and req.distro:
         # Use cmd.exe /c wrapper for safety
         cmd = f"cmd.exe /c wsl -d {req.distro}"
    
    session_id = sess_manager.create_session(
        name=req.name, 
        cols=req.cols, 
        rows=req.rows,
        shell_command=cmd
    )
    # Fetch full info to return
    sessions = sess_manager.list_sessions()
    session_info = next(s for s in sessions if s["id"] == session_id)
    return session_info

@app.get("/sessions", response_model=List[SessionInfo])
def list_sessions():
    """List all active terminal sessions."""
    return sess_manager.list_sessions()

@app.delete("/sessions/{session_id}")
def kill_session(session_id: str):
    """Kill a specific terminal session."""
    if sess_manager.kill_session(session_id):
        return {"status": "killed", "id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/sessions/{session_id}/command")
def send_command(session_id: str, req: CommandRequest):
    """
    Send a command to the terminal session (appends newline).
    Good for executing shell commands (ls, cd, etc).
    """
    session = sess_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not session.is_alive():
        raise HTTPException(status_code=400, detail="Session is dead")

    # Record command in history
    sess_manager.record_command(session_id, req.command)
    
    # Use send_command from TerminalAPI (blocking wait for output)
    output = session.send_command(req.command)
    return {"output": output}

@app.post("/sessions/{session_id}/input")
def send_raw_input(session_id: str, req: CommandRequest):
    """
    Send raw input to the terminal session (NO newline appended).
    Essential for interactive apps like Vim, Nano, or interactive scripts.
    """
    session = sess_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not session.is_alive():
        raise HTTPException(status_code=400, detail="Session is dead")

    # We don't record every raw keystroke in history/commands typically,
    # or we can record it as 'raw input'.
    # For now, let's skip high-level history for raw input to avoid spamming 'j', 'k', etc.
    
    session.write(req.command)
    # Give a tiny delay for reaction, then return any immediate output
    return {"output": session.read_output(timeout=0.05)}

@app.get("/sessions/{session_id}/output")
def get_output(session_id: str, timeout: float = 0.0):
    """
    Get accumulated output from the session.
    Optional timeout to wait for new output.
    """
    session = sess_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    output = session.read_output(timeout=timeout)
    return {"output": output}

@app.get("/sessions/{session_id}/history", response_model=List[HistoryItem])
def get_history(session_id: str):
    """Get command history for the session."""
    history = sess_manager.get_history(session_id)
    if history is None: # None means session not found/no history tracking
         raise HTTPException(status_code=404, detail="Session history not found")
    return history

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup all sessions on server shutdown."""
    sess_manager.cleanup_all()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

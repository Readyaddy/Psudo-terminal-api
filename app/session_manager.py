import uuid
import time
import threading
from typing import Dict, Optional, List
from .terminal_api import TerminalAPI


class SessionManager:
    """
    Manages multiple persistent terminal sessions.
    Sessions stay alive even when not actively being read.
    """
    
    def __init__(self):
        self._sessions: Dict[str, TerminalAPI] = {}
        # History format: {session_id: [{"command": str, "timestamp": float}]}
        self._history: Dict[str, List[dict]] = {}
        # Metadata format: {session_id: {"name": str, "created_at": float}}
        self._metadata: Dict[str, dict] = {}
        self._lock = threading.Lock()
        
    def create_session(self, name: str = None, cols=120, rows=30, shell_command: str = None) -> str:
        """
        Create a new terminal session.
        
        Args:
            name: Human-readable name for the session. If None, uses "Session-{id}"
            cols: Terminal width
            rows: Terminal height
            shell_command: Optional custom command to launch (e.g. specific distro)
            
        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        
        if not name:
            name = f"Session-{session_id[:8]}"
            
        # Ensure logs directory exists
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Create log filename: logs/{name}_{short_id}.log
        # Sanitize name for filename safety
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        log_path = f"logs/{safe_name}_{session_id[:8]}.log"
        
        # Use default (kali) if not specified
        if shell_command:
            terminal = TerminalAPI(cols=cols, rows=rows, shell_command=shell_command, log_path=log_path)
        else:
            terminal = TerminalAPI(cols=cols, rows=rows, log_path=log_path)
            
        terminal.start()
        
        # Initial cleanup sequence
        self._perform_startup_cleanup(terminal)
        
        with self._lock:
            self._sessions[session_id] = terminal
            self._history[session_id] = []
            self._metadata[session_id] = {
                "name": name,
                "created_at": time.time()
            }
            
        print(f"Session created: {session_id} ({name})")
        return session_id
    
    def _resolve_id(self, identifier: str) -> Optional[str]:
        """Resolve an identifier (ID or Name) to a Session ID."""
        # Assumes lock is held by caller or not needed (internal helper)
        # But this method reads shared state, so it should be called under lock or be careful.
        # Actually safer to just iterate since it's fast enough.
        if identifier in self._sessions:
            return identifier
        for sid, meta in self._metadata.items():
            if meta.get("name") == identifier:
                return sid
        return None

    def record_command(self, identifier: str, command: str):
        """Record a command in the session history."""
        with self._lock:
            sid = self._resolve_id(identifier)
            if sid and sid in self._history:
                self._history[sid].append({
                    "command": command,
                    "timestamp": time.time()
                })

    def get_history(self, identifier: str) -> List[dict]:
        """Get command history for a session."""
        with self._lock:
            sid = self._resolve_id(identifier)
            if sid:
                return self._history.get(sid, [])
            return []

    def _perform_startup_cleanup(self, terminal: TerminalAPI):
        """Perform startup cleanup to remove junk and shell echo."""
        # Wait for shell init
        time.sleep(1.0)
        
        # Discard initial junk
        _ = terminal.read_output()
        
        # Send Ctrl+C to clear prompt
        terminal.write('\x03')
        time.sleep(0.1)
        
        # Discard echo
        _ = terminal.read_output()
        
    def get_session(self, identifier: str) -> Optional[TerminalAPI]:
        """
        Get a session by ID or Name.
        
        Args:
            identifier: Session ID or Session Name
        """
        with self._lock:
            # 1. Try direct ID lookup
            if identifier in self._sessions:
                return self._sessions[identifier]
            
            # 2. Try Name lookup
            for sid, meta in self._metadata.items():
                if meta.get("name") == identifier:
                    return self._sessions[sid]
                    
            return None
            
    def list_sessions(self) -> List[dict]:
        """List all active sessions."""
        with self._lock:
            sessions_list = []
            for sid, t in self._sessions.items():
                meta = self._metadata.get(sid, {})
                sessions_list.append({
                    "id": sid,
                    "name": meta.get("name", "Unknown"),
                    "alive": t.is_alive(),
                    "created_at": meta.get("created_at", 0),
                    "log_path": t.log_path
                })
            return sessions_list
            
    def kill_session(self, identifier: str) -> bool:
        """Kill and remove a session by ID or Name."""
        with self._lock:
            session_id = self._resolve_id(identifier)
            if session_id and session_id in self._sessions:
                terminal = self._sessions[session_id]
                terminal.close()
                del self._sessions[session_id]
                if session_id in self._history:
                    del self._history[session_id]
                if session_id in self._metadata:
                    del self._metadata[session_id]
                return True
        return False
        
    def cleanup_all(self):
        """Kill all sessions (e.g., on server shutdown)."""
        with self._lock:
            for terminal in self._sessions.values():
                terminal.close()
            self._sessions.clear()
            self._history.clear()
            self._metadata.clear()

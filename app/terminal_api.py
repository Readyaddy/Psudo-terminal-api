import sys
import os
import threading
import ctypes
import time
import re
from winpty import PTY
from collections import deque


class TerminalAPI:
    """API wrapper for PTY terminal interaction with output filtering."""
    
    # Use cmd.exe /c to ensure PATH resolution works for WSL
    def __init__(self, cols=120, rows=30, shell_command="cmd.exe /c wsl -d kali-linux", log_path=None):
        """
        Initialize the Terminal API.
        
        Args:
            cols: Terminal width in columns
            rows: Terminal height in rows
            shell_command: Command to spawn (default: cmd.exe /c wsl -d kali-linux)
            log_path: Optional path to log file
        """
        self.cols = cols
        self.rows = rows
        self.shell_command = shell_command
        self.log_path = log_path
        self.process = None
        self._output_buffer = deque(maxlen=10000)
        self._running = False
        self._output_thread = None
        self._enable_vt_mode()
        
    def _enable_vt_mode(self):
        """Enable Windows VT100 mode for ANSI escape sequence support."""
        kernel32 = ctypes.windll.kernel32
        hOut = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(hOut, ctypes.byref(mode))
        kernel32.SetConsoleMode(hOut, mode.value | 0x0004 | 0x0008)
    
    def _filter_output(self, data):
        """
        Filter junk characters and unwanted escape sequences from output.
        
        Args:
            data: Raw output string from terminal
            
        Returns:
            Filtered string
        """
        if not data:
            return data
            
        filtered = data
        
        # === Specific Partial Junk Removal ===
        # The DA response often gets split, leaving this tail:
        filtered = filtered.replace('23;24;28;32;42c', '')
        
        # === Device Attributes (DA) Response ===
        # User sees: ^[[?61;6;7;21;22;23;24;28;32;42c
        # Format: ESC [ ? <numbers> c
        filtered = re.sub(r'\x1b\[\?[\d;]+c', '', filtered)
        
        # === Other Terminal Query Responses ===
        # Cursor position report: ESC [ <row> ; <col> R
        filtered = re.sub(r'\x1b\[\d+;\d+R', '', filtered)
        
        # === Terminal Mode Settings (often sent on init) ===
        # Bracketed paste mode
        filtered = re.sub(r'\x1b\[\?2004[hl]', '', filtered)
        
        # Alternate screen buffer
        filtered = re.sub(r'\x1b\[\?1049[hl]', '', filtered)
        
        # Application cursor keys
        filtered = re.sub(r'\x1b\[\?1[hl]', '', filtered)
        
        # Show/hide cursor
        filtered = re.sub(r'\x1b\[\?25[hl]', '', filtered)
        
        # Mouse tracking modes
        filtered = re.sub(r'\x1b\[\?1000[hl]', '', filtered)
        filtered = re.sub(r'\x1b\[\?1002[hl]', '', filtered)
        filtered = re.sub(r'\x1b\[\?1003[hl]', '', filtered)
        filtered = re.sub(r'\x1b\[\?1006[hl]', '', filtered)
        
        # === Cursor Save/Restore ===
        filtered = re.sub(r'\x1b\[s', '', filtered)
        filtered = re.sub(r'\x1b\[u', '', filtered)
        filtered = re.sub(r'\x1b7', '', filtered)  # DECSC
        filtered = re.sub(r'\x1b8', '', filtered)  # DECRC
        
        # === OSC Sequences (Operating System Commands) ===
        # Window title, etc. - Format: ESC ] ... BEL or ESC ] ... ESC \
        filtered = re.sub(r'\x1b\][^\x07]*\x07', '', filtered)
        filtered = re.sub(r'\x1b\][^\x1b]*\x1b\\\\', '', filtered)
        
        # === Specific Control Characters ===
        # Remove problematic control chars (if they appear standalone)
        filtered = filtered.replace('\x17', '')  # ETB
        filtered = filtered.replace('\x18', '')  # CAN
        filtered = filtered.replace('\x1c', '')  # FS
        
        return filtered

    
    def _read_output_loop(self):
        """Background thread to continuously read terminal output."""
        while self._running:
            try:
                data = self.process.read(blocking=False)
                if data:
                    # Filter the output before buffering
                    filtered_data = self._filter_output(data)
                    if filtered_data:
                        self._output_buffer.append(filtered_data)
                        
                        # Write to log file if configured
                        if self.log_path:
                            try:
                                with open(self.log_path, 'a', encoding='utf-8') as f:
                                    f.write(filtered_data)
                                    f.flush()
                                    os.fsync(f.fileno())
                            except Exception as log_err:
                                print(f"Failed to write log: {log_err}")
                                
                time.sleep(0.01)
            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    print(f"Output read error: {e}")
                break
    
    def start(self):
        """Start the terminal session."""
        if self._running:
            raise RuntimeError("Terminal session already running")
        
        # Create PTY and spawn shell
        print(f"DEBUG: Spawning process: '{self.shell_command}'")
        self.process = PTY(self.cols, self.rows)
        self.process.spawn(self.shell_command)
        
        # Start output reading thread
        self._running = True
        self._output_thread = threading.Thread(target=self._read_output_loop, daemon=True)
        self._output_thread.start()
        
        # Give the shell a moment to initialize
        time.sleep(0.5)
        
    def write(self, text):
        """
        Write raw text to the terminal.
        
        Args:
            text: String to write to terminal
        """
        if not self._running:
            raise RuntimeError("Terminal session not started")
        self.process.write(text)
    
    def send_command(self, command, wait_time=0.5):
        """
        Send a command to the terminal and wait for output.
        
        Args:
            command: Command string to execute
            wait_time: Time to wait for command completion (seconds)
            
        Returns:
            Output from the command
        """
        if not self._running:
            raise RuntimeError("Terminal session not started")
        
        # Clear buffer before sending command
        self._output_buffer.clear()
        
        # Send command with newline
        self.process.write(command + '\r')
        
        # Wait for command to execute
        time.sleep(wait_time)
        
        # Collect output
        return self.read_output()
    
    def read_output(self, timeout=0):
        """
        Read available output from the terminal buffer.
        
        Args:
            timeout: Maximum time to wait for output (seconds). 0 = return immediately
            
        Returns:
            Accumulated output as string
        """
        if timeout > 0:
            time.sleep(timeout)
        
        output = ''.join(self._output_buffer)
        self._output_buffer.clear()
        return output
    
    def get_latest_output(self, lines=10):
        """
        Get the last N lines of output without clearing buffer.
        
        Args:
            lines: Number of recent output chunks to retrieve
            
        Returns:
            Recent output as string
        """
        recent = list(self._output_buffer)[-lines:]
        return ''.join(recent)
    
    def is_alive(self):
        """Check if the terminal session is still active."""
        return self._running and self._output_thread and self._output_thread.is_alive()
    
    def close(self):
        """Close the terminal session and cleanup resources."""
        if self._running:
            self._running = False
            
            # Give the thread time to exit gracefully
            if self._output_thread:
                self._output_thread.join(timeout=1.0)
            
            # The PTY will be cleaned up when the object is destroyed
            self.process = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

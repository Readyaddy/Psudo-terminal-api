"""
Example usage of the Session Manager.
Demonstrates creating multiple sessions and switching between them.
"""
import time
from session_manager import SessionManager


def main():
    manager = SessionManager()
    
    try:
        print("=== creating Session 1 ===")
        sid1 = manager.create_session()
        s1 = manager.get_session(sid1)
        
        print("=== creating Session 2 ===")
        sid2 = manager.create_session()
        s2 = manager.get_session(sid2)
        
        # Verify both are alive
        print(f"\nActive Sessions: {manager.list_sessions()}")
        
        # Interact with Session 1
        print("\n--- Session 1: Running 'pwd' ---")
        out1 = s1.send_command("pwd")
        print(f"S1 Output: {out1.strip()}")
        
        # Interact with Session 2
        print("\n--- Session 2: Running 'whoami' ---")
        out2 = s2.send_command("whoami")
        print(f"S2 Output: {out2.strip()}")
        
        # Go back to Session 1 (Persistence Check)
        print("\n--- Session 1: Running 'echo Still Alive' ---")
        out1_again = s1.send_command("echo Still Alive")
        print(f"S1 Output: {out1_again.strip()}")
        
    finally:
        print("\nCleaning up...")
        manager.cleanup_all()

if __name__ == "__main__":
    main()

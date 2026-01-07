"""
Example usage of the TerminalAPI for programmatic terminal interaction.
"""

from terminal_api import TerminalAPI
import time


def example_basic_usage():
    """Basic example: start terminal, run commands, get output."""
    print("=== Basic Usage Example ===\n")
    
    # Create and start terminal session
    terminal = TerminalAPI()
    terminal.start()
    
    print("Terminal started. Waiting for initialization...")
    time.sleep(1)
    
    # Send a simple command
    print("\n1. Running 'pwd' command:")
    output = terminal.send_command("pwd", wait_time=0.5)
    print(f"Output: {output}")
    
    # Send another command
    print("\n2. Running 'ls -la' command:")
    output = terminal.send_command("ls -la", wait_time=1.0)
    print(f"Output: {output}")
    
    # Send echo command
    print("\n3. Running 'echo Hello from API!' command:")
    output = terminal.send_command("echo Hello from API!", wait_time=0.5)
    print(f"Output: {output}")
    
    # Close the session
    terminal.close()
    print("\nTerminal session closed.")


def example_context_manager():
    """Example using context manager for automatic cleanup."""
    print("\n\n=== Context Manager Example ===\n")
    
    with TerminalAPI() as terminal:
        print("Terminal started via context manager")
        
        # Run a command
        output = terminal.send_command("whoami", wait_time=0.5)
        print(f"Current user: {output}")
        
        # Check if alive
        print(f"Session alive: {terminal.is_alive()}")
    
    print("Terminal automatically closed by context manager")


def example_interactive_monitoring():
    """Example: monitor output continuously."""
    print("\n\n=== Interactive Monitoring Example ===\n")
    
    terminal = TerminalAPI()
    terminal.start()
    
    print("Starting a long-running command...")
    terminal.write("echo 'Starting...'\r")
    time.sleep(0.3)
    
    terminal.write("sleep 1\r")
    time.sleep(0.3)
    
    terminal.write("echo 'Done!'\r")
    time.sleep(0.5)
    
    # Get all accumulated output
    output = terminal.read_output()
    print(f"Accumulated output:\n{output}")
    
    terminal.close()


def example_raw_interaction():
    """Example: raw write/read for custom protocols."""
    print("\n\n=== Raw Interaction Example ===\n")
    
    terminal = TerminalAPI()
    terminal.start()
    time.sleep(0.5)
    
    # Write raw text (no automatic newline)
    terminal.write("echo 'Raw write test'")
    time.sleep(0.2)
    terminal.write("\r")  # Send enter manually
    time.sleep(0.5)
    
    output = terminal.read_output()
    print(f"Output: {output}")
    
    terminal.close()


if __name__ == "__main__":
    # Run all examples
    try:
        example_basic_usage()
        example_context_manager()
        example_interactive_monitoring()
        example_raw_interaction()
        
        print("\n\n=== All examples completed successfully! ===")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

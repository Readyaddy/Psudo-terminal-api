import sys
import os
import importlib.util

output_file = "diag_output.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"Python Executable: {sys.executable}\n")
    f.write(f"CWD: {os.getcwd()}\n")
    f.write("\nSys Path:\n")
    for p in sys.path:
        f.write(f"  - {p}\n")
        
    f.write("\nAttempting import pywinpty...\n")
    try:
        import pywinpty
        f.write(f"SUCCESS: Imported pywinpty from {pywinpty.__file__}\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")
        f.write(f"Type: {type(e)}\n")
        
    f.write("\nChecking spec:\n")
    try:
        spec = importlib.util.find_spec("pywinpty")
        f.write(f"Spec: {spec}\n")
    except Exception as e:
        f.write(f"Spec Error: {e}\n")

print(f"Diagnostics written to {output_file}")

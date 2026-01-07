try:
    import pywinpty
    print("SUCCESS: import pywinpty")
    print(f"File: {pywinpty.__file__}")
except ImportError as e:
    print(f"FAIL: import pywinpty ({e})")

try:
    import winpty
    print("SUCCESS: import winpty")
    print(f"File: {winpty.__file__}")
except ImportError as e:
    print(f"FAIL: import winpty ({e})")

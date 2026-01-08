import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_logs():
    print("--- Testing Log Endpoint ---")
    
    # 1. Create Session
    print("1. Creating session...")
    try:
        resp = requests.post(f"{BASE_URL}/sessions", json={"name": "log-test", "cols": 80, "rows": 24})
        resp.raise_for_status()
        sess = resp.json()
        sid = sess['id']
        print(f"   Session ID: {sid}")
    except Exception as e:
        print(f"   FAILED: Any server running? {e}")
        return

    # 2. Generate some distinct output
    unique_str = f"LogCheck_{int(time.time())}"
    print(f"2. Sending unique string: {unique_str}")
    requests.post(f"{BASE_URL}/sessions/{sid}/command", json={"command": f"echo {unique_str}"})
    
    time.sleep(3) # Wait longer for I/O
    
    # 3. Fetch Logs
    print("3. Fetching logs...")
    try:
        log_resp = requests.get(f"{BASE_URL}/sessions/{sid}/logs")
        log_resp.raise_for_status()
        logs = log_resp.text
        print(f"   Logs retrieved ({len(logs)} chars).")
        print(f"   DEBUG CONTENT: {repr(logs)}")
    except Exception as e:
        print(f"   FAILED to get logs: {e}")
        return

    # 4. Verify content
    if unique_str in logs:
        print("   SUCCESS: Unique string found in logs!")
    else:
        print("   FAILURE: Unique string NOT found in logs.")

    # Cleanup
    requests.delete(f"{BASE_URL}/sessions/{sid}")

if __name__ == "__main__":
    test_logs()

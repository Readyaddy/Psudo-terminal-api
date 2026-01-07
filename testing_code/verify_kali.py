import time
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

def post(endpoint, data):
    try:
        req = urllib.request.Request(
            f"{BASE_URL}{endpoint}",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)

def get(endpoint):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)

def main():
    print("--- Verifying Kali Linux Support ---")
    
    # 1. Create Session (Should default to Kali)
    print("1. Creating session 'kali-check'...")
    sess = post("/sessions", {"name": "kali-check", "cols": 80, "rows": 24})
    sid = sess['id']
    print(f"   Session ID: {sid}")

    time.sleep(1)

    # 2. Check OS Release
    print("2. Checking /etc/os-release...")
    # Clean buffer first
    get(f"/sessions/{sid}/output")
    
    # Run command via /input to manually control timing (command endpoint 0.5s might be too fast)
    post(f"/sessions/{sid}/input", {"command": "grep PRETTY_NAME /etc/os-release\r"})
    
    time.sleep(1) # Wait longer for grep to finish
    
    res = get(f"/sessions/{sid}/output")
    output = res['output']
    
    print(f"   Output: {repr(output)}")
    
    if "Kali" in output or "kali" in output.lower():
        print("\n✅ SUCCESS: Session is running Kali Linux!")
    else:
        print("\n❌ FAILURE: 'Kali' not found in OS release info.")
        print(f"Full output was: {output}")

    # Cleanup
    # post(f"/sessions/{sid}/command", {"command": "exit"})

if __name__ == "__main__":
    main()

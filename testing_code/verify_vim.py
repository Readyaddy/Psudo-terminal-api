import time
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def post(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("--- Verifying Vim Support ---")
    
    # 1. Create Session
    print("1. Creating session 'vim-test'...")
    try:
        sess = post("/sessions", {"name": "vim-test", "cols": 80, "rows": 24})
        sid = sess['id']
        print(f"   Session ID: {sid}")
    except urllib.error.URLError:
        print("   FAILED: Server not reachable. Is it running?")
        return

    time.sleep(1)

    # 2. Open Vim
    print("2. Opening vim...")
    post(f"/sessions/{sid}/command", {"command": "vim test_vim.txt"})
    time.sleep(1) # Wait for vim to load

    # 3. Send Input (Insert Mode + Text)
    print("3. Typing text via /input...")
    # 'i' for insert mode
    post(f"/sessions/{sid}/input", {"command": "i"}) 
    time.sleep(0.1)
    
    # Type content
    post(f"/sessions/{sid}/input", {"command": "Hello from the API via Vim!"})
    time.sleep(0.1)
    
    # 4. Save and Quit
    print("4. Saving and exiting...")
    # Esc to exit insert mode
    post(f"/sessions/{sid}/input", {"command": "\x1b"})
    time.sleep(0.1)
    
    # :wq + Enter
    post(f"/sessions/{sid}/input", {"command": ":wq\r"})
    
    # Wait for vim to exit and shell to return
    time.sleep(1)

    # 5. Verify File Content
    print("5. Verifying file content...")
    # clean buffer
    get(f"/sessions/{sid}/output")
    
    # Cat the file
    res = post(f"/sessions/{sid}/command", {"command": "cat test_vim.txt"})
    output = res['output']
    
    print(f"   Output: {repr(output)}")
    
    if "Hello from the API via Vim!" in output:
        print("\nSUCCESS: Vim edited the file correctly!")
    else:
        print("\nFAILURE: Content not found.")

    # Cleanup
    # post(f"/sessions/{sid}/command", {"command": "rm test_vim.txt"})

if __name__ == "__main__":
    main()

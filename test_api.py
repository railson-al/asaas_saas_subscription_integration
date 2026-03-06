import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000"

def get_token():
    url = f"{base_url}/auth/token/"
    data = urllib.parse.urlencode({"username": "admin", "password": "adminpass"}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("access")
    except urllib.error.URLError as e:
        print(f"Error getting token: {e}")
        return None

def test_me(token):
    url = f"{base_url}/me/"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("Successfully hit /me endpoint:")
            print(json.dumps(result, indent=2))
    except urllib.error.URLError as e:
        print(f"Error hitting /me endpoint: {e}")

if __name__ == "__main__":
    import threading
    import time
    import os
    import subprocess
    import sys
    
    print("Starting Django server in background...")
    server_proc = subprocess.Popen([sys.executable, "manage.py", "runserver", "8000"], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # Wait for server to start
    
    try:
        print("Authenticating...")
        token = get_token()
        if token:
            print("Got token. Testing /me endpoint...")
            test_me(token)
        else:
            print("Failed to get token.")
    finally:
        print("Terminating server...")
        server_proc.terminate()

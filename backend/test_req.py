import urllib.request
import json

url = 'http://localhost:8000/api/v1/auth/register'
data = json.dumps({
    "email": "test2@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
}).encode('utf-8')
headers = {'Content-Type': 'application/json'}

req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode())
except Exception as e:
    print("Exception:", e)

import json
import urllib.request
url = 'http://localhost:5000/api/auth/login'
data = json.dumps({'username':'admin','password':'admin123'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        print('Status:', resp.status)
        print('Response:', resp.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)

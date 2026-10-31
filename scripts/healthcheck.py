import os
import urllib.request
from urllib.parse import urlsplit
origin=os.environ.get('APP_ORIGIN','http://localhost:5000')
request=urllib.request.Request('http://127.0.0.1:5000/api/health',headers={'Host':urlsplit(origin).netloc})
with urllib.request.urlopen(request,timeout=5) as response:
    if response.status!=200:raise SystemExit(1)

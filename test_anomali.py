import urllib.request
import json
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://dds-api.bpssulteng.id/api.php?action=get_anomali'
req = urllib.request.Request(url, headers={'Host': 'dds-api.bpssulteng.id'})
with urllib.request.urlopen(req, context=ctx) as r:
    data = json.loads(r.read().decode())
    print(json.dumps(data[0], indent=2))

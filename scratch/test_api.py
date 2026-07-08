import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=se_umum&kab="
req = urllib.request.Request(url)
with urllib.request.urlopen(req, context=ctx) as response:
    data = json.loads(response.read().decode('utf-8'))
    print(json.dumps(data[:2], indent=2))

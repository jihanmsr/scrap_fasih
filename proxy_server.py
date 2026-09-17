"""
proxy_server.py
Local lightweight CORS & SSL bypass proxy for geotagging API.
Listens on http://127.0.0.1:5050/api/sls
Allows any SLS (all 8,980 SLS) to be fetched live without CORS or SSL errors in the browser.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import urllib3

urllib3.disable_warnings()

API_URL = "https://103.5.51.154/api/sqllab_geotagging/sls"
HEADERS = {
    "Content-Type": "application/json",
    "Host": "ause.bpssulteng.id",
    "User-Agent": "BPS-Proxy/1.0"
}

class ProxyHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/sls':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                # Call Kak Ical's server directly
                resp = requests.post(API_URL, json=payload, headers=HEADERS, verify=False, timeout=20)
                
                self.send_response(resp.status_code)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(resp.content)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        # Quiet logger
        pass

def run():
    server_address = ('127.0.0.1', 5050)
    httpd = HTTPServer(server_address, ProxyHandler)
    print("Local Geotagging Proxy running on http://127.0.0.1:5050/api/sls")
    httpd.serve_forever()

if __name__ == '__main__':
    run()

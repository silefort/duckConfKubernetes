#!/usr/bin/env python3
import socket
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

received_packets = []

# --- UDP server ---

def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 5000))
    print("UDP listening on :5000")
    while True:
        data, addr = sock.recvfrom(4096)
        msg = data.decode(errors="replace")
        print(f"UDP recv from {addr}: {msg}")
        received_packets.append({"from": str(addr), "msg": msg})

# --- HTTP server ---

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"HTTP {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._json({"status": "ok"})

        elif parsed.path == "/packets":
            self._json(received_packets)

        elif parsed.path == "/send-udp":
            qs = parse_qs(parsed.query)
            host = qs.get("host", [""])[0]
            port = int(qs.get("port", [5000])[0])
            msg  = qs.get("msg",  ["ping"])[0]
            if not host:
                self._json({"error": "missing host"}, 400)
                return
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(msg.encode(), (host, port))
            sock.close()
            print(f"UDP sent to {host}:{port} → {msg}")
            self._json({"sent": msg, "to": f"{host}:{port}"})

        elif parsed.path == "/send-http":
            qs = parse_qs(parsed.query)
            host = qs.get("host", [""])[0]
            port = int(qs.get("port", [80])[0])
            path = qs.get("path", ["/"])[0]
            if not host:
                self._json({"error": "missing host"}, 400)
                return
            import http.client
            try:
                conn = http.client.HTTPConnection(host, port, timeout=5)
                conn.request("GET", path)
                resp = conn.getresponse()
                body = resp.read().decode(errors="replace")
                conn.close()
                print(f"HTTP GET {host}:{port}{path} → {resp.status}")
                self._json({"status": resp.status, "body": body})
            except Exception as e:
                self._json({"error": str(e)}, 502)

        else:
            self._json({"error": "not found"}, 404)

    def _json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    threading.Thread(target=udp_server, daemon=True).start()
    print("HTTP listening on :8080")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

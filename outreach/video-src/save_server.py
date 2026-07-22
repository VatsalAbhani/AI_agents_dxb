import http.server, os
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith("/save/"):
            name = os.path.basename(self.path[6:]) or "out.bin"
            n = int(self.headers.get("content-length", 0))
            with open(os.path.join(BASE, name), "wb") as f:
                remaining = n
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk: break
                    f.write(chunk); remaining -= len(chunk)
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(404); self.end_headers()
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(("127.0.0.1", 8777), H).serve_forever()

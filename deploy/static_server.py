"""Serves both marketing sites: Attesta at /, Guard at /guard/. Stdlib only."""
import http.server
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCROOT = "/tmp/docroot"

shutil.rmtree(DOCROOT, ignore_errors=True)
shutil.copytree(os.path.join(ROOT, "website-attesta"), DOCROOT)
shutil.copytree(os.path.join(ROOT, "website"), os.path.join(DOCROOT, "guard"))
os.chdir(DOCROOT)


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=300")
        super().end_headers()


port = int(os.getenv("PORT", "8080"))
http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()

#!/usr/bin/env python
"""
Resume viewer server — static files + writable /save endpoint.

Usage:
    python server.py          # serves on port 8080
    python server.py 8888     # custom port

Endpoints:
    GET  /*                   → serve static files (same as python -m http.server)
    POST /save?file=name.json → write JSON to tailored_resumes/name.json
    POST /save?file=base.json → write JSON to resume_data/base.json
"""
import http.server
import json
import os
import sys
import urllib.parse
from pathlib import Path


class ResumeHandler(http.server.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/save':
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        filename = params.get('file', [None])[0]

        # Basic path-traversal guard
        if not filename or '/' in filename or '\\' in filename or '..' in filename:
            self.send_response(400)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        # Validate JSON
        try:
            json.loads(body)
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return

        # Write to the right directory
        if filename == 'base.json':
            target = Path('resume_data') / filename
        else:
            target = Path('tailored_resumes') / filename

        if not target.parent.exists():
            self.send_response(400)
            self.end_headers()
            return

        target.write_bytes(body)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def end_headers(self):
        # Add CORS headers to every response
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, fmt, *args):
        # Only log POSTs and errors, not every GET
        if args and (str(args[1]) != '200' or self.command == 'POST'):
            super().log_message(fmt, *args)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    server = http.server.HTTPServer(('', port), ResumeHandler)
    print(f'Resume server running at http://localhost:{port}/resume_viewer.html')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

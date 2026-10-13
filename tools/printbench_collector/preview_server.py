from __future__ import annotations
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import export_preview

ROOT = Path(__file__).resolve().parent
PREVIEW = ROOT / 'preview'

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?',1)[0].endswith('/data.json') or self.path.split('?',1)[0] == '/data.json':
            try:
                export_preview.main()
            except Exception as e:
                print(f'[PRINTBENCH PREVIEW] export failed: {e}', flush=True)
        return super().do_GET()
    def log_message(self, fmt, *args):
        pass

def main():
    os.chdir(PREVIEW)
    export_preview.main()
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('[PRINTBENCH PREVIEW] http://127.0.0.1:8765/', flush=True)
    server.serve_forever()

if __name__ == '__main__':
    main()

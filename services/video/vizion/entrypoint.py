"""Railway web and worker services share an image and run independent processes."""

import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def main():
    if os.getenv("APP_ROLE", "web") == "worker":
        from vizion.worker import main as worker_main

        class WorkerHealth(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200 if self.path == "/api/health" else 404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "role": "worker"}).encode())

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), WorkerHealth)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        worker_main()
    else:
        import uvicorn

        logging.basicConfig(level=logging.INFO)
        uvicorn.run("vizion.api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), proxy_headers=True)


if __name__ == "__main__":
    main()

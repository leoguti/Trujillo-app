import json
import logging
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from generate import build_feed, build_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("simulator")

PATTERNS_PATH = os.environ.get("PATTERNS_PATH", "/app/patterns.json")
CLONE_FACTOR = int(os.environ.get("CLONE_FACTOR", "3"))
MAX_VEHICLES = int(os.environ.get("MAX_VEHICLES", "0"))  # 0 = no cap
PORT = int(os.environ.get("PORT", "9000"))

_patterns = json.loads(Path(PATTERNS_PATH).read_text())
_server_start = datetime.now(timezone.utc)
_pool = build_pool(_patterns, CLONE_FACTOR, _server_start)

if MAX_VEHICLES > 0 and len(_pool) > MAX_VEHICLES:
    _pool = _pool[:MAX_VEHICLES]

log.info(
    "Loaded %d trajectories from %s; pool=%d (clone_factor=%d, max_vehicles=%s)",
    len(_patterns["trajectories"]),
    PATTERNS_PATH,
    len(_pool),
    CLONE_FACTOR,
    MAX_VEHICLES or "unlimited",
)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/pe-trujillo.proto") or self.path.startswith(
            "/gtfsrt.proto"
        ):
            body = build_feed(_pool, datetime.now(timezone.utc))
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Cache-Control", "no-cache, no-store, max-age=0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith("/healthz"):
            payload = {
                "status": "ok",
                "patterns_source": _patterns.get("source", {}),
                "pool_size": len(_pool),
                "trajectories": len(_patterns["trajectories"]),
                "server_start_utc": _server_start.isoformat().replace("+00:00", "Z"),
                "clone_factor": CLONE_FACTOR,
                "max_vehicles": MAX_VEHICLES or None,
            }
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):  # keep the logs tidy
        log.info("%s - %s", self.address_string(), format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log.info("Serving on 0.0.0.0:%d", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")

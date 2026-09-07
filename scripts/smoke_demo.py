"""Exercise the synthetic demo through its real reverse proxy."""

import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    try:
        with urlopen(Request(base + path, data=data, headers={"Content-Type": "application/json"}), timeout=20) as response:
            return response.status, response.headers, response.read()
    except HTTPError as response:
        return response.code, response.headers, response.read()


status, headers, _ = request("/")
assert status == 200
assert headers["X-Content-Type-Options"] == "nosniff"
assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
assert request("/health/ready")[0] == 200
status, _, body = request("/api/v1/config")
assert status == 200 and json.loads(body)["local_ingestion_enabled"] is False
assert request("/api/v1/runs/example")[0] == 404
assert request("/api/v1/bankops/ingest", {})[0] == 404
status, _, body = request("/api/v1/chat", {"domain": "bankops", "question": "How many cases are overdue?"})
assert status == 200, body
assert request("/api/v1/awardlens/demo-audit")[0] == 200
assert request("/api/v1/chat", {"question": "x" * 2_100_000})[0] == 413
assert 429 in [request("/api/v1/config")[0] for _ in range(25)]
print("Demo smoke passed: readiness, safe profile, chat, audit, security headers, body and rate limits")

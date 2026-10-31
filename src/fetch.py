"""One-at-a-time fetch from www.gsi.go.jp / www1.gsi.go.jp (only these two hosts), 2 s apart.

These hosts need TLS legacy renegotiation; it is enabled per connection through the SSL context
(OP_LEGACY_SERVER_CONNECT) and nowhere else. A 403 or 429 stops the run.
"""

import ssl
import time
import urllib.parse
import urllib.request

ALLOWED = {"www.gsi.go.jp", "www1.gsi.go.jp"}
DELAY = 2.0
UA = "yuiseki-hf-data-pipeline (research; github.com/yuiseki)"
_ctx = ssl.create_default_context()
_ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
_last = 0.0


def get(url: str) -> tuple[bytes, dict]:
    global _last
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOWED:
        raise ValueError(f"host not allowed: {host}")
    wait = DELAY - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=120) as r:
            body, hdr = r.read(), dict(r.headers)
    finally:
        _last = time.monotonic()
    return body, hdr

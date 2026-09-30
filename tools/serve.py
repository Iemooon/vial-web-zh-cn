"""Serve a vial-web build directory the way the app needs to be served.

Qt/Python here are compiled with -pthread, so the page must be cross-origin
isolated to get SharedArrayBuffer; a plain `python -m http.server` therefore
fails with "SharedArrayBuffer is not available".  http://localhost is a secure
context, so these two headers are all that is missing.

    python tools/serve.py [dir] [port]        # default: src/build  port 8000
    pythonw tools/serve.py <dir> <port>       # no console; log goes to <dir>/serve.log
"""
import http.server
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "src/build"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
# Under pythonw there is no console to write to, so keep the request log in a file.
LOG_PATH = os.path.join(ROOT, "serve.log")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        if path.endswith(".wasm"):
            return "application/wasm"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        line = "%s - %s" % (self.address_string(), fmt % args)
        try:
            if sys.stderr:
                sys.stderr.write(line + "\n")
        except Exception:
            pass
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            pass


def say(text):
    try:
        if sys.stdout:
            sys.stdout.write(text + "\n")
    except Exception:
        pass


if not os.path.isdir(ROOT):
    sys.stderr = sys.stderr or open(os.devnull, "w")
    sys.exit("no such directory: %s" % ROOT)

os.chdir(ROOT)
say("serving %s at http://localhost:%d/  (Ctrl-C to stop)" % (ROOT, PORT))
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

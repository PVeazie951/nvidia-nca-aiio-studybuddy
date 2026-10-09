"""Throwaway OpenAI-compatible mock for exercising the AI path offline."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        prompt = body.get("messages", [{}])[-1].get("content", "")
        reply = (
            "MOCK REPLY\n"
            f"model={body.get('model')}\n"
            f"received_chars={len(prompt)}\n"
            "--- prompt head ---\n"
            + prompt[:400]
        )
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": reply}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 9001), Handler).serve_forever()

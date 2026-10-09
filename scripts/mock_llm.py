"""OpenAI-compatible mock with optional vision, for offline testing."""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

VISION = "--vision" in sys.argv


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        msgs = body.get("messages", [])
        parts = msgs[-1].get("content", "") if msgs else ""
        n_images = 0
        prompt = ""
        if isinstance(parts, list):
            for p in parts:
                if p.get("type") == "text":
                    prompt = p.get("text", "")
                elif p.get("type") == "image_url":
                    n_images += 1
        else:
            prompt = parts

        head = (
            "MOCK REPLY\n"
            f"model={body.get('model')}\n"
            f"images_attached={n_images}\n"
            f"prompt_chars={len(prompt)}\n"
            f"vision_note={'yes' if 'attached directly' in prompt else 'no'}\n"
            "--- prompt head ---\n" + prompt[:300]
        )
        # A real vision model reads the pixels; the mock cannot, so it simply
        # simulates success whenever an image part is present and vision is on.
        reply = "VISION-OK 7319" if (VISION and n_images) else head

        out = json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": reply}}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 9001), Handler).serve_forever()

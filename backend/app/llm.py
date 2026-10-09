"""OpenAI-compatible LLM client, vision support, and default prompt templates."""

from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path

import httpx

DEFAULT_PROMPTS: dict[str, str] = {
    "whiteboard": (
        "You are an AI infrastructure tutor preparing a student for the NVIDIA "
        "NCA-AIIO (AI Infrastructure and Operations) certification.\n\n"
        "Topic: {topic}\n"
        "Student's self-rated confidence: {confidence}/5\n\n"
        "Study material supplied by the student:\n"
        "-----\n{material}\n-----\n\n"
        "Produce a whiteboard-style breakdown:\n"
        "1. A short plain-English framing of the topic (2-3 sentences).\n"
        "2. A structured outline of the key concepts, grouped logically.\n"
        "3. A simple ASCII diagram of how the pieces relate.\n"
        "4. The 3 facts most likely to be tested on the exam.\n"
        "Be concrete. Prefer specifics (bus types, memory types, tool names, "
        "commands) over generalities. If the material is insufficient, say what "
        "is missing rather than inventing details."
    ),
    "hint": (
        "You are an AI infrastructure tutor for the NVIDIA NCA-AIIO exam.\n\n"
        "Topic: {topic}\n"
        "Question the student is working on:\n{question}\n\n"
        "Relevant material:\n-----\n{material}\n-----\n\n"
        "Give a PROGRESSIVE HINT ONLY. Do not reveal the answer. "
        "Start with the smallest nudge that could unblock them: point at the "
        "concept area, or ask one guiding question. End by inviting them to try "
        "again. Keep it under 120 words."
    ),
    "explain": (
        "You are an AI infrastructure tutor for the NVIDIA NCA-AIIO exam.\n\n"
        "Topic: {topic}\n"
        "The student is confused about:\n{question}\n\n"
        "Material:\n-----\n{material}\n-----\n\n"
        "Explain it clearly and build intuition. Use an everyday analogy first, "
        "then the precise technical explanation. Call out the common "
        "misconception if there is one. Under 300 words."
    ),
    "quiz": (
        "You are generating exam-style questions for the NVIDIA NCA-AIIO "
        "certification.\n\n"
        "Topic: {topic}\n"
        "Material:\n-----\n{material}\n-----\n\n"
        "Write {count} multiple-choice questions in the style of the real exam. "
        "Each question has 4 options (A-D), exactly one correct. "
        "Format each as:\n"
        "Q<n>. <question>\nA) ...\nB) ...\nC) ...\nD) ...\n"
        "Answer: <letter>\nWhy: <one sentence>\n\n"
        "Cover different subtopics; do not repeat the same fact twice."
    ),
    "gap": (
        "You are an AI infrastructure tutor reviewing a student's study material "
        "against the NVIDIA NCA-AIIO syllabus topic: {topic}.\n\n"
        "Material the student has collected:\n-----\n{material}\n-----\n\n"
        "Identify what is MISSING or thin for this topic relative to the exam. "
        "Return a short list of gaps, each with a one-line reason why it matters "
        "and what to go find. If coverage looks complete, say so plainly."
    ),
}

PROMPT_KEYS = tuple(DEFAULT_PROMPTS.keys())

VISION_NOTE = (
    "\n\nThe student has also supplied {n} image(s), attached directly. Read them "
    "carefully -- they are likely architecture diagrams, topology screenshots, "
    "NVIDIA dashboard captures, or slides. Use what the images actually show, "
    "including labels, part numbers, port counts and component names. Where the "
    "attached images contradict the extracted text above, trust the images."
)

MAX_IMAGE_BYTES = 3_500_000
MAX_IMAGE_DIM = 1568


def prepare_image(
    path: str, max_dim: int = MAX_IMAGE_DIM, max_bytes: int = MAX_IMAGE_BYTES
) -> tuple[str, str]:
    """Downscale/compress an image for attachment.

    Returns (data_url, note). Never raises; on failure returns ("", reason).
    """
    p = Path(path)
    if not p.is_file():
        return "", f"image missing on disk: {p.name}"

    raw = p.read_bytes()
    mime = mimetypes.guess_type(p.name)[0] or "image/png"

    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        resized = False
        if max(img.width, img.height) > max_dim:
            scale = max_dim / max(img.width, img.height)
            img = img.resize(
                (max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                Image.LANCZOS,
            )
            resized = True

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        data = buf.getvalue()

        if len(data) > max_bytes:
            for q in (70, 55, 40):
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=q, optimize=True)
                data = buf.getvalue()
                if len(data) <= max_bytes:
                    break

        note = f"{p.name}: {img.width}x{img.height} jpeg, {len(data) // 1024}KB" + (
            " (resized)" if resized else ""
        )
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/jpeg;base64,{b64}", note
    except Exception as exc:  # noqa: BLE001
        if len(raw) <= max_bytes:
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{mime};base64,{b64}", f"{p.name}: passthrough {mime}, {len(raw) // 1024}KB"
        return "", f"{p.name}: could not prepare ({exc})"


def build_messages(
    prompt_key: str,
    prompts: dict,
    images: list[str] | None = None,
    **kwargs: object,
) -> list[dict[str, object]]:
    template = (prompts or {}).get(prompt_key) or DEFAULT_PROMPTS[prompt_key]
    text = template.format(**kwargs)

    images = images or []
    if images:
        text += VISION_NOTE.format(n=len(images))
        content: list[dict[str, object]] = [{"type": "text", "text": text}]
        for data_url in images:
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        return [{"role": "user", "content": content}]

    return [{"role": "user", "content": text}]


async def call_llm(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, object]],
    temperature: float = 0.3,
    max_tokens: int = 1500,
    timeout: float = 300.0,
) -> str:
    """Call an OpenAI-compatible /chat/completions endpoint."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"LLM endpoint returned {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected LLM response shape: {str(data)[:500]}") from exc


async def call_llm_vision_probe(
    *, base_url: str, api_key: str, model: str, timeout: float = 60.0
) -> dict:
    """Send a tiny synthetic image and report whether the model can actually read it.

    Catches the common failure where a text-only model silently ignores image
    content parts and answers from the text prompt alone.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (320, 120), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 300, 100], outline="black", width=3)
    draw.text((40, 55), "VISION-OK 7319", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    messages: list[dict[str, object]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What exact text appears inside the rectangle in this image? "
                    "Reply with only the text you see.",
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]
    try:
        out = await call_llm(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=32,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "verdict": "error", "detail": str(exc)[:300]}

    text = out.strip()
    return {
        "ok": True,
        "verdict": "vision" if "7319" in text else "no-vision",
        "reply": text[:200],
    }

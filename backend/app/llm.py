"""OpenAI-compatible LLM client and default prompt templates."""

from __future__ import annotations

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


def build_messages(prompt_key: str, prompts: dict, **kwargs: object) -> list[dict[str, str]]:
    template = (prompts or {}).get(prompt_key) or DEFAULT_PROMPTS[prompt_key]
    filled = template.format(**kwargs)
    return [{"role": "user", "content": filled}]


async def call_llm(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1500,
    timeout: float = 180.0,
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

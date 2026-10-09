# NVIDIA NCA-AIIO Study Buddy

A local study workspace for the **NVIDIA-Certified Associate: AI Infrastructure
and Operations (NCA-AIIO)** exam. Drop in PDFs, slides, screenshots and pasted
text from NVIDIA's courseware; the app extracts the text, lets you file material
against a syllabus topic, and gives you an LLM tutor to whiteboard, hint, explain,
quiz and gap-check against exactly the material you select.

## Stack

- **Frontend:** Vite + React 19 + TypeScript + Tailwind v4
- **Backend:** FastAPI + SQLAlchemy 2 (async) + asyncpg
- **Database:** PostgreSQL 18
- **Extraction:** pypdf (PDF), python-docx (DOCX), openpyxl (XLSX),
  tesseract OCR (screenshots, auto-upscaled 2x)
- **LLM:** any OpenAI-compatible `/chat/completions` endpoint

## Run it

```bash
./start.sh          # backend :8077 + frontend :5273
./stop.sh
```

Then open **http://127.0.0.1:5273**.

API docs live at http://127.0.0.1:8077/docs.

## First run

1. Click **Configure model** (top right).
2. Enter a base URL and model name. Common ones:

   | Backend | Base URL | Model example |
   |---|---|---|
   | Ollama | `http://127.0.0.1:11434/v1` | `qwen2.5:14b` |
   | llama.cpp server | `http://127.0.0.1:8080/v1` | whatever `-m` loaded |
   | vLLM | `http://127.0.0.1:8000/v1` | `Qwen/Qwen2.5-14B-Instruct` |
   | OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
   | LiteLLM proxy | `http://127.0.0.1:4000/v1` | any routed model |

   Leave the API key blank for local servers.
3. Hit **Save & test** to confirm the connection.

## Using it

- **Add material:** drag files onto the drop zone, click to browse, or press
  **Ctrl+V** anywhere to paste a screenshot or copied text.
- **File it:** use the dropdown on each item to assign it to a syllabus topic.
  Click a topic in the left rail to filter.
- **Rate yourself:** click the stars on a topic to track confidence 0–5.
- **Ask the tutor:** check the files you want in scope (or none, to use the
  newest files for the selected topic), pick a mode, and hit **Ask tutor**.

| Mode | What it does |
|---|---|
| **Whiteboard** | Structured breakdown of the topic + ASCII diagram + likely exam facts |
| **Hint** | Progressive nudge toward an answer without revealing it |
| **Explain** | Analogy-first explanation of something you're stuck on |
| **Quiz me** | Exam-style multiple choice from your material |
| **Find gaps** | What's missing vs the syllabus for that topic |

## Prompts

Every mode's prompt is editable in Settings → Prompt templates. Placeholders:

- `whiteboard` — `{topic}` `{confidence}` `{material}`
- `hint` / `explain` — `{topic}` `{question}` `{material}`
- `quiz` — `{topic}` `{material}` `{count}`
- `gap` — `{topic}` `{material}`

"reset to default" restores the shipped template. The **extra instruction**
field on the main panel appends a one-off instruction without changing saved
prompts.

## Notes on OCR

Screenshots are converted to greyscale and upscaled 2× before tesseract runs;
without that, small UI text OCRs poorly. Accuracy is good on normal-size text and
degrades on very small or low-contrast text — for dense diagrams, paste the
source text if you have it.

## Layout

```
backend/app/
  main.py       app entry, seeding
  routes.py     all HTTP endpoints
  models.py     SQLAlchemy tables
  extract.py    per-format text extraction
  llm.py        OpenAI-compatible client + default prompts
  syllabus.py   NCA-AIIO topic seed data
frontend/src/
  App.tsx        layout + state
  TopicRail.tsx  syllabus sidebar with confidence stars
  DropZone.tsx   drag/drop + clipboard paste
  AssetList.tsx  material list with topic assignment
  TutorPanel.tsx tutor modes and markdown output
  Settings.tsx   endpoint + prompt configuration
data/uploads/   stored files (metadata + text live in Postgres)
```

## Data

Postgres database `studybuddy`, role `studybuddy` (password `studybuddy`), local
only. Connection string override: `DATABASE_URL` env var.

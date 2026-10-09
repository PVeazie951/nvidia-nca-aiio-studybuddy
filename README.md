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

When images are attached, a short note is appended telling the model to trust
the pixels over the extracted text where the two disagree.

## Vision

Off by default. In **Settings → Vision**, tick *Send screenshots to the model as
images* and hit **Detect capability**.

Detection matters because a text-only model does not error when handed image
parts — it ignores them and answers from the text alone, which looks like a bad
answer rather than a capability gap. The probe sends a synthetic image with the
string `7319` and checks whether it comes back; the verdict is saved on the
profile. The tutor panel also exposes a per-call `images: auto / always / never`
selector, where `auto` follows the saved setting.

Images are downscaled to a 1568px long edge and recompressed as JPEG before
sending. One unreadable file degrades to a note in the prompt rather than
failing the whole request.

## Notes on OCR

Screenshots are converted to greyscale and upscaled 2× before tesseract runs;
without that, small UI text OCRs poorly. Accuracy is good on normal-size text and
degrades on very small or low-contrast text.

**Better path for dense diagrams:** turn on vision (Settings → Vision) and the
image is sent to the model as actual pixels alongside the OCR text. Hit
**Detect capability** first — it sends a test image and tells you whether your
model can actually see, since text-only models ignore image parts silently. The
tutor panel also has a per-request `images: auto / always / never` selector.

## Layout

```
backend/app/
  main.py       app entry, seeding
  routes.py     all HTTP endpoints
  models.py     SQLAlchemy tables
  extract.py    per-format text extraction
  llm.py        OpenAI-compatible client, vision, default prompts
  migrations.py additive schema upgrades on startup
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

# NVIDIA NCA-AIIO Study Buddy — Project Doc

Local study workspace for the **NVIDIA-Certified Associate: AI Infrastructure
and Operations (NCA-AIIO)** exam. Collect material from NVIDIA's courseware
(drag/drop, screenshot paste), file it against the syllabus, and use an
LLM tutor to whiteboard, hint, explain, quiz, and gap-check against exactly the
material you select.

Status: **working, verified end-to-end.** Not deployed anywhere — local only.

---

## 1. Why it exists

Prepping for NCA-AIIO means accumulating a lot of heterogeneous material:
PDFs from NVIDIA Academy, screenshots of dashboards and topology diagrams,
copied text from docs, slide decks. There's no good audiobook or single source,
so the workflow is: collect scattered artifacts → organise them → active recall.

This tool covers the last two steps and adds a tutor that is *grounded in your
own collected material* rather than generic model knowledge.

---

## 2. Stack and why

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Vite + React 19 + TypeScript + Tailwind v4 | Fast dev server, no build ceremony, HMR while iterating on UI |
| Backend | FastAPI + SQLAlchemy 2 (async) + asyncpg | Async I/O suits file uploads + long LLM calls; auto OpenAPI docs at `/docs` |
| Database | PostgreSQL 18 | Requested. Metadata + extracted text in PG; raw files on disk |
| Extraction | pypdf, python-docx, openpyxl, tesseract | Per-format; OCR for screenshots |
| LLM | Any OpenAI-compatible `/chat/completions` | Provider-agnostic — Ollama, llama.cpp, vLLM, OpenAI, LiteLLM proxy |

**Key decision — text extraction, not blob storage.** Files are written to disk
but their *text* is extracted, stored in Postgres, and injected into prompts.
That's what makes the tutor grounded: it sees the content of what you dropped,
not just a filename.

**Key decision — OCR with 2× upscale.** tesseract on UI-sized screenshot text
produced garbage (`PCle Gens 16` instead of `PCIe Gen5 x16`). Converting to
greyscale and upscaling 2× with LANCZOS before OCR fixed it. This is in
`_ocr_image()` in `backend/app/extract.py` and matters — don't remove it.

**Known limitation — OCR is not vision.** Dense diagrams, low-contrast slides,
and very small text still degrade. The proper fix for a vision-capable model is
to send the image itself rather than OCR output. Not implemented; noted as the
most valuable next step.

---

## 3. Architecture

```
Browser (127.0.0.1:5273)
    │  Vite dev server, /api/* proxied to :8077
    ▼
FastAPI (127.0.0.1:8077)
    ├── /api/assets        upload, paste, list, patch, delete
    ├── /api/topics        syllabus list, confidence/weight updates
    ├── /api/notes         user + LLM notes
    ├── /api/llm/*         profile, defaults, connection test
    └── /api/ai            whiteboard | hint | explain | quiz | gap
    │
    ├── Postgres 18  (studybuddy db)  → assets, topics, notes, llm_profiles
    ├── data/uploads/                → raw files on disk
    └── OpenAI-compatible endpoint   → whatever you configure
```

### Data model

- **assets** — one dropped/pasted item. `kind` is `file | image | text`;
  `extracted_text` holds the parsed content; `extraction_error` holds the reason
  when parsing fails; `topic_id` files it against the syllabus.
- **topics** — the 10 NCA-AIIO topics seeded from `syllabus.py`.
  `weight` = share of the exam blueprint; `confidence` = your self-rating 0–5.
- **notes** — freeform, `source` distinguishes `user` from `llm`.
- **llm_profiles** — endpoint config plus a `prompts` JSONB blob holding the
  five editable prompt templates.

### AI request flow

`POST /api/ai` → load profile → resolve topic label + confidence → gather
material from `asset_ids` (or newest 6 for the topic if none selected) → truncate
to 24,000 chars → `str.format()` the chosen template → attach image assets as
base64 image parts if vision is on → append optional extra instruction → call
endpoint → return content + model + elapsed ms.

### Vision (images to the model)

Text-only models get OCR output and nothing else. With vision enabled, image
assets are *also* sent as real pixels in the same request, so the model can read
diagrams, port counts and part numbers that OCR mangles.

- Toggle lives in **Settings → Vision**; the tutor panel has a per-request
  override (`images: auto | always | never`). `auto` follows the saved setting.
- **Detect capability** sends a synthetic image containing the string `7319` and
  checks whether the model reports it back. The verdict is stored on the profile
  as `last_probe` — a text-only model silently *ignores* image parts rather than
  erroring, so probing is the only reliable way to know.
- Images are downscaled to a 1568px long edge and JPEG-recompressed (quality
  stepped down 85 → 40) before sending. A single unreadable image degrades to a
  note in the prompt instead of failing the request.
- The vision note tells the model to trust the pixels over the extracted text
  where the two disagree.

### Schema migrations

`create_all()` never adds columns to an existing table, so `app/migrations.py`
applies additive column changes on startup (currently `llm_profiles.supports_vision`
and `llm_profiles.last_probe`). Existing databases upgrade in place — no drop and
recreate needed.

---

## 4. The five tutor modes

| Mode | Placeholders | Behaviour |
|---|---|---|
| **whiteboard** | `{topic} {confidence} {material}` | Framing, structured outline, ASCII diagram, 3 likely exam facts |
| **hint** | `{topic} {question} {material}` | Progressive nudge only — explicitly forbidden from revealing the answer, under 120 words |
| **explain** | `{topic} {question} {material}` | Analogy first, then precise technical explanation, calls out common misconceptions |
| **quiz** | `{topic} {material} {count}` | Exam-style MCQ, 4 options, answer + one-line rationale |
| **gap** | `{topic} {material}` | What's missing vs the syllabus for that topic |

All templates are editable in Settings and resettable to the shipped default.
The "extra instruction" field on the main panel appends a one-off directive
without mutating saved prompts.

---

## 5. Running it

```bash
cd ~/projects/nvidia-studybuddy
./start.sh     # backend :8077 + frontend :5273
./stop.sh
```

`start.sh` starts Postgres if it isn't responding, creates the venv and installs
deps on first run, then launches both services and writes PID files to `logs/`.

Verification points:
- http://127.0.0.1:8077/api/health → `{"ok": true}`
- http://127.0.0.1:5273 → the UI
- http://127.0.0.1:8077/docs → OpenAPI

### First run

Settings → base URL + model. Blank API key for local servers.

| Backend | Base URL | Model example |
|---|---|---|
| Ollama | `http://127.0.0.1:11434/v1` | `qwen2.5:14b` |
| llama.cpp server | `http://127.0.0.1:8080/v1` | whatever `-m` loaded |
| vLLM | `http://127.0.0.1:8000/v1` | `Qwen/Qwen2.5-14B-Instruct` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| LiteLLM proxy | `http://127.0.0.1:4000/v1` | any routed model |

**Save & test** round-trips a real completion, so a green result means the
endpoint genuinely works.

---

## 6. Environment setup notes

Things that had to be done to the machine, recorded so they don't have to be
rediscovered:

1. **Postgres was not installed.** `sudo pacman -S postgresql`, then
   `initdb -D /var/lib/postgres/data`, then `systemctl enable --now postgresql`.
   Role + db: `studybuddy` / `studybuddy` (password `studybuddy`), local only.
2. **Stale package mirror.** The first `pacman -S` 404'd on `postgresql-18.6-1`
   because the local package DB was out of date. `sudo pacman -Sy` first, then
   the install resolved to `18.6-2`.
3. **tesseract not installed.** `sudo pacman -S tesseract tesseract-data-eng`.
4. **venv console scripts missing.** `/usr/bin/python3 -m venv .venv` produced no
   `bin/uvicorn` shim, so launch with `.venv/bin/python -m uvicorn …` rather than
   the bare executable. `start.sh` already does this.
5. **npm blocked esbuild's postinstall.** Vite cannot run without the esbuild
   binary. Fix: `npm install-scripts approve esbuild && npm rebuild esbuild`.
6. **Python is 3.14.7** at `/usr/bin/python3`. Node is 26.7.0, but only on PATH
   via `~/.hermes/tools/node-26.7.0-linux-x64/bin`.

---

## 7. Gotchas and design notes

- **`llm_profiles.prompts` was narrowed to exactly one key at one point** during
  testing (an API-key-only PUT with a partial `prompts` object). The full default
  set was restored. If prompts ever go missing, `GET /api/llm/default-prompts`
  returns the shipped five and Settings → reset to default restores them.
- **Template placeholders are strict.** `str.format()` raises `KeyError` on an
  unknown placeholder. If you add a placeholder to a prompt, add it to the
  `kwargs` dict in the `/api/ai` handler in `routes.py` or every call to that
  mode will 500.
- **Material truncation is 24,000 chars**, head-only (no middle-out). Long PDFs
  get cut at the tail, so page order matters when you select multiple files.
- **"Find gaps" needs real material.** With no file selected for a topic it falls
  back to the newest 6; with none at all it answers "coverage looks complete"
  from thin air. Always scope it to actual files.
- **Screenshots are stored, not just OCR'd.** The original image is on disk, so a
  future vision path can use it without re-uploading.
- **Ports are fixed** (5273 frontend, 8077 backend, `strictPort: true`). If a
  port is taken, Vite exits rather than silently shifting.

---

## 8. File map

```
backend/app/
  main.py       app entry, lifespan, syllabus + profile seeding
  routes.py     all HTTP endpoints (assets, topics, notes, llm, ai)
  models.py     SQLAlchemy tables
  schemas.py    pydantic request/response models
  extract.py    per-format text extraction (incl. 2x-upscaled OCR)
  llm.py        OpenAI-compatible client + the five default prompts
  syllabus.py   10-topic NCA-AIIO seed data
  db.py         async engine + session
  config.py     settings (DATABASE_URL, upload dir, host/port, CORS)
frontend/src/
  App.tsx        layout, state, filtering, selection
  TopicRail.tsx  syllabus sidebar, confidence stars, exam weights
  DropZone.tsx   drag/drop + global Ctrl+V paste handler
  AssetList.tsx  material list, topic assignment, previews
  TutorPanel.tsx the five modes + markdown rendering + session history
  Settings.tsx   endpoint config + prompt template editor
  api.ts         typed API client
scripts/mock_llm.py   throwaway OpenAI-compatible mock for offline testing
start.sh / stop.sh    lifecycle
data/uploads/         raw files (metadata + text in Postgres)
```

---

## 9. Verification performed

Every claim below was checked with real execution, not assumed:

- Health, seeding (10 topics, default profile) — verified via curl.
- Upload: text file, pasted text, PNG screenshot, hand-built text PDF — all
  parsed, text stored correctly.
- OCR: synthetic screenshot read back as `PCIe Gen5 x16 = 64 GB/s per direction`.
- All five AI modes against a mock OpenAI-compatible server — correct prompt
  construction confirmed for each, including topic label, confidence, and
  material injection.
- Custom prompt override — confirmed the edited template reaches the model.
- Error path — unreachable endpoint returns HTTP 502 with a clear message.
- Settings modal, topic filtering, select-all, confidence stars — driven in a
  real browser.
- Production build clean (`tsc -b` exit 0, `vite build` 291 modules).
- Known bug found and fixed during review: "All material" count excluded
  unassigned files; now reconciles with the material header.
- Vision, added after the first release and verified: profile PUT persists
  `supports_vision`; `/api/ai` attaches 2 image parts when enabled and 0 when the
  per-request override is off; a text-only asset adds no parts; the probe returns
  `verdict: vision` against a mock that reads the image and `no-vision` against
  one that cannot; migration added both columns to the existing database with no
  drop/recreate; driven in a real browser — checkbox → save → Detect capability →
  "Vision detected", then Ask tutor returned the mock's vision marker.

---

## 10. Next steps (ranked)

1. **Progress/spaced repetition.** Topics have confidence ratings but nothing
   schedules review. A simple SM-2 queue over weak topics would make the tool
   actually drive study rather than just store it.
2. **Serve built assets from FastAPI** for a single-process run instead of two
   dev servers.
3. **Per-asset chunking** so long PDFs aren't truncated at 24k chars.
4. **Export** — dump a topic's material + notes + quiz results to markdown.

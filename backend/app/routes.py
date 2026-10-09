"""HTTP API: assets, topics, notes, LLM settings, and AI assist."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import get_session
from .extract import extract_text
from .llm import (
    DEFAULT_PROMPTS,
    PROMPT_KEYS,
    VISION_NOTE,
    build_messages,
    call_llm,
    call_llm_vision_probe,
    prepare_image,
)
from .models import Asset, LlmProfile, Note, Topic
from .schemas import (
    AiRequest,
    AiResponse,
    AssetOut,
    LlmProfileIn,
    LlmProfileOut,
    NoteCreate,
    NoteOut,
    TopicOut,
    TopicUpdate,
)

router = APIRouter(prefix="/api")


# --------------------------------------------------------------------------- assets

@router.post("/assets", response_model=list[AssetOut])
async def upload_assets(
    files: list[UploadFile] = File(...),
    topic_id: int | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    created: list[Asset] = []

    for upload in files:
        raw = await upload.read()
        if not raw:
            continue
        filename = upload.filename or "unnamed"
        ctype = upload.content_type or ""
        is_image = ctype.startswith("image/")
        kind = "image" if is_image else "file"

        safe = "".join(c for c in filename if c.isalnum() or c in "._- ").strip() or "file"
        stored_name = f"{uuid.uuid4().hex[:12]}_{safe}"
        dest = upload_dir / stored_name
        dest.write_bytes(raw)

        text = ""
        err = ""
        if kind == "file" and ctype.startswith("text/"):
            text = raw.decode("utf-8", errors="replace").strip()
        elif kind != "image":
            text, err = extract_text(filename, ctype, raw)
        elif is_image:
            # OCR screenshots too -- useful for worked problems and exam screenshots.
            text, err = extract_text(filename, ctype, raw)

        asset = Asset(
            filename=filename,
            content_type=ctype,
            size_bytes=len(raw),
            kind=kind,
            stored_path=str(dest),
            extracted_text=text,
            extraction_error=err,
            topic_id=topic_id,
            meta={"stored_name": stored_name},
        )
        session.add(asset)
        created.append(asset)

    await session.commit()
    for a in created:
        await session.refresh(a)
    return created


@router.post("/assets/text", response_model=AssetOut)
async def paste_text(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    """Handle clipboard pastes (text or a pasted image data URL)."""
    content = (payload or {}).get("content", "")
    title = (payload or {}).get("title") or "pasted note"
    topic_id = (payload or {}).get("topic_id")
    if not content:
        raise HTTPException(400, "content is required")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    text, err, kind, ctype = content, "", "text", "text/plain"

    if isinstance(content, str) and content.startswith("data:image"):
        import base64
        import re

        header, _, b64 = content.partition(",")
        m = re.search(r"data:(image/[a-zA-Z+.-]+);base64", header)
        ctype = m.group(1) if m else "image/png"
        raw = base64.b64decode(b64)
        ext = ctype.split("/")[-1].replace("jpeg", "jpg")
        stored_name = f"{uuid.uuid4().hex[:12]}_paste.{ext}"
        (upload_dir / stored_name).write_bytes(raw)
        kind = "image"
        text, err = extract_text(f"paste.{ext}", ctype, raw)
        content_len = len(raw)
    else:
        stored_name = f"{uuid.uuid4().hex[:12]}_paste.txt"
        (upload_dir / stored_name).write_text(content, encoding="utf-8")
        content_len = len(content.encode())

    asset = Asset(
        filename=title,
        content_type=ctype,
        size_bytes=content_len,
        kind=kind,
        stored_path=str(upload_dir / stored_name),
        extracted_text=text,
        extraction_error=err,
        topic_id=topic_id,
        meta={"stored_name": stored_name, "pasted": True},
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(
    topic_id: int | None = None,
    q: str | None = None,
    limit: int = 200,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Asset).order_by(Asset.created_at.desc()).limit(limit)
    if topic_id is not None:
        stmt = select(Asset).where(Asset.topic_id == topic_id).order_by(Asset.created_at.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    if q:
        needle = q.lower()
        rows = [r for r in rows if needle in r.filename.lower() or needle in (r.extracted_text or "").lower()]
    return rows


@router.patch("/assets/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: int, payload: dict, session: AsyncSession = Depends(get_session)):
    asset = await session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "asset not found")
    if "topic_id" in payload:
        asset.topic_id = payload["topic_id"]
    if "filename" in payload:
        asset.filename = payload["filename"]
    await session.commit()
    await session.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: int, session: AsyncSession = Depends(get_session)):
    asset = await session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "asset not found")
    Path(asset.stored_path).unlink(missing_ok=True)
    await session.delete(asset)
    await session.commit()
    return {"deleted": asset_id}


# --------------------------------------------------------------------------- topics

@router.get("/topics", response_model=list[TopicOut])
async def list_topics(session: AsyncSession = Depends(get_session)):
    stmt = select(Topic).order_by(Topic.sort_order, Topic.id)
    return (await session.execute(stmt)).scalars().all()


@router.patch("/topics/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: int, payload: TopicUpdate, session: AsyncSession = Depends(get_session)):
    topic = await session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "topic not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(topic, field, value)
    await session.commit()
    await session.refresh(topic)
    return topic


# --------------------------------------------------------------------------- notes

@router.get("/notes", response_model=list[NoteOut])
async def list_notes(topic_id: int | None = None, session: AsyncSession = Depends(get_session)):
    stmt = select(Note).order_by(Note.created_at.desc()).limit(200)
    if topic_id is not None:
        stmt = select(Note).where(Note.topic_id == topic_id).order_by(Note.created_at.desc())
    return (await session.execute(stmt)).scalars().all()


@router.post("/notes", response_model=NoteOut)
async def create_note(payload: NoteCreate, session: AsyncSession = Depends(get_session)):
    note = Note(**payload.model_dump())
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, session: AsyncSession = Depends(get_session)):
    note = await session.get(Note, note_id)
    if not note:
        raise HTTPException(404, "note not found")
    await session.delete(note)
    await session.commit()
    return {"deleted": note_id}


# --------------------------------------------------------------------------- llm settings

def _profile_out(p: LlmProfile) -> LlmProfileOut:
    data = LlmProfileOut.model_validate(
        {
            "id": p.id,
            "name": p.name,
            "base_url": p.base_url,
            "model": p.model,
            "is_active": p.is_active,
            "supports_vision": p.supports_vision,
            "last_probe": p.last_probe or {},
            "temperature": p.temperature,
            "max_tokens": p.max_tokens,
            "prompts": p.prompts or {},
        }
    )
    data.has_key = bool(p.api_key)
    return data


@router.get("/llm/default-prompts")
async def default_prompts():
    return {"prompts": DEFAULT_PROMPTS, "keys": list(PROMPT_KEYS)}


@router.get("/llm/profile", response_model=LlmProfileOut | None)
async def get_profile(session: AsyncSession = Depends(get_session)):
    row = (await session.execute(select(LlmProfile).order_by(LlmProfile.id).limit(1))).scalars().first()
    return _profile_out(row) if row else None


@router.put("/llm/profile", response_model=LlmProfileOut)
async def put_profile(payload: LlmProfileIn, session: AsyncSession = Depends(get_session)):
    row = (await session.execute(select(LlmProfile).order_by(LlmProfile.id).limit(1))).scalars().first()
    if not row:
        row = LlmProfile()
        session.add(row)
    row.name = payload.name
    row.base_url = payload.base_url
    row.model = payload.model
    row.is_active = payload.is_active
    if payload.supports_vision is not None:
        row.supports_vision = payload.supports_vision
    row.temperature = payload.temperature
    row.max_tokens = payload.max_tokens
    if payload.api_key is not None:
        row.api_key = payload.api_key
    if payload.prompts is not None:
        row.prompts = payload.prompts
    elif not row.prompts:
        row.prompts = dict(DEFAULT_PROMPTS)
    await session.commit()
    await session.refresh(row)
    return _profile_out(row)


@router.post("/llm/vision-check")
async def vision_check(send: bool = False, session: AsyncSession = Depends(get_session)):
    """Probe whether the configured model can actually read an attached image.

    Always reports a verdict. With send=false it is purely informational (no
    call is made); with send=true it sends a synthetic image and checks whether
    the model reports the text inside it.
    """
    row = (await session.execute(select(LlmProfile).order_by(LlmProfile.id).limit(1))).scalars().first()
    if not row:
        raise HTTPException(400, "no LLM profile configured yet")
    if not row.model:
        raise HTTPException(400, "no model set in Settings yet")

    if not send:
        return {
            "sent": False,
            "supports_vision": row.supports_vision,
            "last_probe": row.last_probe or {},
            "hint": "POST with ?send=true to actually test the endpoint.",
        }

    result = await call_llm_vision_probe(
        base_url=row.base_url, api_key=row.api_key, model=row.model
    )
    result["sent"] = True
    if result.get("verdict") == "vision":
        row.supports_vision = True
    elif result.get("verdict") == "no-vision":
        row.supports_vision = False
    row.last_probe = result
    await session.commit()
    return result


@router.post("/llm/test")
async def test_llm(session: AsyncSession = Depends(get_session)):
    row = (await session.execute(select(LlmProfile).order_by(LlmProfile.id).limit(1))).scalars().first()
    if not row:
        raise HTTPException(400, "no LLM profile configured yet")
    started = time.time()
    try:
        out = await call_llm(
            base_url=row.base_url,
            api_key=row.api_key,
            model=row.model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            temperature=0.0,
            max_tokens=16,
            timeout=30.0,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "elapsed_ms": int((time.time() - started) * 1000)}
    return {"ok": True, "reply": out.strip(), "elapsed_ms": int((time.time() - started) * 1000)}


# --------------------------------------------------------------------------- ai assist

FEATURE_KEYS = set(PROMPT_KEYS)


@router.post("/ai", response_model=AiResponse)
async def ai_assist(payload: AiRequest, session: AsyncSession = Depends(get_session)):
    if payload.feature not in FEATURE_KEYS:
        raise HTTPException(400, f"unknown feature '{payload.feature}'")

    profile = (await session.execute(select(LlmProfile).order_by(LlmProfile.id).limit(1))).scalars().first()
    if not profile or not profile.model:
        raise HTTPException(400, "Configure an LLM in Settings first (base URL + model).")

    topic = await session.get(Topic, payload.topic_id) if payload.topic_id else None
    topic_label = topic.title if topic else "general NCA-AIIO material"
    confidence = topic.confidence if topic else 0

    gathered: list[Asset] = []
    if payload.asset_ids:
        gathered = list(
            (await session.execute(select(Asset).where(Asset.id.in_(payload.asset_ids))))
            .scalars()
            .all()
        )
    elif topic:
        gathered = list(
            (
                await session.execute(
                    select(Asset)
                    .where(Asset.topic_id == topic.id)
                    .order_by(Asset.created_at.desc())
                    .limit(6)
                )
            )
            .scalars()
            .all()
        )

    material_parts: list[str] = []
    for a in gathered:
        body = (a.extracted_text or "").strip()
        if body:
            material_parts.append(f"[{a.filename}]\n{body}")
        elif a.kind == "image":
            material_parts.append(f"[{a.filename}] (image, no OCR text: {a.extraction_error or 'empty'})")
        else:
            material_parts.append(f"[{a.filename}] (no text extracted: {a.extraction_error or 'empty'})")

    # Vision: attach image assets directly when enabled. A per-request flag wins
    # over the saved profile setting.
    want_vision = payload.use_vision if payload.use_vision is not None else profile.supports_vision
    images: list[str] = []
    image_notes: list[str] = []
    if want_vision:
        for a in gathered:
            if a.kind != "image":
                continue
            data_url, note = prepare_image(a.stored_path)
            if data_url:
                images.append(data_url)
                image_notes.append(note)
            else:
                image_notes.append(f"SKIPPED {note}")
        if images:
            material_parts.append(
                "Attached images: " + "; ".join(image_notes)
            )

    material = "\n\n".join(material_parts).strip() or "(no material supplied)"
    budget = 24000
    if len(material) > budget:
        material = material[:budget] + "\n\n[...truncated...]"

    kwargs = {
        "topic": topic_label,
        "confidence": confidence,
        "material": material,
        "question": payload.question or "(none given)",
        "count": payload.count,
    }
    messages = build_messages(payload.feature, profile.prompts or {}, images=images, **kwargs)
    if payload.extra:
        messages.append({"role": "user", "content": payload.extra})

    started = time.time()
    try:
        content = await call_llm(
            base_url=profile.base_url,
            api_key=profile.api_key,
            model=profile.model,
            messages=messages,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"LLM call failed: {exc}") from exc

    return AiResponse(
        feature=payload.feature,
        content=content,
        model=profile.model,
        elapsed_ms=int((time.time() - started) * 1000),
    )

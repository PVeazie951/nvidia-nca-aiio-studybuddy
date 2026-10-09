export type Asset = {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  kind: string;
  extracted_text: string;
  extraction_error: string;
  topic_id: number | null;
  created_at: string;
};

export type Topic = {
  id: number;
  slug: string;
  title: string;
  description: string;
  weight: number;
  sort_order: number;
  confidence: number;
};

export type Note = {
  id: number;
  topic_id: number | null;
  title: string;
  body: string;
  source: string;
  created_at: string;
};

export type LlmProfile = {
  id: number;
  name: string;
  base_url: string;
  model: string;
  has_key: boolean;
  is_active: boolean;
  supports_vision: boolean;
  last_probe: {
    ok?: boolean;
    verdict?: "vision" | "no-vision" | "error";
    reply?: string;
    detail?: string;
  };
  temperature: number;
  max_tokens: number;
  prompts: Record<string, string>;
};

export type AiFeature = "whiteboard" | "hint" | "explain" | "quiz" | "gap";

export type AiResponse = {
  feature: string;
  content: string;
  model: string;
  elapsed_ms: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => req<{ ok: boolean }>("/api/health"),

  listTopics: () => req<Topic[]>("/api/topics"),
  updateTopic: (id: number, patch: Partial<Topic>) =>
    req<Topic>(`/api/topics/${id}`, json("PATCH", patch)),

  listAssets: (topicId?: number | null, q?: string) => {
    const p = new URLSearchParams();
    if (topicId != null) p.set("topic_id", String(topicId));
    if (q) p.set("q", q);
    const qs = p.toString();
    return req<Asset[]>(`/api/assets${qs ? `?${qs}` : ""}`);
  },
  uploadAssets: (files: File[], topicId: number | null) => {
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    if (topicId != null) fd.append("topic_id", String(topicId));
    return req<Asset[]>("/api/assets", { method: "POST", body: fd });
  },
  pasteContent: (payload: {
    content: string;
    title?: string;
    topic_id?: number | null;
  }) => req<Asset>("/api/assets/text", json("POST", payload)),
  updateAsset: (id: number, patch: Partial<Asset>) =>
    req<Asset>(`/api/assets/${id}`, json("PATCH", patch)),
  deleteAsset: (id: number) => req<{ deleted: number }>(`/api/assets/${id}`, { method: "DELETE" }),

  listNotes: (topicId?: number | null) => {
    const qs = topicId != null ? `?topic_id=${topicId}` : "";
    return req<Note[]>(`/api/notes${qs}`);
  },
  createNote: (payload: Partial<Note>) => req<Note>("/api/notes", json("POST", payload)),
  deleteNote: (id: number) => req<{ deleted: number }>(`/api/notes/${id}`, { method: "DELETE" }),

  getProfile: () => req<LlmProfile | null>("/api/llm/profile"),
  putProfile: (payload: Record<string, unknown>) => req<LlmProfile>("/api/llm/profile", json("PUT", payload)),
  testLlm: () => req<{ ok: boolean; reply?: string; error?: string; elapsed_ms: number }>("/api/llm/test", {
    method: "POST",
  }),
  defaultPrompts: () => req<{ prompts: Record<string, string>; keys: string[] }>("/api/llm/default-prompts"),
  visionCheck: (send = false) =>
    req<{
      sent: boolean;
      ok?: boolean;
      verdict?: "vision" | "no-vision" | "error";
      reply?: string;
      detail?: string;
      supports_vision?: boolean;
      hint?: string;
    }>(`/api/llm/vision-check?send=${send}`, { method: "POST" }),

  ai: (payload: {
    feature: AiFeature;
    topic_id?: number | null;
    asset_ids?: number[];
    question?: string;
    count?: number;
    extra?: string;
    use_vision?: boolean | null;
  }) => req<AiResponse>("/api/ai", json("POST", payload)),
};

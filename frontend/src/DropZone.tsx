import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  topicId: number | null;
  onUploaded: () => void;
};

/**
 * Drop zone for files and screenshots. Also accepts clipboard paste (Ctrl+V)
 * for images and text, which is how most Nvidia dashboards/slides get captured.
 */
export default function DropZone({ topicId, onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = useCallback(
    async (files: File[]) => {
      if (!files.length) return;
      setBusy(true);
      setMsg("");
      try {
        const fd = new FormData();
        files.forEach((f) => fd.append("files", f));
        if (topicId != null) fd.append("topic_id", String(topicId));
        const res = await fetch("/api/assets", { method: "POST", body: fd });
        if (!res.ok) throw new Error(await res.text());
        const created = await res.json();
        setMsg(`Added ${created.length} item${created.length === 1 ? "" : "s"}`);
        onUploaded();
      } catch (e) {
        setMsg(`Upload failed: ${(e as Error).message}`);
      } finally {
        setBusy(false);
        setTimeout(() => setMsg(""), 4000);
      }
    },
    [topicId, onUploaded]
  );

  // Global paste handler: images become screenshots, text becomes a note asset.
  useEffect(() => {
    const onPaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      const files: File[] = [];
      let text = "";
      for (const item of items) {
        if (item.kind === "file") {
          const f = item.getAsFile();
          if (f) files.push(f);
        } else if (item.kind === "string" && item.type === "text/plain") {
          text = e.clipboardData?.getData("text/plain") ?? "";
        }
      }
      const target = e.target as HTMLElement | null;
      const inField =
        target &&
        (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);

      if (files.length) {
        e.preventDefault();
        await upload(files);
        return;
      }
      if (text.trim() && !inField) {
        e.preventDefault();
        setBusy(true);
        try {
          const res = await fetch("/api/assets/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: text,
              title: "pasted text",
              topic_id: topicId,
            }),
          });
          if (!res.ok) throw new Error(await res.text());
          setMsg("Pasted text captured");
          onUploaded();
        } catch (err) {
          setMsg(`Paste failed: ${(err as Error).message}`);
        } finally {
          setBusy(false);
          setTimeout(() => setMsg(""), 4000);
        }
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [topicId, onUploaded, upload]);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        void upload(Array.from(e.dataTransfer.files));
      }}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-xl border-2 border-dashed px-4 py-6 text-center transition ${
        dragging ? "border-emerald-400 bg-emerald-400/10" : "border-slate-700 bg-slate-900/40 hover:border-slate-500"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => {
          void upload(Array.from(e.target.files ?? []));
          e.target.value = "";
        }}
      />
      <div className="text-sm font-medium text-slate-200">
        {busy ? "Processing…" : "Drop files or screenshots here"}
      </div>
      <div className="mt-1 text-xs text-slate-400">
        or click to browse · <span className="text-emerald-400">Ctrl+V</span> pastes screenshots and text ·
        PDF, DOCX, XLSX, TXT, MD, PNG, JPG
      </div>
      {msg && <div className="mt-2 text-xs text-emerald-400">{msg}</div>}
    </div>
  );
}

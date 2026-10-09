import type { Asset } from "./api";

type Props = {
  assets: Asset[];
  selected: number[];
  onToggle: (id: number) => void;
  onDelete: (id: number) => void;
  onAssign: (id: number, topicId: number | null) => void;
  topics: { id: number; title: string }[];
  loading: boolean;
};

function fmtBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function fmtDate(s: string) {
  try {
    return new Date(s).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return s;
  }
}

export default function AssetList({
  assets,
  selected,
  onToggle,
  onDelete,
  onAssign,
  topics,
  loading,
}: Props) {
  if (loading) {
    return <div className="p-6 text-center text-sm text-slate-500">Loading material…</div>;
  }
  if (!assets.length) {
    return (
      <div className="p-6 text-center text-sm text-slate-500">
        No material yet. Drop files above, or paste with Ctrl+V.
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-900">
      {assets.map((a) => {
        const isSel = selected.includes(a.id);
        const hasText = (a.extracted_text ?? "").trim().length > 0;
        return (
          <div
            key={a.id}
            className={`flex gap-3 p-3 transition ${isSel ? "bg-emerald-500/5" : "hover:bg-slate-900/50"}`}
          >
            <input
              type="checkbox"
              checked={isSel}
              onChange={() => onToggle(a.id)}
              className="mt-1 h-4 w-4 shrink-0 accent-emerald-500"
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-medium text-slate-200 truncate">{a.filename}</span>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ${
                    a.kind === "image"
                      ? "bg-purple-500/15 text-purple-300"
                      : "bg-sky-500/15 text-sky-300"
                  }`}
                >
                  {a.kind}
                </span>
              </div>
              <div className="mt-0.5 flex flex-wrap items-center gap-x-3 text-[11px] text-slate-500">
                <span>{fmtBytes(a.size_bytes)}</span>
                <span>{fmtDate(a.created_at)}</span>
                {hasText ? (
                  <span className="text-emerald-500">text extracted ({a.extracted_text.length} chars)</span>
                ) : (
                  <span className="text-amber-500">{a.extraction_error || "no text"}</span>
                )}
              </div>
              {hasText && (
                <details className="mt-1">
                  <summary className="cursor-pointer text-[11px] text-slate-500 hover:text-slate-300">
                    preview extracted text
                  </summary>
                  <pre className="mt-1 max-h-40 overflow-auto rounded bg-slate-950 p-2 text-[11px] leading-relaxed text-slate-400 whitespace-pre-wrap">
                    {a.extracted_text.slice(0, 2000)}
                  </pre>
                </details>
              )}
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <select
                value={a.topic_id ?? ""}
                onChange={(e) => onAssign(a.id, e.target.value ? Number(e.target.value) : null)}
                className="max-w-[150px] rounded border border-slate-700 bg-slate-900 px-1.5 py-1 text-[11px] text-slate-300"
              >
                <option value="">— unassigned —</option>
                {topics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </select>
              <button
                onClick={() => onDelete(a.id)}
                className="text-[11px] text-slate-500 hover:text-red-400"
              >
                delete
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

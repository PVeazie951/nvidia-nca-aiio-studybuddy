import type { Topic } from "./api";

type Props = {
  topics: Topic[];
  activeTopic: number | null;
  onSelect: (id: number | null) => void;
  onConfidence: (id: number, value: number) => void;
  counts: Record<number, number>;
  totalFiles: number;
};

function Stars({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex gap-0.5" onClick={(e) => e.stopPropagation()}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          title={`Confidence ${n}/5`}
          onClick={() => onChange(n === value ? 0 : n)}
          className={`text-[13px] leading-none transition ${
            n <= value ? "text-amber-400" : "text-slate-600 hover:text-slate-400"
          }`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export default function TopicRail({
  topics,
  activeTopic,
  onSelect,
  onConfidence,
  counts,
  totalFiles,
}: Props) {
  const totalWeight = topics.reduce((s, t) => s + t.weight, 0) || 1;

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-slate-800 bg-slate-950">
      <div className="border-b border-slate-800 p-3">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Syllabus</div>
        <div className="mt-1 flex items-baseline justify-between">
          <span className="text-[11px] text-slate-500">NCA-AIIO</span>
          <span className="text-[11px] text-amber-400/80">★ = your confidence · % = exam weight</span>
        </div>
      </div>

      <button
        onClick={() => onSelect(null)}
        className={`border-b border-slate-800 px-3 py-2 text-left text-xs transition ${
          activeTopic === null ? "bg-slate-800 text-emerald-300" : "text-slate-400 hover:bg-slate-900"
        }`}
      >
        All material ({totalFiles})
      </button>

      <div className="flex-1 overflow-y-auto">
        {topics.map((t) => {
          const active = activeTopic === t.id;
          const pct = Math.round((t.weight / totalWeight) * 100);
          return (
            <div
              key={t.id}
              onClick={() => onSelect(active ? null : t.id)}
              className={`cursor-pointer border-b border-slate-900 px-3 py-2 transition ${
                active ? "bg-slate-800" : "hover:bg-slate-900"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span
                  className={`text-[13px] font-medium leading-snug ${
                    active ? "text-emerald-300" : "text-slate-200"
                  }`}
                >
                  {t.title}
                </span>
                <span
                  title="share of the exam blueprint"
                  className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400"
                >
                  {pct}%
                </span>
              </div>
              <div className="mt-1 flex items-center justify-between">
                <Stars value={t.confidence} onChange={(v) => onConfidence(t.id, v)} />
                <span className="text-[10px] text-slate-500">{counts[t.id] ?? 0} files</span>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

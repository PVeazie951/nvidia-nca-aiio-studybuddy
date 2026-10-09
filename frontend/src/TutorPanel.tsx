import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, type AiFeature, type AiResponse, type Topic } from "./api";

type Props = {
  activeTopic: number | null;
  topics: Topic[];
  selectedCount: number;
  selectedIds: number[];
  configured: boolean;
  onOpenSettings: () => void;
};

const FEATURES: { key: AiFeature; label: string; hint: string }[] = [
  { key: "whiteboard", label: "Whiteboard", hint: "Full topic breakdown with diagram" },
  { key: "hint", label: "Hint", hint: "Progressive nudge, no answer" },
  { key: "explain", label: "Explain", hint: "Analogy-first deep explanation" },
  { key: "quiz", label: "Quiz me", hint: "Exam-style multiple choice" },
  { key: "gap", label: "Find gaps", hint: "What's missing vs the syllabus" },
];

export default function TutorPanel({
  activeTopic,
  selectedCount,
  selectedIds,
  configured,
  onOpenSettings,
}: Props) {
  const [feature, setFeature] = useState<AiFeature>("whiteboard");
  const [question, setQuestion] = useState("");
  const [count, setCount] = useState(5);
  const [extra, setExtra] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AiResponse | null>(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<AiResponse[]>([]);

  const needsQuestion = feature === "hint" || feature === "explain";

  async function run() {
    setBusy(true);
    setError("");
    try {
      const res = await api.ai({
        feature,
        topic_id: activeTopic,
        asset_ids: selectedIds,
        question,
        count,
        extra,
      });
      setResult(res);
      setHistory((h) => [res, ...h].slice(0, 12));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap gap-1.5 border-b border-slate-800 p-3">
        {FEATURES.map((f) => (
          <button
            key={f.key}
            title={f.hint}
            onClick={() => setFeature(f.key)}
            className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
              feature === f.key
                ? "bg-emerald-500 text-slate-950"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="space-y-2 border-b border-slate-800 p-3">
        {needsQuestion && (
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              feature === "hint"
                ? "Paste the question you're stuck on…"
                : "What are you confused about?"
            }
            rows={3}
            className="w-full resize-y rounded-md border border-slate-700 bg-slate-900 px-2.5 py-2 text-[13px] text-slate-200 outline-none focus:border-emerald-500"
          />
        )}
        {feature === "quiz" && (
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Number of questions
            <input
              type="number"
              min={1}
              max={20}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200"
            />
          </label>
        )}
        <input
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          placeholder="Optional extra instruction for the model…"
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
        />
        <div className="flex items-center gap-2">
          <button
            onClick={run}
            disabled={busy}
            className="rounded-md bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-40"
          >
            {busy ? "Thinking…" : "Ask tutor"}
          </button>
          <span className="text-[11px] text-slate-500">
            {selectedCount > 0
              ? `${selectedCount} selected file${selectedCount === 1 ? "" : "s"} in scope`
              : activeTopic
                ? "using newest files for this topic"
                : "using newest files overall"}
          </span>
        </div>
        {!configured && (
          <div className="rounded-md border border-amber-600/40 bg-amber-500/10 px-2.5 py-2 text-[11px] text-amber-300">
            No model configured yet.{" "}
            <button onClick={onOpenSettings} className="underline hover:text-amber-200">
              Open settings
            </button>{" "}
            to point at an OpenAI-compatible endpoint.
          </div>
        )}
        {error && (
          <div className="rounded-md border border-red-600/40 bg-red-500/10 px-2.5 py-2 text-[11px] text-red-300">
            {error}
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {!result && !busy && (
          <div className="mt-8 text-center text-sm text-slate-600">
            Pick a mode and hit <span className="text-slate-400">Ask tutor</span>.
            <div className="mt-1 text-xs">
              Select files on the left to scope what the model sees.
            </div>
          </div>
        )}
        {result && (
          <article className="md-body max-w-none text-[13px]">
            <div className="mb-3 flex items-center gap-2 text-[11px] text-slate-500">
              <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-emerald-300">
                {result.feature}
              </span>
              <span>{result.model}</span>
              <span>· {(result.elapsed_ms / 1000).toFixed(1)}s</span>
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.content}</ReactMarkdown>
          </article>
        )}
        {history.length > 1 && (
          <div className="mt-8 border-t border-slate-800 pt-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Earlier in this session
            </div>
            {history.slice(1).map((h, i) => (
              <details key={i} className="mb-1">
                <summary className="cursor-pointer text-[11px] text-slate-500 hover:text-slate-300">
                  {h.feature} · {h.model} · {(h.elapsed_ms / 1000).toFixed(1)}s
                </summary>
                <div className="md-body mt-2 text-[12px]">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{h.content}</ReactMarkdown>
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api, type LlmProfile } from "./api";

type Props = { onClose: () => void; onSaved: () => void };

const KEYS = ["whiteboard", "hint", "explain", "quiz", "gap"] as const;

export default function Settings({ onClose, onSaved }: Props) {
  const [profile, setProfile] = useState<LlmProfile | null>(null);
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [temperature, setTemperature] = useState(0.3);
  const [maxTokens, setMaxTokens] = useState(1500);
  const [prompts, setPrompts] = useState<Record<string, string>>({});
  const [defaults, setDefaults] = useState<Record<string, string>>({});
  const [activeKey, setActiveKey] = useState<(typeof KEYS)[number]>("whiteboard");
  const [status, setStatus] = useState("");
  const [testOut, setTestOut] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      const [p, d] = await Promise.all([api.getProfile(), api.defaultPrompts()]);
      setDefaults(d.prompts);
      if (p) {
        setProfile(p);
        setBaseUrl(p.base_url);
        setModel(p.model);
        setTemperature(p.temperature);
        setMaxTokens(p.max_tokens);
        setPrompts({ ...d.prompts, ...(p.prompts ?? {}) });
      } else {
        setPrompts({ ...d.prompts });
      }
    })();
  }, []);

  async function save() {
    setBusy(true);
    setStatus("");
    try {
      const saved = await api.putProfile({
        name: profile?.name ?? "default",
        base_url: baseUrl,
        model,
        ...(apiKey ? { api_key: apiKey } : {}),
        temperature,
        max_tokens: maxTokens,
        prompts,
      });
      setProfile(saved);
      setApiKey("");
      setStatus("Saved.");
      onSaved();
    } catch (e) {
      setStatus(`Save failed: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function test() {
    setBusy(true);
    setTestOut("");
    try {
      await save();
      const r = await api.testLlm();
      setTestOut(r.ok ? `OK — model replied: ${r.reply}` : `Failed: ${r.error}`);
    } catch (e) {
      setTestOut(`Failed: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  const field =
    "w-full rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-[13px] text-slate-200 outline-none focus:border-emerald-500";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-950">
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-100">Model & Prompt Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            ✕
          </button>
        </div>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="text-[11px] font-medium text-slate-400">Base URL (OpenAI-compatible)</span>
              <input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:11434/v1"
                className={`${field} mt-1`}
              />
            </label>
            <label className="block">
              <span className="text-[11px] font-medium text-slate-400">Model name</span>
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="qwen2.5:14b, gpt-4o, llama-3.3-70b…"
                className={`${field} mt-1`}
              />
            </label>
            <label className="block">
              <span className="text-[11px] font-medium text-slate-400">
                API key {profile?.has_key && <span className="text-emerald-500">(saved — blank to keep)</span>}
              </span>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-… (leave blank for local servers)"
                className={`${field} mt-1`}
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-[11px] font-medium text-slate-400">Temperature</span>
                <input
                  type="number"
                  step={0.1}
                  min={0}
                  max={2}
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className={`${field} mt-1`}
                />
              </label>
              <label className="block">
                <span className="text-[11px] font-medium text-slate-400">Max tokens</span>
                <input
                  type="number"
                  step={100}
                  min={100}
                  max={32000}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className={`${field} mt-1`}
                />
              </label>
            </div>
          </div>

          <div className="rounded-md border border-slate-800 bg-slate-900/40 p-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Prompt templates
            </div>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {KEYS.map((k) => (
                <button
                  key={k}
                  onClick={() => setActiveKey(k)}
                  className={`rounded px-2 py-1 text-[11px] ${
                    activeKey === k
                      ? "bg-emerald-500 text-slate-950"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {k}
                </button>
              ))}
            </div>
            <textarea
              value={prompts[activeKey] ?? ""}
              onChange={(e) => setPrompts((p) => ({ ...p, [activeKey]: e.target.value }))}
              rows={12}
              className={`${field} font-mono text-[11px] leading-relaxed`}
            />
            <div className="mt-1.5 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">
                Placeholders:{" "}
                <code className="text-slate-400">
                  {activeKey === "hint" || activeKey === "explain"
                    ? "{topic} {question} {material}"
                    : activeKey === "quiz"
                      ? "{topic} {material} {count}"
                      : activeKey === "whiteboard"
                        ? "{topic} {confidence} {material}"
                        : "{topic} {material}"}
                </code>
              </span>
              <button
                onClick={() => setPrompts((p) => ({ ...p, [activeKey]: defaults[activeKey] }))}
                className="text-[10px] text-slate-500 underline hover:text-slate-300"
              >
                reset to default
              </button>
            </div>
          </div>

          <div className="rounded-md border border-slate-800 bg-slate-900/40 p-3 text-[11px] text-slate-400">
            <div className="mb-1 font-semibold text-slate-300">Common endpoints</div>
            <ul className="space-y-0.5">
              <li>• Ollama: <code>http://127.0.0.1:11434/v1</code> — model e.g. <code>qwen2.5:14b</code></li>
              <li>• llama.cpp server: <code>http://127.0.0.1:8080/v1</code></li>
              <li>• vLLM: <code>http://127.0.0.1:8000/v1</code></li>
              <li>• OpenAI: <code>https://api.openai.com/v1</code></li>
              <li>• LiteLLM proxy: <code>http://127.0.0.1:4000/v1</code> (one URL, many backends)</li>
            </ul>
          </div>

          {status && <div className="text-[11px] text-emerald-400">{status}</div>}
          {testOut && <div className="text-[11px] text-slate-300">{testOut}</div>}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-slate-800 px-4 py-3">
          <button
            onClick={test}
            disabled={busy}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-40"
          >
            Save & test
          </button>
          <button
            onClick={save}
            disabled={busy}
            className="rounded-md bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-40"
          >
            {busy ? "Working…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

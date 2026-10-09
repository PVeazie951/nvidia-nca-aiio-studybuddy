import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type Asset, type Topic } from "./api";
import AssetList from "./AssetList";
import DropZone from "./DropZone";
import Settings from "./Settings";
import TopicRail from "./TopicRail";
import TutorPanel from "./TutorPanel";

export default function App() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [activeTopic, setActiveTopic] = useState<number | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [configured, setConfigured] = useState(false);
  const [toast, setToast] = useState("");

  const refreshTopics = useCallback(async () => {
    setTopics(await api.listTopics());
  }, []);

  const refreshAssets = useCallback(async () => {
    setAssets(await api.listAssets());
    setLoading(false);
  }, []);

  const refreshConfigured = useCallback(async () => {
    const p = await api.getProfile();
    setConfigured(Boolean(p && p.model));
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        await refreshTopics();
        await refreshAssets();
        await refreshConfigured();
      } catch (e) {
        setToast(`Backend unreachable: ${(e as Error).message}`);
      }
    })();
  }, [refreshTopics, refreshAssets, refreshConfigured]);

  const counts = useMemo(() => {
    const c: Record<number, number> = {};
    for (const a of assets) {
      if (a.topic_id != null) c[a.topic_id] = (c[a.topic_id] ?? 0) + 1;
    }
    return c;
  }, [assets]);

  const visible = useMemo(() => {
    let list = assets;
    if (activeTopic != null) list = list.filter((a) => a.topic_id === activeTopic);
    if (search.trim()) {
      const n = search.toLowerCase();
      list = list.filter(
        (a) =>
          a.filename.toLowerCase().includes(n) ||
          (a.extracted_text ?? "").toLowerCase().includes(n)
      );
    }
    return list;
  }, [assets, activeTopic, search]);

  async function onConfidence(id: number, value: number) {
    setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, confidence: value } : t)));
    await api.updateTopic(id, { confidence: value });
  }

  async function onDelete(id: number) {
    await api.deleteAsset(id);
    setSelected((s) => s.filter((x) => x !== id));
    await refreshAssets();
  }

  async function onAssign(id: number, topicId: number | null) {
    await api.updateAsset(id, { topic_id: topicId });
    await refreshAssets();
  }

  async function clearTopicMaterial() {
    if (activeTopic == null) return;
    const targets = assets.filter((a) => a.topic_id === activeTopic);
    if (!targets.length) return;
    if (!confirm(`Delete all ${targets.length} files assigned to this topic?`)) return;
    for (const t of targets) await api.deleteAsset(t.id);
    setSelected([]);
    await refreshAssets();
  }

  const activeTopicObj = topics.find((t) => t.id === activeTopic) ?? null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-200">
      <TopicRail
        topics={topics}
        activeTopic={activeTopic}
        onSelect={setActiveTopic}
        onConfidence={onConfidence}
        counts={counts}
        totalFiles={assets.length}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 px-4 py-2.5">
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-slate-100">
              {activeTopicObj ? activeTopicObj.title : "All study material"}
            </h1>
            <p className="truncate text-[11px] text-slate-500">
              {activeTopicObj?.description || "NVIDIA NCA-AIIO exam prep workspace"}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search material…"
              className="w-44 rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500"
            />
            {activeTopic != null && (
              <button
                onClick={clearTopicMaterial}
                className="rounded-md border border-slate-700 px-2.5 py-1.5 text-xs text-slate-400 hover:border-red-600 hover:text-red-400"
              >
                Clear topic
              </button>
            )}
            <button
              onClick={() => setShowSettings(true)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium ${
                configured
                  ? "border border-slate-700 text-slate-300 hover:bg-slate-800"
                  : "bg-amber-500 text-slate-950 hover:bg-amber-400"
              }`}
            >
              {configured ? "Settings" : "Configure model"}
            </button>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(340px,1fr)_minmax(420px,1.15fr)]">
          <section className="flex min-h-0 flex-col border-r border-slate-800">
            <div className="p-3">
              <DropZone topicId={activeTopic} onUploaded={refreshAssets} />
            </div>
            <div className="flex items-center justify-between border-y border-slate-800 px-3 py-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Material ({visible.length})
              </span>
              <div className="flex items-center gap-2">
                {selected.length > 0 && (
                  <button
                    onClick={() => setSelected([])}
                    className="text-[11px] text-slate-500 hover:text-slate-300"
                  >
                    clear selection ({selected.length})
                  </button>
                )}
                {visible.length > 0 && (
                  <button
                    onClick={() =>
                      setSelected(
                        selected.length === visible.length ? [] : visible.map((a) => a.id)
                      )
                    }
                    className="text-[11px] text-slate-500 hover:text-slate-300"
                  >
                    {selected.length === visible.length ? "deselect all" : "select all"}
                  </button>
                )}
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <AssetList
                assets={visible}
                selected={selected}
                onToggle={(id) =>
                  setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
                }
                onDelete={onDelete}
                onAssign={onAssign}
                topics={topics}
                loading={loading}
              />
            </div>
          </section>

          <section className="min-h-0">
            <TutorPanel
              activeTopic={activeTopic}
              topics={topics}
              selectedCount={selected.length}
              selectedIds={selected}
              configured={configured}
              onOpenSettings={() => setShowSettings(true)}
            />
          </section>
        </div>
      </main>

      {showSettings && (
        <Settings
          onClose={() => setShowSettings(false)}
          onSaved={() => {
            void refreshConfigured();
            setToast("Model settings saved");
            setTimeout(() => setToast(""), 2500);
          }}
        />
      )}

      {toast && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

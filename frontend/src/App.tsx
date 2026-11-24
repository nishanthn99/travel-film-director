import { useEffect, useMemo, useRef, useState } from "react";
import {
  Aperture, ArrowUpRight, Check, ChevronRight, Clapperboard, Film,
  FolderOpen, LoaderCircle, Play, Plus, Sparkles, UploadCloud, WandSparkles,
} from "lucide-react";

type Asset = {
  id: string; name: string; media_type: "video" | "image"; size_bytes: number;
  duration_seconds: number | null; width: number | null; height: number | null;
  metadata_available: boolean;
};
type Scene = { id: string; title: string; direction: string; start_seconds: number; duration_seconds: number; suggested_shot: string };
type Board = { title: string; destination: string; mood: string; aspect_ratio: string; target_duration_seconds: number; trip_summary: string; scenes: Scene[]; note: string };

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "https://travel-film-director-api-o40j.onrender.com").replace(/\/$/, "");
const HOSTED_DEMO = import.meta.env.PROD;
const API = `${API_BASE}/api`;
const absoluteMediaUrl = (path: string) => `${API_BASE}${path}`;
const formatBytes = (bytes: number) => bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
const formatTime = (seconds: number | null) => seconds == null ? "—" : `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;

export default function App() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [destination, setDestination] = useState("");
  const [description, setDescription] = useState("");
  const [mood, setMood] = useState("Cinematic & warm");
  const [duration, setDuration] = useState(45);
  const [ratio, setRatio] = useState("9:16");
  const [board, setBoard] = useState<Board | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [renderUrl, setRenderUrl] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const selectedVideos = useMemo(() => assets.filter(a => selected.includes(a.id) && a.media_type === "video"), [assets, selected]);

  async function loadAssets() {
    try {
      const response = await fetch(`${API}/media`);
      if (response.ok) setAssets((await response.json()).assets);
    } catch { setMessage("Could not reach the local API. Start the backend on port 8000."); }
  }
  useEffect(() => { void loadAssets(); }, []);

  async function uploadFiles(files: FileList | File[]) {
    if (!files.length) return;
    setUploading(true); setMessage("");
    const form = new FormData();
    Array.from(files).forEach(file => form.append("files", file));
    try {
      const response = await fetch(`${API}/media/upload`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Upload failed");
      setAssets(current => [...payload.assets, ...current]);
      setSelected(current => [...new Set([...current, ...payload.assets.map((a: Asset) => a.id)])]);
      setMessage(`${payload.assets.length} file(s) added to your local library.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Upload failed."); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function generateStoryboard() {
    setBusy(true); setMessage(""); setRenderUrl("");
    try {
      const response = await fetch(`${API}/storyboard`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ destination: destination || "Your destination", trip_description: description, mood, target_duration_seconds: duration, aspect_ratio: ratio }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Could not create storyboard");
      setBoard(payload);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Storyboard generation failed."); }
    finally { setBusy(false); }
  }

  async function renderFilm() {
    if (!selectedVideos.length) { setMessage("Select at least one video clip. Images are not renderable in this MVP yet."); return; }
    setBusy(true); setMessage(""); setRenderUrl("");
    try {
      const response = await fetch(`${API}/render`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset_ids: selectedVideos.map(a => a.id), aspect_ratio: ratio, title: destination || "My trip", clip_seconds: 5 }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Render failed");
      setRenderUrl(payload.url); setMessage("Your local video export is ready.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Render failed."); }
    finally { setBusy(false); }
  }

  function toggleAsset(id: string) {
    setSelected(current => current.includes(id) ? current.filter(value => value !== id) : [...current, id]);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#"><span className="brand-mark"><Aperture size={19} /></span><span>FRAME<span className="brand-light">TRIP</span></span></a>
        <div className="topbar-right"><span className="local-pill"><span /> {HOSTED_DEMO ? "HOSTED DEMO" : "LOCAL WORKSPACE"}</span><a className="github-link" href="https://github.com/nishanthn99/travel-film-director" target="_blank" rel="noreferrer">Open source <ArrowUpRight size={14} /></a></div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={13} /> YOUR TRIP. YOUR STORY.</div>
          <h1>Make memories<br /><em>move.</em></h1>
          <p>Bring your travel footage together. Shape the moments into a film that feels like being there all over again.</p>
          <div className="hero-meta"><span><FolderOpen size={14} /> {HOSTED_DEMO ? "No account required" : "Your files stay on your device"}</span><span><Aperture size={14} /> No subscription required</span></div>
        </div>
        <div className="hero-art" aria-label="Abstract cinematic mountain landscape">
          <div className="sun" /><div className="mountain mountain-back" /><div className="mountain mountain-front" />
          <div className="art-caption"><span>01 / THE JOURNEY</span><span>STORIES IN MOTION</span></div>
        </div>
      </section>

      <div className="workspace-heading"><div><span className="eyebrow">THE EDIT SUITE</span><h2>Build your travel film</h2></div><span className="step-count">01 — 03</span></div>
      <div className="workspace-grid">
        <section className="panel media-panel">
          <div className="panel-heading"><div className="panel-icon"><Film size={17} /></div><div><h3>Your footage</h3><p>Bring the raw moments together</p></div><span className="count">{assets.length.toString().padStart(2, "0")}</span></div>
          <div className={`dropzone ${HOSTED_DEMO ? "dropzone-disabled" : ""}`} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (HOSTED_DEMO) setMessage("Media uploads are available in the local version. The hosted demo currently supports storyboard generation."); else void uploadFiles(e.dataTransfer.files); }}>
            <div className="upload-icon">{uploading ? <LoaderCircle className="spin" /> : <UploadCloud />}</div>
            <strong>{uploading ? "Adding your footage…" : "Drop your trip media here"}</strong>
            <span>MP4, MOV, WEBM, JPG, PNG · up to 500 MB each</span>
            <button className="outline-button" onClick={() => fileRef.current?.click()} disabled={uploading}><Plus size={15} /> Browse files</button>
            <input ref={fileRef} hidden type="file" multiple accept="video/*,image/jpeg,image/png,image/webp" onChange={e => e.target.files && void uploadFiles(e.target.files)} />
          </div>
          <div className="asset-header"><span>MEDIA LIBRARY</span><span>{selected.length} SELECTED</span></div>
          <div className="asset-list">
            {assets.length === 0 ? <div className="empty-assets"><Clapperboard size={23} /><span>Your footage will appear here.</span></div> : assets.map(asset => (
              <button className={`asset-row ${selected.includes(asset.id) ? "is-selected" : ""}`} key={asset.id} onClick={() => toggleAsset(asset.id)}>
                <span className="asset-thumb">{asset.media_type === "video" ? <Film size={17} /> : <Aperture size={17} />}</span>
                <span className="asset-info"><strong>{asset.name}</strong><small>{asset.media_type.toUpperCase()} · {formatBytes(asset.size_bytes)}{asset.duration_seconds ? ` · ${formatTime(asset.duration_seconds)}` : ""}</small></span>
                <span className="asset-check">{selected.includes(asset.id) && <Check size={13} />}</span>
              </button>
            ))}
          </div>
          <div className="panel-footnote">{HOSTED_DEMO ? "Hosted demo mode: media upload and video rendering are disabled. Run locally for private file processing." : "Stored in your local backend folder. Nothing is uploaded to a third-party service."}</div>
        </section>

        <section className="panel brief-panel">
          <div className="panel-heading"><div className="panel-icon"><WandSparkles size={17} /></div><div><h3>Tell your story</h3><p>Give your edit a sense of place</p></div></div>
          <label className="field-label" htmlFor="destination">WHERE DID YOU GO?</label>
          <input id="destination" className="text-input" placeholder="e.g. The quiet roads of Coorg" value={destination} onChange={e => setDestination(e.target.value)} />
          <label className="field-label" htmlFor="description">WHAT MADE THIS TRIP SPECIAL?</label>
          <textarea id="description" className="text-input text-area" placeholder="Coffee estates at sunrise, misty mountain drives, a waterfall trek with friends…" value={description} onChange={e => setDescription(e.target.value)} rows={4} />
          <label className="field-label">THE FEELING</label>
          <div className="mood-options">{["Cinematic & warm", "Adventure", "Dreamy", "Energetic"].map(item => <button key={item} className={mood === item ? "mood active" : "mood"} onClick={() => setMood(item)}>{item}</button>)}</div>
          <div className="field-row">
            <div className="field-grow"><label className="field-label" htmlFor="duration">FILM LENGTH</label><select id="duration" className="text-input" value={duration} onChange={e => setDuration(Number(e.target.value))}><option value={30}>30 seconds</option><option value={45}>45 seconds</option><option value={60}>1 minute</option><option value={90}>90 seconds</option><option value={120}>2 minutes</option><option value={180}>3 minutes</option></select></div>
            <div className="field-grow"><label className="field-label" htmlFor="ratio">FORMAT</label><select id="ratio" className="text-input" value={ratio} onChange={e => setRatio(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option></select></div>
          </div>
          <button className="primary-button" onClick={() => void generateStoryboard()} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />} Create my storyboard <ChevronRight size={16} /></button>
          <p className="small-note">Creates a first-draft travel narrative locally. Footage-aware AI analysis is planned for a later milestone.</p>
        </section>
      </div>

      {board && <section className="storyboard-section">
        <div className="section-title"><div><span className="eyebrow">THE FIRST CUT</span><h2>{board.title}</h2></div><span className="duration-tag">{board.target_duration_seconds}s · {board.aspect_ratio}</span></div>
        <p className="board-note">{board.note}</p>
        <div className="storyboard-grid">{board.scenes.map((scene, index) => <article className="scene-card" key={scene.id}><div className={`scene-number scene-${index + 1}`}>0{index + 1}</div><div className="scene-time">{formatTime(scene.start_seconds)} · {scene.duration_seconds}s</div><h3>{scene.title}</h3><p>{scene.direction}</p><span className="shot-tag">{scene.suggested_shot}</span></article>)}</div>
        <div className="render-bar"><div><strong>Ready for a first cut?</strong><span>Concatenate selected video clips into a local MP4 export.</span></div><button className="primary-button render-button" onClick={() => void renderFilm()} disabled={busy || selectedVideos.length === 0 || HOSTED_DEMO}>{busy ? <LoaderCircle className="spin" size={16} /> : <Play size={16} />} {HOSTED_DEMO ? "Rendering available locally" : "Render selected clips"}</button></div>
        {renderUrl && <a className="export-link" href={absoluteMediaUrl(renderUrl)} target="_blank" rel="noreferrer"><Check size={16} /> Open your rendered film <ArrowUpRight size={14} /></a>}
      </section>}

      {message && <div className="toast" role="status">{message}</div>}
      <footer className="footer"><span>FRAME<span className="brand-light">TRIP</span> · A LITTLE MORE CINEMA IN EVERY JOURNEY</span><span>OPEN SOURCE · LOCAL FIRST <Aperture size={13} /></span></footer>
    </main>
  );
}

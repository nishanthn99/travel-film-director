# Travel Film Director

An open-source, local-first AI-assisted travel video editor. Turn a folder of trip photos and videos into a story-driven edit: import media, describe the trip, generate an editable storyboard, and render a video locally.

> **Zero-cost by default:** no account, subscription, API key, or cloud upload is required. Media stays on the machine running the backend. AI integrations and social-platform discovery are intentionally optional and are not required by the MVP.

## MVP status

- [x] Local media upload and metadata inspection
- [x] Trip brief and editable storyboard generation (local Ollama with deterministic demo fallback)
- [x] Local FFmpeg render pipeline for selected video clips
- [x] React workspace with upload, asset library, storyboard and render controls
- [x] API tests and CI workflow
- [ ] Reference URL collection and manual style notes
- [ ] Optional local vision-language model integration
- [ ] Timeline editor, transitions, audio mixing and cloud-drive import

## Architecture

- **Web:** React 18, TypeScript, Vite
- **API:** Python 3.11+, FastAPI, Pydantic
- **Media:** FFmpeg / ffprobe (optional for metadata; required to render)
- **Storage:** local `data/uploads` and `data/exports` directories
- **Tests:** pytest + HTTPX; frontend production build in GitHub Actions

Local storyboard generation uses Ollama when enabled. The deterministic storyboard is retained for the hosted demo and as an explicit non-AI fallback. No hosted AI API or API key is used.

## Run locally

### Requirements
- Python 3.11+
- Node.js 20+
- FFmpeg and ffprobe on PATH (needed for video rendering)

### 1. Start the API
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Start the web app
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

Vite proxies `/api` requests to the API at port 8000.

## Local AI with Ollama

The local backend connects to the Ollama HTTP API on the same machine. By default it expects `http://127.0.0.1:11434` and the `qwen2.5:3b` model. Install Ollama from [ollama.com](https://ollama.com/), then run:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Keep Ollama running, start the FastAPI backend, and open the frontend. The workspace displays the connection state. `GET /api/ai/status` reports whether the configured model is available. `POST /api/storyboard` uses the local model when `OLLAMA_ENABLED=true` (the default). If Ollama is unavailable, the API returns an actionable 503 rather than silently pretending the result is AI-generated.

Optional backend environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_ENABLED` | `true` | Set `false` to use the deterministic template locally |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Model name already pulled in Ollama |
| `OLLAMA_TIMEOUT_SECONDS` | `180` | Generation request timeout |

For a different model, pull it with `ollama pull <model>` and set `OLLAMA_MODEL` to that exact name. Keep Ollama bound to localhost; do not expose its unauthenticated API to the public internet. The hosted Render demo intentionally uses the deterministic template because the free web service does not host a local model runtime.

**Current AI scope:** the model creates a personalized storyboard from the trip brief. It does not yet inspect uploaded footage, classify video frames, match clips, or make edits. Those require a later vision-analysis and media-matching milestone.

## Rendering notes

The current renderer accepts video clips, normalizes them to the selected aspect ratio and frame rate, concatenates them, and writes an MP4 to `backend/data/exports`. Rendering is local and may take time. Images are accepted in the library and storyboard but image-to-video rendering is not yet part of this MVP. Use footage you own or have permission to edit; add music only when you have the required rights.

## Privacy and safety

- Uploaded media is stored locally by the backend.
- The API binds to localhost by default when run using the commands above.
- Do not expose the development server to the public internet without authentication, upload limits, and deployment hardening.
- Files are validated by extension and size; this is a personal-use prototype, not a hardened multi-user service.

## Roadmap

1. **Media intelligence:** sampled keyframes, scene labels, duplicate detection and chronology hints.
2. **Reference discovery:** save public URLs supplied by the user; never scrape private or restricted social content.
3. **Reference DNA:** describe pacing, framing, transitions and color mood as an editable style brief.
4. **Story matching:** map the user's own clips to storyboard beats.
5. **Editing:** add image clips, transitions, audio ducking, captions and preview timeline.
6. **Optional AI:** local Ollama / open-source vision models; external free tiers only when explicitly configured.

## License

MIT. See [LICENSE](LICENSE).


## Free demo deployment

The recommended free-tier demo uses **Cloudflare Pages** for the Vite frontend and **Render** for the FastAPI API. This is a public demo deployment, not a production media-hosting architecture.

### Deploy the API on Render

1. Sign in to [Render](https://render.com/) and choose **New → Blueprint**.
2. Connect this GitHub repository. Render detects the root `render.yaml`.
3. Create the web service using the Free instance type.
4. After deployment, copy the service URL (for example, `https://your-service.onrender.com`).

The free instance can sleep when idle. The hosted blueprint enables demo mode, which disables public uploads and cloud rendering because this service has no persistent media storage or authentication. Use the hosted site to try storyboard generation. Keep actual media upload and FFmpeg rendering local for now.

### Deploy the frontend on Cloudflare Pages

1. In [Cloudflare Dashboard](https://dash.cloudflare.com/), open **Workers & Pages → Create → Pages → Connect to Git**.
2. Select `nishanthn99/travel-film-director` and the `main` branch.
3. Set the root directory to `frontend`.
4. Set build command to `npm run build` and output directory to `dist`.
5. Add the environment variable `VITE_API_BASE_URL` with the Render service URL, without a trailing slash (for example, `https://your-service.onrender.com`).
6. Deploy.

### Configure API CORS

After Cloudflare gives you the Pages URL, open the Render service's Environment settings and set `TFD_ALLOWED_ORIGINS` to the exact frontend origin, for example `https://your-project.pages.dev`. Separate multiple origins with commas. Save changes and redeploy.

### Important limitations of the free demo

- Render free services may spin down after inactivity, so the first request can be slow.
- Render's filesystem is ephemeral. Do not treat it as permanent storage or upload personal/irreplaceable travel footage.
- The hosted demo is suitable for testing the storyboard flow only. Public upload and rendering endpoints are deliberately disabled to prevent anonymous file storage and resource abuse.
- The current app has no user authentication or per-user storage isolation. Do not expose sensitive media or use it as a multi-user production service.
- For a reliable public editor, we will need a secure upload/storage design and a dedicated rendering worker. Those are separate from this zero-cost demo.
- The frontend can also be built locally with no environment variable; Vite's development proxy continues to route `/api` to localhost.

# Travel Film Director

An open-source, local-first AI-assisted travel video editor. Turn a folder of trip photos and videos into a story-driven edit: import media, describe the trip, generate an editable storyboard, and render a video locally.

> **Zero-cost by default:** no account, subscription, API key, or cloud upload is required. Media stays on the machine running the backend. AI integrations and social-platform discovery are intentionally optional and are not required by the MVP.

## MVP status

- [x] Local media upload and metadata inspection
- [x] Trip brief and editable storyboard generation (deterministic, no paid AI)
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

The first release deliberately uses a predictable storyboard engine rather than pretending to provide AI analysis without a model. The service boundary is ready for optional local models (for example, Ollama) later.

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

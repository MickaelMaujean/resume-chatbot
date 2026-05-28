# Resume Chatbot — Backend

A lightweight FastAPI backend powering an AI chatbot for a personal resume website.
Uses Google Gemini (via AI Studio free tier) with rate limiting to protect your quota from abuse.

---

## Project Structure

```
resume-chatbot/
├── main.py                  # FastAPI app — all backend logic
├── resume_context.md        # Your resume content — edit this first
├── pyproject.toml           # Project metadata & dependencies (uv)
├── .env.example             # Environment variable template
├── .gitignore
├── railway.toml             # One-click Railway deployment config
└── frontend_integration.js  # Copy-paste snippet for your Lovable frontend
```

---

## Prerequisites

This project uses [**uv**](https://docs.astral.sh/uv/) for package management and virtual environments.
It is significantly faster than pip and handles the venv automatically.

**Install uv** (once, globally):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/you/resume-chatbot.git
cd resume-chatbot
```

### 2. Create the virtual environment and install dependencies

```bash
uv sync
```

That's it. `uv sync` reads `pyproject.toml`, creates a `.venv` folder, and installs all dependencies in one shot. No manual `venv` creation or `pip install` needed.

To also install dev dependencies (testing tools):

```bash
uv sync --extra dev
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then open `.env` and fill in your values:

```env
GEMINI_API_KEY=your_google_ai_studio_key_here
FRONTEND_URL=https://your-lovable-site.com
```

### 4. Edit your resume context

Open `resume_context.md` and replace the placeholder content with your real information.
This file is injected as the AI's system prompt — the more detail you add, the better it answers.

### 5. Run the development server

```bash
uv run uvicorn main:app --reload
```

| Endpoint | URL |
|---|---|
| API base | http://localhost:8000 |
| Interactive docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## Common uv Commands

| Task | Command |
|---|---|
| Install / sync all deps | `uv sync` |
| Add a new dependency | `uv add package-name` |
| Remove a dependency | `uv remove package-name` |
| Run any command in the venv | `uv run <command>` |
| Upgrade all dependencies | `uv sync --upgrade` |
| Show installed packages | `uv pip list` |

> You never need to manually activate the venv — `uv run` handles it automatically.

---

## Rate Limiting & Abuse Protection

Google AI Studio does **not** offer per-user or per-key usage caps — limits are per project and only visible to you.
All protection is therefore implemented in this backend via **slowapi**, with multiple layers:

| Layer | Limit | Purpose |
|---|---|---|
| Requests per minute (per IP) | 10 | Block burst abuse |
| Requests per day (per IP) | 100 | Protect your free Gemini quota |
| Max message length | 1 000 chars | Prevent oversized inputs |
| Max conversation history | 20 messages | Cap context window size |
| Max output tokens | 300 | Keep replies short and cheap |
| CORS | Your domain only | Block requests from unknown origins |

When a limit is hit, the API returns `429 Too Many Requests`. The frontend integration snippet handles this with a user-friendly error message.

---

## Deploy to Railway

Railway reads `railway.toml` automatically — no extra configuration needed in the UI.

1. Push this repo to a GitHub repository
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your repo
4. Under **Variables**, add:
   - `GEMINI_API_KEY` → your AI Studio key
   - `FRONTEND_URL` → your Lovable site URL (e.g. `https://yourname.lovable.app`)
5. Railway builds and deploys automatically, then gives you a public URL like `https://resume-chatbot-production.up.railway.app`
6. Copy that URL into `frontend_integration.js` as `BACKEND_URL`

> Railway's free tier is sufficient for a personal resume chatbot with low traffic.

---

## Frontend Integration

See `frontend_integration.js` for a ready-to-use `sendMessage()` function and a commented React component example.

The only value you need to change is `BACKEND_URL` at the top of that file:

```js
const BACKEND_URL = "https://your-backend.railway.app";
```

The function maintains conversation history automatically in memory for the duration of the browser session.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Your Google AI Studio API key |
| `FRONTEND_URL` | ✅ | Full URL of your frontend (used for CORS) |

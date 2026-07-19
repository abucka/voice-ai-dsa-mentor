# Voice AI DSA Mentor

Learning DSA is difficult because explanations are generic and learners often don't know why their solution is wrong.
Voice AI DSA Mentor is an AI tutor that helps users learn data structures and algorithms through interactive coding, personalized explanations, and voice conversations.

## What is included

- apps/web: React + Vite frontend for chat and voice UX
- apps/backend: Python + FastAPI backend for orchestration and AI hooks
- CI workflow for lint, type-check, and build

## Run locally

### Prerequisites

- Node.js 18+
- npm 9+
- Python 3.13+

### 1. Install dependencies

From the repo root:

```bash
npm install
```

Create and activate a virtual environment for the backend, then install Python packages:

```bash
/usr/local/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
```

If `python3.13` is already on your `PATH`, you can use `python3.13 -m venv .venv` instead.

### 2. Optional environment file

An `.env.example` file is included in the repo root:

```bash
cp .env.example .env
```

The current starter app can run without extra configuration, but this file is useful for upcoming AI integration settings such as `OPENAI_API_KEY` and `VITE_API_BASE_URL`.

### 3. Start the project

Run both backend and frontend together from the repo root:

```bash
npm run dev
```

The root dev script uses `scripts/dev-backend.sh`, which prefers `.venv/bin/python` automatically, so you do not need to activate the virtual environment before starting the app once `.venv` has been created.

This starts:

- FastAPI backend at `http://localhost:4000`
- Vite frontend at `http://localhost:5173`

### 4. Verify it is running

Open the frontend in your browser:

```text
http://localhost:5173
```

Check the backend health endpoint:

```text
http://localhost:4000/health
```

You should get a response similar to:

```json
{"ok":true,"service":"voice-ai-dsa-mentor-api"}
```

### 5. Run services separately

If you want to run each app in its own terminal:

Backend:

```bash
npm run dev:backend
```

Frontend:

```bash
npm run dev:web
```

### 6. Build the frontend

```bash
npm run build
```

### 7. Useful commands

```bash
npm run typecheck
npm run lint
```

## Suggested roadmap

1. Add speech-to-text input streaming in web
2. Add text-to-speech responses from server
3. Add interview and DSA prompt templates
4. Add coding challenge evaluator
5. Add session persistence and analytics

## Environment variables

The repo includes [.env.example](/Users/aleksandrabucka/OneDrive/projects/voice-ai-dsa-mentor/.env.example).

Defined there today:

- `PORT=4000`
- `OPENAI_API_KEY=your_api_key_here`
- `OPENAI_MODEL=gpt-4.1-mini`
- `VITE_API_BASE_URL=http://localhost:4000`

At the moment, the local dev scripts already start the backend on port `4000`, and the starter UI does not yet require an API key to render.

## Backend dependency notes

The backend dependency versions currently used for local startup are:

- `fastapi==0.116.1`
- `uvicorn==0.33.0`
- `pydantic==2.10.6`

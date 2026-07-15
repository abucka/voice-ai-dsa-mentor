# Voice AI DSA Mentor

A starter repository for a voice-enabled DSA coaching assistant.

## What is included

- apps/web: React + Vite frontend for chat and voice UX
- apps/backend: Python + FastAPI backend for orchestration and AI hooks
- CI workflow for lint, type-check, and build

## Quick start

## Run locally

### Prerequisites

- Node.js 18+
- npm 9+
- Python 3.11+

### 1. Install dependencies

From the repo root:

```bash
npm install
```

Create and activate a virtual environment for the backend, then install Python packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
```

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
source .venv/bin/activate
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

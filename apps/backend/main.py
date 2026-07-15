from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


MentorMode = Literal["explain", "interview", "hints-only"]


class SessionStartRequest(BaseModel):
    mode: MentorMode
    topic: str = Field(min_length=2)


class SessionStartResponse(BaseModel):
    sessionId: str
    startedAt: str
    mode: MentorMode
    topic: str


app = FastAPI(title="Voice AI DSA Mentor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "voice-ai-dsa-mentor-api"}


@app.post("/api/session/start", response_model=SessionStartResponse, status_code=201)
def start_session(payload: SessionStartRequest) -> SessionStartResponse:
    return SessionStartResponse(
        sessionId=str(uuid4()),
        startedAt=datetime.now(timezone.utc).isoformat(),
        mode=payload.mode,
        topic=payload.topic,
    )
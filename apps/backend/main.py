from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


MentorMode = Literal["explain", "interview", "hints-only"]
ProblemId = Literal[
    "two-sum",
    "valid-parentheses",
    "longest-substring-no-repeat",
    "merge-k-sorted-lists",
]
DEFAULT_PROBLEM_ID: ProblemId = "two-sum"

# In-memory storage for starter auth/progress flow.
user_last_problem: dict[str, ProblemId] = {}
token_to_email: dict[str, str] = {}


class SessionStartRequest(BaseModel):
    mode: MentorMode
    topic: str = Field(min_length=2)


class SessionStartResponse(BaseModel):
    sessionId: str
    startedAt: str
    mode: MentorMode
    topic: str


class SignInRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=1)


class SignInResponse(BaseModel):
    token: str
    email: str
    lastProblemId: ProblemId


class LastProblemResponse(BaseModel):
    email: str
    lastProblemId: ProblemId


class LastProblemUpdateRequest(BaseModel):
    problemId: ProblemId


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


def require_authenticated_email(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

    token = authorization[7:].strip()
    email = token_to_email.get(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return email


@app.post("/api/session/start", response_model=SessionStartResponse, status_code=201)
def start_session(payload: SessionStartRequest) -> SessionStartResponse:
    return SessionStartResponse(
        sessionId=str(uuid4()),
        startedAt=datetime.now(timezone.utc).isoformat(),
        mode=payload.mode,
        topic=payload.topic,
    )


@app.post("/api/auth/signin", response_model=SignInResponse, status_code=200)
def sign_in(payload: SignInRequest) -> SignInResponse:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address")

    if email not in user_last_problem:
        user_last_problem[email] = DEFAULT_PROBLEM_ID

    token = str(uuid4())
    token_to_email[token] = email

    return SignInResponse(token=token, email=email, lastProblemId=user_last_problem[email])


@app.get("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def get_last_problem(authorization: str | None = Header(default=None)) -> LastProblemResponse:
    email = require_authenticated_email(authorization)
    return LastProblemResponse(email=email, lastProblemId=user_last_problem.get(email, DEFAULT_PROBLEM_ID))


@app.patch("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def update_last_problem(
    payload: LastProblemUpdateRequest,
    authorization: str | None = Header(default=None),
) -> LastProblemResponse:
    email = require_authenticated_email(authorization)
    user_last_problem[email] = payload.problemId
    return LastProblemResponse(email=email, lastProblemId=user_last_problem[email])
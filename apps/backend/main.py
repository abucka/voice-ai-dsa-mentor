from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .ai_services import call_elevenlabs_tts, call_openai_tutor, transcribe_audio_with_openai
from .execution import evaluate_submission, execute_code
from .models import (
    DEFAULT_PROBLEM_ID,
    HelpCodeRequest,
    HelpCodeResponse,
    LastProblemResponse,
    LastProblemUpdateRequest,
    RunCodeRequest,
    RunCodeResponse,
    SessionStartRequest,
    SessionStartResponse,
    SignInRequest,
    SignInResponse,
    SubmitCodeRequest,
    SubmitCodeResponse,
    TranscribeAudioRequest,
    TranscribeAudioResponse,
    ProblemId
)
from .problem_data import SUBMISSION_TESTS

load_dotenv()

user_last_problem: dict[str, ProblemId] = {}
token_to_email: dict[str, str] = {}

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

@app.post("/api/code/run", response_model=RunCodeResponse, status_code=200)
def run_code(payload: RunCodeRequest) -> RunCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")

    stdin_text, _ = tests[0]
    return execute_code(payload.problemId, payload.language, payload.code, stdin_text)

@app.post("/api/code/submit", response_model=SubmitCodeResponse, status_code=200)
def submit_code(payload: SubmitCodeRequest) -> SubmitCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")

    results, passed_tests, total_tests = evaluate_submission(payload.problemId, payload.code)
    return SubmitCodeResponse(
        problemId=payload.problemId,
        language=payload.language,
    passed=passed_tests == total_tests,
    passedTests=passed_tests,
    totalTests=total_tests,
        note=None if passed_tests == total_tests else "One or more sample tests failed",
        results=results,
    )

@app.post("/api/help", response_model=HelpCodeResponse, status_code=200)
def help_code(payload: HelpCodeRequest) -> HelpCodeResponse:
    answer = call_openai_tutor(payload.problemId, payload.question, payload.code, payload.mode)
    audio_base64, audio_mime_type, voice_used = call_elevenlabs_tts(answer)

    return HelpCodeResponse(
    problemId=payload.problemId,
    answer=answer,
    audioBase64=audio_base64,
        audioMimeType=audio_mime_type,
        voiceUsed=voice_used,
    )

@app.post("/api/help/transcribe", response_model=TranscribeAudioResponse, status_code=200)
def transcribe_audio(payload: TranscribeAudioRequest) -> TranscribeAudioResponse:
    text = transcribe_audio_with_openai(payload.audioBase64, payload.mimeType)
    return TranscribeAudioResponse(text=text)
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .ai_services import call_elevenlabs_tts, call_openai_tutor, transcribe_audio_with_openai
from .database import Base, engine, get_db
from .db_models import AuthToken, User
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
from .security import hash_password, verify_password

load_dotenv()

app = FastAPI(title="Voice AI DSA Mentor API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "voice-ai-dsa-mentor-api"}

def require_authenticated_user(authorization: str | None, db: Session) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

    token = authorization[7:].strip()
    auth_token = db.get(AuthToken, token)
    if not auth_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, auth_token.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user

@app.post("/api/session/start", response_model=SessionStartResponse, status_code=201)
def start_session(payload: SessionStartRequest) -> SessionStartResponse:
    return SessionStartResponse(
    sessionId=str(uuid4()),
    startedAt=datetime.now(timezone.utc).isoformat(),
    mode=payload.mode,
        topic=payload.topic,
    )

@app.post("/api/auth/signin", response_model=SignInResponse, status_code=200)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)) -> SignInResponse:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            last_problem_id=DEFAULT_PROBLEM_ID,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = str(uuid4())
    db.add(AuthToken(token=token, user_id=user.id))
    db.commit()

    return SignInResponse(token=token, email=user.email, lastProblemId=ProblemId(user.last_problem_id))

@app.get("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def get_last_problem(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> LastProblemResponse:
    user = require_authenticated_user(authorization, db)
    return LastProblemResponse(email=user.email, lastProblemId=ProblemId(user.last_problem_id))

@app.patch("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def update_last_problem(
    payload: LastProblemUpdateRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> LastProblemResponse:
    user = require_authenticated_user(authorization, db)
    user.last_problem_id = payload.problemId
    db.commit()
    return LastProblemResponse(email=user.email, lastProblemId=ProblemId(user.last_problem_id))

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
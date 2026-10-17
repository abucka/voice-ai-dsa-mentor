import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .ai_services import call_elevenlabs_tts, call_openai_tutor, transcribe_audio_with_openai
from .database import Base, engine, get_db
from .db_models import AuthToken, User, SolvedProblems
from .execution import evaluate_submission, execute_code
from .models import (
    DEFAULT_PROBLEM_ID,
    HelpCodeRequest,
    HelpCodeResponse,
    LastProblemResponse,
    LastProblemUpdateRequest,
    RunCodeRequest,
    RunCodeResponse,
    SignInRequest,
    SignInResponse,
    SubmitCodeRequest,
    SubmitCodeResponse,
    TranscribeAudioRequest,
    TranscribeAudioResponse,
    ProblemId,
    ProblemSolution
)
from .problem_data import SUBMISSION_TESTS, update_problem_solution
from .security import hash_password, require_authenticated_user, verify_password, check_signin_rate_limit

load_dotenv()

def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

app = FastAPI(title="Voice AI DSA Mentor API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "voice-ai-dsa-mentor-api"}

#### SECURITY ENDPOINTS
@app.post("/api/auth/signin", response_model=SignInResponse, status_code=200)
def sign_in(payload: SignInRequest, db: Session = Depends(get_db)) -> SignInResponse:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address")

    check_signin_rate_limit(email)

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

@app.delete("/api/auth/signout", status_code=204)
def sign_out(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        auth_token = db.get(AuthToken, token)
        if auth_token:
            db.delete(auth_token)
            db.commit()
    return None

@app.get("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def get_last_problem(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> LastProblemResponse:
    user = require_authenticated_user(authorization, db)
    return LastProblemResponse(email=user.email, lastProblemId=ProblemId(user.last_problem_id))

#@app.patch("/problems/{problem_id}")
#def update_problem(problem_id: int):
#    _update_problem_solution(db, payload.problemId, payload.code)
#    return {"message": "Updated successfully"}

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


#### SOLVE PROBLEMS ENDPOINTS
@app.post("/api/code/run", response_model=RunCodeResponse, status_code=200)
def run_code(payload: RunCodeRequest) -> RunCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")

    return execute_code(payload.problemId, payload.language, payload.code, tests[0])

@app.post("/api/code/submit", response_model=SubmitCodeResponse, status_code=200)
def submit_code(payload: SubmitCodeRequest, db: Session = Depends(get_db)) -> SubmitCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")

    update_problem_solution(db, payload.problemId, payload.code)

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

@app.get("/api/problems/{problem_id}/solution", response_model=ProblemSolution, status_code=200)
def get_last_problem(
    problem_id: ProblemId,
    db: Session = Depends(get_db),
) -> str:
    problem = db.get(SolvedProblems, problem_id)
    if not problem:
        return ProblemSolution(solution="")
    return ProblemSolution(solution=problem.solution)

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
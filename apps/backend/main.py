from datetime import datetime, timezone
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal
from uuid import uuid4
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import quote
from dotenv import load_dotenv

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

MentorMode = Literal["explain", "interview", "hints-only"]
CodeLanguage = Literal["python"]
HelpTone = Literal["hint", "explain", "encourage"]
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


class RunCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)


class RunCodeResponse(BaseModel):
    language: CodeLanguage
    stdout: str
    stderr: str
    exitCode: int
    timedOut: bool


class SubmitCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)


class SubmitTestResult(BaseModel):
    input: str
    expectedOutput: str
    actualOutput: str
    passed: bool
    exitCode: int
    timedOut: bool
    stderr: str
    reason: str | None = None


class SubmitCodeResponse(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    passed: bool
    passedTests: int
    totalTests: int
    note: str | None = None
    results: list[SubmitTestResult]


class HelpRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    question: str = Field(min_length=3)
    code: str = Field(min_length=1)
    mode: MentorMode


class HelpResponse(BaseModel):
    problemId: ProblemId
    answer: str
    audioBase64: str | None = None
    audioMimeType: str | None = None
    voiceUsed: str | None = None


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


SUBMISSION_TESTS: dict[ProblemId, list[tuple[str, str]]] = {
    "two-sum": [
        ("4 9\n2 7 11 15\n", "0 1\n"),
        ("3 6\n3 2 4\n", "1 2\n"),
    ],
    "valid-parentheses": [
        ("([{}])\n", "true\n"),
        ("([)]\n", "false\n"),
    ],
    "longest-substring-no-repeat": [
        ("abcabcbb\n", "3\n"),
        ("bbbbb\n", "1\n"),
    ],
    "merge-k-sorted-lists": [
        ("3\n1 4 5\n1 3 4\n2 6\n", "1 1 2 3 4 4 5 6\n"),
        ("2\n1 2\n3 4\n", "1 2 3 4\n"),
    ],
}


def normalize_output(value: str) -> str:
    return value.strip()


def get_problem_summary(problem_id: ProblemId) -> str:
    if problem_id == "two-sum":
        return "Find two indices whose values add up to a target in linear time."
    if problem_id == "valid-parentheses":
        return "Validate bracket order using stack pushes and pops."
    if problem_id == "longest-substring-no-repeat":
        return "Use a sliding window to find the longest substring with unique characters."
    return "Merge multiple sorted linked lists efficiently."


def call_openai_tutor(problem_id: ProblemId, question: str, code: str, mode: MentorMode) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    system_prompt = (
        "You are a concise DSA tutor. Help the learner solve the problem without giving away the full solution. "
        "Focus on debugging hints, algorithm direction, and why their current code may fail. "
        "Keep the answer under 180 words and avoid code unless it is a tiny illustrative snippet."
    )
    user_prompt = (
        f"Problem: {problem_id}\n"
        f"Summary: {get_problem_summary(problem_id)}\n"
        f"Mentor mode: {mode}\n"
        f"Learner question: {question}\n"
        f"Current code:\n{code}\n"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }

    request = urllib_request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {exc.read().decode('utf-8', errors='ignore')}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {exc.reason}") from exc

    choices = response_payload.get("choices", [])
    if not choices:
        raise HTTPException(status_code=500, detail="OpenAI returned no tutor answer")

    return choices[0]["message"]["content"].strip()


def call_elevenlabs_tts(answer: str) -> tuple[str | None, str | None, str | None]:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        return None, None, None

    payload = {
        "text": answer,
        "model_id": os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.2,
            "use_speaker_boost": True,
        },
    }

    request = urllib_request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{quote(voice_id)}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            audio_bytes = response.read()
    except urllib_error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"ElevenLabs request failed: {exc.read().decode('utf-8', errors='ignore')}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"ElevenLabs request failed: {exc.reason}") from exc

    return base64.b64encode(audio_bytes).decode("utf-8"), "audio/mpeg", voice_id


class HelpCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)
    question: str = Field(min_length=3)
    mode: MentorMode


class HelpCodeResponse(BaseModel):
    problemId: ProblemId
    answer: str


def build_python_harness(problem_id: ProblemId) -> str:
    if problem_id == "two-sum":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

parts = sys.stdin.readline().strip().split()
n = int(parts[0])
target = int(parts[1])
nums = list(map(int, sys.stdin.readline().strip().split()))[:n]
result = solve(nums, target)

if isinstance(result, (list, tuple)):
    print(" ".join(str(x) for x in result))
else:
    print(result)
"""

    if problem_id == "valid-parentheses":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

s = sys.stdin.readline().rstrip("\n")
result = solve(s)
print("true" if bool(result) else "false")
"""

    if problem_id == "longest-substring-no-repeat":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

s = sys.stdin.readline().rstrip("\n")
result = solve(s)
print(result)
"""

    return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

k = int(sys.stdin.readline().strip())
lists = []
for _ in range(k):
    line = sys.stdin.readline().strip()
    lists.append(list(map(int, line.split())) if line else [])

result = solve(lists)
if isinstance(result, (list, tuple)):
    print(" ".join(str(x) for x in result))
else:
    print(result)
"""


def execute_python_code(problem_id: ProblemId, code: str, stdin_text: str) -> RunCodeResponse:
    timeout_seconds = 5

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        code_file = temp_dir / "main.py"
        wrapped_code = f"{code}\n\n{build_python_harness(problem_id)}"
        code_file.write_text(wrapped_code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, str(code_file)],
                cwd=temp_dir,
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            return RunCodeResponse(
                language="python",
                stdout=error.stdout or "",
                stderr=error.stderr or "Timed out while running Python code",
                exitCode=124,
                timedOut=True,
            )

        return RunCodeResponse(
            language="python",
            stdout=completed.stdout,
            stderr=completed.stderr,
            exitCode=completed.returncode,
            timedOut=False,
        )


def execute_code(problem_id: ProblemId, language: CodeLanguage, code: str, stdin_text: str) -> RunCodeResponse:
    return execute_python_code(problem_id, code, stdin_text)


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

    # Run uses the first sample test as quick feedback.
    stdin_text, _ = tests[0]
    return execute_code(payload.problemId, payload.language, payload.code, stdin_text)


@app.post("/api/code/submit", response_model=SubmitCodeResponse, status_code=200)
def submit_code(payload: SubmitCodeRequest) -> SubmitCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    total_tests = len(tests)
    results: list[SubmitTestResult] = []

    passed_tests = 0
    for test_input, expected_output in tests:
        execution_result = execute_python_code(payload.problemId, payload.code, test_input)
        actual_output = execution_result.stdout
        passed = (
            not execution_result.timedOut
            and execution_result.exitCode == 0
            and normalize_output(actual_output) == normalize_output(expected_output)
        )
        if passed:
            passed_tests += 1

        results.append(
            SubmitTestResult(
                input=test_input,
                expectedOutput=expected_output,
                actualOutput=actual_output,
                passed=passed,
                exitCode=execution_result.exitCode,
                timedOut=execution_result.timedOut,
                stderr=execution_result.stderr,
                reason=None if passed else "Output mismatch" if not execution_result.stderr else "Runtime error",
            )
        )

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
    #audio_base64, audio_mime_type, voice_used = call_elevenlabs_tts(answer)

    return HelpCodeResponse(
        problemId=payload.problemId,
        answer=answer,
    )
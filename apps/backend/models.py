from typing import Literal, NewType

from pydantic import BaseModel, Field

MentorMode = Literal["explain", "interview", "hints-only"]
CodeLanguage = Literal["python"]
ProblemId = NewType('ProblemId', int)
DEFAULT_PROBLEM_ID: ProblemId = 0


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

class ProblemSolution(BaseModel):
    solution: str
    is_solved: bool

class LastProblemUpdateRequest(BaseModel):
    problemId: ProblemId


class RunCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)


class RunCodeResponse(BaseModel):
    language: CodeLanguage
    input: str
    expectedOutput: str
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


class HelpCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)
    question: str = Field(min_length=3)
    mode: MentorMode


class HelpCodeResponse(BaseModel):
    problemId: ProblemId
    answer: str
    audioBase64: str | None = None
    audioMimeType: str | None = None
    voiceUsed: str | None = None


class TranscribeAudioRequest(BaseModel):
    audioBase64: str = Field(min_length=1)
    mimeType: str = Field(min_length=1)


class TranscribeAudioResponse(BaseModel):
    text: str

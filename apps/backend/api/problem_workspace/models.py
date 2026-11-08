from pydantic import BaseModel, Field

from ...models import CodeLanguage, ProblemId

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


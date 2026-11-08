from pydantic import BaseModel, Field

from ...models import CodeLanguage, ProblemId

class HelpCodeRequest(BaseModel):
    problemId: ProblemId
    language: CodeLanguage
    code: str = Field(min_length=1)
    question: str = Field(min_length=3)

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

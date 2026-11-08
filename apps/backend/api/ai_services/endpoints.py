from fastapi import APIRouter
from .models import HelpCodeResponse, HelpCodeRequest, TranscribeAudioResponse, TranscribeAudioRequest
from .ai_services import call_openai_tutor, transcribe_audio_with_openai

router = APIRouter()

@router.post("/api/help", response_model=HelpCodeResponse, status_code=200)
def help_code(payload: HelpCodeRequest) -> HelpCodeResponse:
    answer = call_openai_tutor(payload.problemId, payload.question, payload.code)
    #audio_base64, audio_mime_type, voice_used = call_elevenlabs_tts(answer)

    return HelpCodeResponse(
        problemId=payload.problemId,
        answer=answer,
        audioBase64=None,
        audioMimeType=None,
        voiceUsed=None,
    )

@router.post("/api/help/transcribe", response_model=TranscribeAudioResponse, status_code=200)
def transcribe_audio(payload: TranscribeAudioRequest) -> TranscribeAudioResponse:
    text = transcribe_audio_with_openai(payload.audioBase64, payload.mimeType)
    return TranscribeAudioResponse(text=text)
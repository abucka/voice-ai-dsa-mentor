from fastapi import APIRouter
from .models import HelpCodeResponse, HelpCodeRequest, TranscribeAudioResponse, TranscribeAudioRequest, SynthesizeAudioRequest, SynthesizeAudioResponse
from .ai_services import call_openai_tutor, transcribe_audio_with_openai, call_elevenlabs_tts

router = APIRouter()

@router.post("/api/help", response_model=HelpCodeResponse, status_code=200)
def help_code(payload: HelpCodeRequest) -> HelpCodeResponse:
    answer = call_openai_tutor(payload.problemId, payload.question, payload.code)
    return HelpCodeResponse(
        problemId=payload.problemId,
        answer=answer,
    )

@router.post("/api/help/transcribe", response_model=TranscribeAudioResponse, status_code=200)
def transcribe_audio(payload: TranscribeAudioRequest) -> TranscribeAudioResponse:
    text = transcribe_audio_with_openai(payload.audioBase64, payload.mimeType)
    return TranscribeAudioResponse(text=text)


@router.post("/api/help/synthesize", response_model=SynthesizeAudioResponse, status_code=200)
def help_code(payload: SynthesizeAudioRequest) -> SynthesizeAudioResponse:
    audio_base64, audio_mime_type = call_elevenlabs_tts(payload.text)

    return SynthesizeAudioResponse(
        audioBase64=audio_base64,
        audioMimeType=audio_mime_type,
    )
import base64
import io
import os

from fastapi import HTTPException
from openai import OpenAI

from elevenlabs.client import ElevenLabs

from ...models import ProblemId
from ..problem_workspace.problem_data import get_problem_summary

SYSTEM_TUTOR_PROMPT = (
    "You are a concise DSA tutor. Help the learner solve the problem without giving away the full solution. "
    "Focus on debugging hints, algorithm direction, and why their current code may fail. "
    "Keep the answer under 180 words and avoid code unless it is a tiny illustrative snippet."
)

def call_openai_tutor(problem_id: ProblemId, question: str, code: str, mentor_mode: str = "explain") -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)
    user_prompt = (
        f"Problem: {problem_id}\n"
        f"Summary: {get_problem_summary(problem_id)}\n"
        f"Mentor mode: {mentor_mode}\n"
        f"Learner question: {question}\n"
        f"Current code:\n{code}\n"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_TUTOR_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {exc}") from exc

    choices = getattr(response, "choices", None) or []
    if not choices:
        raise HTTPException(status_code=500, detail="OpenAI returned no tutor answer")

    content = getattr(choices[0].message, "content", None)
    if not content:
        raise HTTPException(status_code=500, detail="OpenAI returned an empty tutor answer")

    return content.strip()


def call_elevenlabs_tts(text: str) -> tuple[str | None, str | None, str | None]:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    

    if not api_key or not voice_id:
        return None, None, None

    try:
        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
            text=text,
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(chunk for chunk in audio)
        return base64.b64encode(audio_bytes).decode("utf-8"), "audio/mpeg"
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ElevenLabs request failed: {exc}") from exc


def transcribe_audio_with_openai(audio_base64: str, mime_type: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    audio_bytes = base64.b64decode(audio_base64)
    filename = "voice-recording.webm"
    if "mp4" in mime_type:
        filename = "voice-recording.mp4"
    elif "ogg" in mime_type:
        filename = "voice-recording.ogg"

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    try:
        response = OpenAI(api_key=api_key).audio.transcriptions.create(
            file=(filename, audio_file.read(), mime_type),
            model=model,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI transcription failed: {exc}") from exc

    text = getattr(response, "text", "").strip()
    if not text:
        raise HTTPException(status_code=500, detail="OpenAI returned no transcription")

    return text

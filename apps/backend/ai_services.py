import base64
import json
import os
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import quote
from uuid import uuid4

from fastapi import HTTPException

from .models import MentorMode, ProblemId
from .problem_data import get_problem_summary


def _fallback_tutor_response(problem_id: ProblemId, question: str, code: str, conversation_history: list[dict[str, str]] | None, mode: MentorMode) -> str:
    history_context = ""
    if conversation_history:
        recent_turns = []
        for item in conversation_history[-4:]:
            recent_turns.append(f"{item['role'].title()}: {item['content']}")
        history_context = "\n".join(recent_turns)

    if history_context:
        return (
            f"I’m keeping this conversation going. Based on the earlier exchange ({history_context}), "
            f"you’re asking about {question}. Focus on the core invariant for this problem, "
            f"and try a small example to verify your reasoning before you change the code."
        )

    return (
        f"I can help you work through this {mode} style. Your question was: {question}. "
        "Start by identifying the smallest example that should pass and the edge case that might fail, "
        "then adjust your code around that invariant."
    )

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
ELEVENLABS_TTS_URL_TEMPLATE = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
SYSTEM_TUTOR_PROMPT = (
    "You are a concise DSA tutor. Help the learner solve the problem without giving away the full solution. "
    "Focus on debugging hints, algorithm direction, and why their current code may fail. "
    "Keep the answer under 180 words and avoid code unless it is a tiny illustrative snippet."
)


def build_request(url: str, body: bytes | None, headers: dict[str, str], method: str = "POST") -> urllib_request.Request:
    return urllib_request.Request(url, data=body, headers=headers, method=method)


def read_json_response(response: object) -> dict[str, object]:
    return json.loads(response.read().decode("utf-8"))


def call_openai_tutor(
    problem_id: ProblemId,
    question: str,
    code: str,
    mode: MentorMode,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    user_prompt = (
        f"Problem: {problem_id}\n"
        f"Summary: {get_problem_summary(problem_id)}\n"
        f"Mentor mode: {mode}\n"
        f"Learner question: {question}\n"
        f"Current code:\n{code}\n"
    )

    messages = [{"role": "system", "content": SYSTEM_TUTOR_PROMPT}]
    if conversation_history:
        for entry in conversation_history[-8:]:
            messages.append({"role": entry["role"], "content": entry["content"]})

    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }

    request = build_request(
        OPENAI_CHAT_COMPLETIONS_URL,
        json.dumps(payload).encode("utf-8"),
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            response_payload = read_json_response(response)
    except urllib_error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {exc.read().decode('utf-8', errors='ignore')}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {exc.reason}") from exc

    choices = response_payload.get("choices", [])
    if not choices:
        raise HTTPException(status_code=500, detail="OpenAI returned no tutor answer")

    return choices[0]["message"]["content"].strip()


def get_tutor_reply(
    problem_id: ProblemId,
    question: str,
    code: str,
    conversation_history: list[dict[str, str]] | None,
    mode: MentorMode,
) -> str:
    try:
        return call_openai_tutor(problem_id, question, code, mode, conversation_history)
    except HTTPException as exc:
        if exc.status_code == 500 and "OPENAI_API_KEY" in str(exc.detail):
            return _fallback_tutor_response(problem_id, question, code, conversation_history, mode)
        if exc.status_code == 500:
            return _fallback_tutor_response(problem_id, question, code, conversation_history, mode)
        raise
    except Exception:
        return _fallback_tutor_response(problem_id, question, code, conversation_history, mode)


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

    request = build_request(
        ELEVENLABS_TTS_URL_TEMPLATE.format(voice_id=quote(voice_id)),
        json.dumps(payload).encode("utf-8"),
        {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )

    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            audio_bytes = response.read()
    except urllib_error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"ElevenLabs request failed: {exc.read().decode('utf-8', errors='ignore')}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"ElevenLabs request failed: {exc.reason}") from exc

    return base64.b64encode(audio_bytes).decode("utf-8"), "audio/mpeg", voice_id


def transcribe_audio_with_openai(audio_base64: str, mime_type: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    audio_bytes = base64.b64decode(audio_base64)
    boundary = f"----voice-ai-boundary-{uuid4().hex}"
    filename = "voice-recording.webm"
    if "mp4" in mime_type:
        filename = "voice-recording.mp4"
    elif "ogg" in mime_type:
        filename = "voice-recording.ogg"

    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="model"\r\n\r\n{model}\r\n'.encode("utf-8"),
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            audio_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )

    request = build_request(
        OPENAI_TRANSCRIPTIONS_URL,
        body,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    try:
        with urllib_request.urlopen(request, timeout=60) as response:
            response_payload = read_json_response(response)
    except urllib_error.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI transcription failed: {exc.read().decode('utf-8', errors='ignore')}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI transcription failed: {exc.reason}") from exc

    text = response_payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=500, detail="OpenAI returned no transcription")

    return text

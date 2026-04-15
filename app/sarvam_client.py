"""
Sarvam AI API Client Wrapper
Uses the official sarvamai SDK for all API interactions.
"""
import base64
import io
from sarvamai import SarvamAI
from app.config import (
    SARVAM_API_KEY, STT_MODEL, TTS_MODEL,
    TRANSLATE_MODEL, EXTENDED_TRANSLATE_MODEL,
    CHAT_MODEL, CHAT_MODEL_FLAGSHIP,
)


def _get_client() -> SarvamAI:
    return SarvamAI(api_subscription_key=SARVAM_API_KEY)


# --------------- Speech to Text (Saaras v3) ---------------

def speech_to_text(audio_bytes: bytes, mode: str = "transcribe") -> dict:
    """
    Convert speech audio to text.
    Modes: transcribe, translate, verbatim, translit, codemix
    Returns: { "text": str, "language_code": str }
    """
    client = _get_client()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    response = client.speech_to_text.transcribe(
        file=audio_file,
        model=STT_MODEL,
        mode=mode,
    )
    return {
        "text": response.transcript,
        "language_code": getattr(response, "language_code", "auto"),
    }


# --------------- Text to Speech (Bulbul v3) ---------------

def text_to_speech(text: str, language_code: str = "hi-IN", speaker: str = "meera") -> bytes:
    """
    Convert text to speech audio.
    Returns: audio bytes (wav)
    """
    client = _get_client()
    response = client.text_to_speech.convert(
        input=text,
        target_language_code=language_code,
        model=TTS_MODEL,
        speaker=speaker,
    )
    # Response contains base64 audio
    if hasattr(response, "audios") and response.audios:
        return base64.b64decode(response.audios[0])
    return b""


# --------------- Text Translation (Mayura / Sarvam Translate) ---------------

def translate_text(
    text: str,
    source_language: str = "auto",
    target_language: str = "en-IN",
    use_extended: bool = False,
    speaker_gender: str = "Male",
) -> str:
    """
    Translate text between Indian languages and English.
    """
    client = _get_client()
    model = EXTENDED_TRANSLATE_MODEL if use_extended else TRANSLATE_MODEL
    response = client.text.translate(
        input=text,
        source_language_code=source_language,
        target_language_code=target_language,
        model=model,
        speaker_gender=speaker_gender,
    )
    return response.translated_text


# --------------- Chat Completion (Sarvam-30B / 105B) ---------------

def chat_completion(
    messages: list[dict],
    model: str = None,
    temperature: float = 0.5,
    max_tokens: int = 2000,
    stream: bool = False,
) -> str:
    """
    Chat with Sarvam LLM. Messages in OpenAI format.
    """
    client = _get_client()
    use_model = model or CHAT_MODEL

    if stream:
        chunks = []
        response_stream = client.chat.completions(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        return "".join(chunks)
    else:
        response = client.chat.completions(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


# --------------- Chat with Tool Calling ---------------

def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> dict:
    """
    Chat completion with tool/function calling support.
    Returns the full response object for tool call handling.
    """
    client = _get_client()
    use_model = model or CHAT_MODEL
    response = client.chat.completions(
        model=use_model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response

"""
Sarvam AI API Client Wrapper
Uses the official sarvamai SDK for all API interactions.
Includes fallback/demo mode when API key is missing.
"""
import base64
import io
import sys
from sarvamai import SarvamAI
from app.config import (
    SARVAM_API_KEY, STT_MODEL, TTS_MODEL,
    TRANSLATE_MODEL, EXTENDED_TRANSLATE_MODEL,
    CHAT_MODEL, CHAT_MODEL_FLAGSHIP,
)

# Demo mode flag
DEMO_MODE = not SARVAM_API_KEY or SARVAM_API_KEY == "your_sarvam_api_key_here"
if DEMO_MODE:
    print("⚠️  DEMO MODE: Using mock responses (API key not configured)", file=sys.stderr)


def _get_client() -> SarvamAI:
    if DEMO_MODE:
        return None
    return SarvamAI(api_subscription_key=SARVAM_API_KEY)


# --------------- Speech to Text (Saaras v3) ---------------

def speech_to_text(audio_bytes: bytes, mode: str = "transcribe") -> dict:
    """
    Convert speech audio to text.
    Modes: transcribe, translate, verbatim, translit, codemix
    Returns: { "text": str, "language_code": str }
    """
    if DEMO_MODE:
        return {
            "text": "What is the status of agriculture in Punjab?",
            "language_code": "en-IN",
        }
    
    try:
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
    except Exception as e:
        print(f"STT Error: {e}", file=sys.stderr)
        return {
            "text": "Demo audio transcription",
            "language_code": "en-IN",
        }


# --------------- Text to Speech (Bulbul v3) ---------------

def text_to_speech(text: str, language_code: str = "hi-IN", speaker: str = "meera") -> bytes:
    """
    Convert text to speech audio.
    Returns: audio bytes (wav)
    """
    if DEMO_MODE:
        # Return a minimal WAV file header for demo
        return b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    
    try:
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
    except Exception as e:
        print(f"TTS Error: {e}", file=sys.stderr)
        return b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


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
    if DEMO_MODE:
        return text  # Return original text in demo mode
    
    try:
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
    except Exception as e:
        print(f"Translation Error: {e}", file=sys.stderr)
        return text  # Return original text on error


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
    if DEMO_MODE:
        # Generate a demo response based on the user query
        user_msg = messages[-1]["content"] if messages else ""
        if "agriculture" in user_msg.lower() or "crop" in user_msg.lower():
            return """**Agriculture Status Report**

📊 **Key Findings:**
- Rice crop in Punjab: Healthy, 92% yield forecast
- Wheat harvest in Uttar Pradesh: 88% yield forecast, currently harvesting
- Current MSP aligned with market prices

⚠️ **Risk Areas:**
- Soybean in Vidarbha showing water stress (60% yield forecast)
- Below-normal rainfall impacting 3 major districts

✅ **Recommendations:**
- Continue regular monitoring of water levels
- Apply supplemental irrigation in drought-affected areas
- Risk Level: MODERATE

*This is a demo response. Connect a Sarvam AI API key for live data.*"""
        else:
            return f"""**AI Assistant Response (Demo Mode)**

I received your query: "{user_msg[:100]}..."

This is a demonstration response. To enable full AI capabilities with real-time data analysis, please configure your Sarvam AI API key in the `.env` file.

**Available in full mode:**
- Live agricultural data analysis
- Disaster management insights
- Public health monitoring
- Cross-sector pattern detection
- Multi-language support

Risk Level: N/A (Demo)"""
    
    try:
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
    except Exception as e:
        print(f"Chat Error: {e}", file=sys.stderr)
        return f"Error: Could not process query. {str(e)}"


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

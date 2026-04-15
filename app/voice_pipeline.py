"""
Voice Q&A Pipeline
Full flow: Speech → STT → Translate → RAG + LLM → Translate back → TTS
"""
from app.sarvam_client import (
    speech_to_text,
    text_to_speech,
    translate_text,
    chat_completion,
)
from app.rag_engine import get_context_string, get_all_sectors_context

SYSTEM_PROMPT = """You are Sanket.AI — an AI-powered Public Intelligence Assistant for Indian government officials.
You provide data-driven insights across agriculture, disaster management, public health, and security/civil unrest.

Your responsibilities:
1. Answer queries using the provided context data from multiple sectors
2. Identify cross-sector patterns (e.g., heavy rainfall → flood risk → waterborne disease, protest → supply disruption → price rise)
3. Provide actionable recommendations with severity levels
4. Flag early warnings when data suggests emerging risks
5. Present information clearly with specific numbers, regions, and timeframes
6. For security/civil unrest events: assess crowd size, escalation potential, affected infrastructure, and public safety impact

Always cite the data sources when available. If the context doesn't contain relevant data, say so clearly.
If you detect a potential emergency (flood, outbreak, crop failure, protest escalation, security threat), highlight it prominently.

Format your response with:
- A brief summary (2-3 sentences)
- Key findings with bullet points
- Recommended actions
- Risk level: LOW / MODERATE / HIGH / CRITICAL (if applicable)
"""


def process_voice_query(audio_bytes: bytes) -> dict:
    """
    Full voice-in, voice-out pipeline.
    Returns: {
        "user_text": str,          # what user said (original language)
        "user_text_english": str,  # translated to English
        "detected_language": str,  # language code
        "response_english": str,   # LLM response in English
        "response_translated": str,# LLM response in user's language
        "response_audio": bytes,   # TTS audio bytes
        "sector": str,             # detected sector
    }
    """
    # Step 1: Speech to Text
    stt_result = speech_to_text(audio_bytes, mode="transcribe")
    user_text = stt_result["text"]
    detected_lang = stt_result["language_code"]

    # Step 2: Translate to English if needed
    if detected_lang and detected_lang != "en-IN":
        user_text_english = translate_text(
            user_text,
            source_language=detected_lang,
            target_language="en-IN",
        )
    else:
        user_text_english = user_text
        detected_lang = "en-IN"

    # Step 3: Get RAG context
    sector = _detect_sector(user_text_english)
    if sector:
        context = get_context_string(user_text_english, sector=sector)
    else:
        # Cross-sector query — get context from all sectors
        all_ctx = get_all_sectors_context(user_text_english)
        context = "\n\n--- AGRICULTURE DATA ---\n" + all_ctx["agriculture"]
        context += "\n\n--- DISASTER DATA ---\n" + all_ctx["disaster"]
        context += "\n\n--- HEALTH DATA ---\n" + all_ctx["health"]
        context += "\n\n--- SECURITY DATA ---\n" + all_ctx.get("security", "No data available")

    # Step 4: LLM reasoning
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context data:\n{context}\n\nUser query: {user_text_english}"},
    ]
    response_english = chat_completion(messages, temperature=0.3, max_tokens=2000)

    # Step 5: Translate response back to user's language
    if detected_lang != "en-IN":
        response_translated = translate_text(
            response_english,
            source_language="en-IN",
            target_language=detected_lang,
        )
    else:
        response_translated = response_english

    # Step 6: Text to Speech
    response_audio = text_to_speech(response_translated, language_code=detected_lang)

    return {
        "user_text": user_text,
        "user_text_english": user_text_english,
        "detected_language": detected_lang,
        "response_english": response_english,
        "response_translated": response_translated,
        "response_audio": response_audio,
        "sector": sector or "cross-sector",
        "emergency_detected": _detect_emergency(user_text_english),
    }


def process_text_query(text: str, language_code: str = "en-IN") -> dict:
    """
    Text-based query pipeline (no audio).
    """
    # Translate to English if needed
    if language_code != "en-IN":
        text_english = translate_text(text, source_language=language_code, target_language="en-IN")
    else:
        text_english = text

    # RAG + LLM
    sector = _detect_sector(text_english)
    if sector:
        context = get_context_string(text_english, sector=sector)
    else:
        all_ctx = get_all_sectors_context(text_english)
        context = "\n\n--- AGRICULTURE DATA ---\n" + all_ctx["agriculture"]
        context += "\n\n--- DISASTER DATA ---\n" + all_ctx["disaster"]
        context += "\n\n--- HEALTH DATA ---\n" + all_ctx["health"]
        context += "\n\n--- SECURITY DATA ---\n" + all_ctx.get("security", "No data available")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context data:\n{context}\n\nUser query: {text_english}"},
    ]
    response_english = chat_completion(messages, temperature=0.3, max_tokens=2000)

    # Translate back
    if language_code != "en-IN":
        response_translated = translate_text(
            response_english,
            source_language="en-IN",
            target_language=language_code,
        )
    else:
        response_translated = response_english

    return {
        "user_text": text,
        "user_text_english": text_english,
        "detected_language": language_code,
        "response_english": response_english,
        "response_translated": response_translated,
        "sector": sector or "cross-sector",
        "emergency_detected": _detect_emergency(text_english),
    }


# Emergency keywords that should trigger SOS/police redirect
_EMERGENCY_KEYWORDS = [
    "help", "help me", "bachao", "sos", "emergency", "danger", "attack",
    "murder", "killing", "bomb", "fire", "kidnap", "abduct", "rape",
    "assault", "robbery", "gun", "shoot", "stabbing", "bleeding", "dying",
    "accident", "trapped", "threat", "save me", "call police", "under attack",
    "madad", "khatra", "khatara", "jaan", "maaro", "police bulao",
    "i am in danger", "mob", "violence", "riot",
]


def _detect_emergency(text: str) -> bool:
    """Detect if user text contains emergency/threat keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _EMERGENCY_KEYWORDS)


def _detect_sector(text: str) -> str | None:
    """Simple keyword-based sector detection."""
    text_lower = text.lower()
    agriculture_kw = ["crop", "harvest", "farm", "agriculture", "soil", "irrigation",
                       "wheat", "rice", "monsoon", "fertilizer", "yield", "kharif", "rabi",
                       "msp", "sowing", "drought"]
    disaster_kw = ["flood", "earthquake", "cyclone", "tsunami", "landslide", "storm",
                    "disaster", "evacuation", "dam", "river", "water level", "rescue",
                    "rainfall", "heavy rain", "warning"]
    health_kw = ["disease", "outbreak", "dengue", "malaria", "cholera", "hospital",
                  "epidemic", "pandemic", "vaccination", "cases", "infection", "health",
                  "mortality", "fever", "patients"]
    security_kw = ["protest", "strike", "bandh", "riot", "unrest", "violence", "mob",
                    "curfew", "section 144", "tension", "communal", "militant", "naxal",
                    "border", "ceasefire", "terrorist", "security", "police", "army",
                    "demonstration", "rally", "blockade", "arson", "clashes"]

    scores = {
        "agriculture": sum(1 for kw in agriculture_kw if kw in text_lower),
        "disaster": sum(1 for kw in disaster_kw if kw in text_lower),
        "health": sum(1 for kw in health_kw if kw in text_lower),
        "security": sum(1 for kw in security_kw if kw in text_lower),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None

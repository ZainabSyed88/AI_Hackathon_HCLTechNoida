"""
Voice Q&A Pipeline
Full flow: Speech → STT → Translate → RAG + LLM → Translate back → TTS
"""
import sys
from app.sarvam_client import (
    speech_to_text,
    text_to_speech,
    translate_text,
    chat_completion,
    DEMO_MODE,
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

LANGUAGE_LABELS = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "od-IN": "Odia",
    "as-IN": "Assamese",
    "ur-IN": "Urdu",
    "mai-IN": "Maithili",
    "sa-IN": "Sanskrit",
    "ne-IN": "Nepali",
    "sd-IN": "Sindhi",
    "ks-IN": "Kashmiri",
    "doi-IN": "Dogri",
    "kok-IN": "Konkani",
    "mni-IN": "Manipuri",
    "sat-IN": "Santali",
    "bo-IN": "Bodo",
}


def _resolve_reply_language(detected_lang: str | None, preferred_language: str | None) -> str:
    """Choose the best language code to use for translation + TTS."""
    if preferred_language and preferred_language not in {"", "auto"}:
        return preferred_language
    if detected_lang and detected_lang not in {"", "auto"}:
        return detected_lang
    return "en-IN"


def _detect_text_language(text: str) -> str:
    """Lightweight script-based detection for text queries when UI uses auto mode."""
    if not text:
        return "en-IN"

    for ch in text:
        code = ord(ch)
        if 0x0980 <= code <= 0x09FF:
            return "bn-IN" if any(0x09E6 <= ord(c) <= 0x09EF or c in "ৰৱ" for c in text) else "as-IN"
        if 0x0900 <= code <= 0x097F:
            lowered = text.lower()
            if any(word in lowered for word in ["nepali", "नेपाल", "छ", "छु"]):
                return "ne-IN"
            if any(word in lowered for word in ["मैथिली", "अछि", "छिऐ"]):
                return "mai-IN"
            return "hi-IN"
        if 0x0B80 <= code <= 0x0BFF:
            return "ta-IN"
        if 0x0C00 <= code <= 0x0C7F:
            return "te-IN" if code <= 0x0C7F and code >= 0x0C00 and any(0x0C00 <= ord(c) <= 0x0C7F for c in text) else "kn-IN"
        if 0x0C80 <= code <= 0x0CFF:
            return "kn-IN"
        if 0x0D00 <= code <= 0x0D7F:
            return "ml-IN"
        if 0x0A00 <= code <= 0x0A7F:
            return "pa-IN"
        if 0x0B00 <= code <= 0x0B7F:
            return "od-IN"
        if 0x0600 <= code <= 0x06FF:
            return "ur-IN"
    return "en-IN"


def process_voice_query(audio_bytes: bytes, preferred_language: str | None = None) -> dict:
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
    try:
        # Step 1: Speech to Text (demo returns immediately)
        stt_result = speech_to_text(audio_bytes, mode="transcribe")
        user_text = stt_result["text"]
        detected_lang = stt_result["language_code"]
        print(f"[STT] User said: {user_text} (language: {detected_lang})", file=sys.stderr)

        reply_language = _resolve_reply_language(detected_lang, preferred_language)

        # Step 2: Translate to English if needed
        if reply_language != "en-IN":
            user_text_english = translate_text(
                user_text,
                source_language=detected_lang if detected_lang not in {"", None} else "auto",
                target_language="en-IN",
            )
        else:
            user_text_english = user_text
            reply_language = "en-IN"

        # Step 3: Get RAG context (SKIP in demo mode for speed)
        sector = _detect_sector(user_text_english)
        if DEMO_MODE:
            # In demo mode, use minimal context to avoid RAG query delays
            context = f"User query about {sector or 'general intelligence'} topic: {user_text_english}"
            print(f"[DEMO MODE] Skipping RAG query, using quick context", file=sys.stderr)
        else:
            try:
                if sector:
                    context = get_context_string(user_text_english, sector=sector)
                else:
                    # Cross-sector query — get context from all sectors
                    all_ctx = get_all_sectors_context(user_text_english)
                    context = "\n\n--- AGRICULTURE DATA ---\n" + all_ctx["agriculture"]
                    context += "\n\n--- DISASTER DATA ---\n" + all_ctx["disaster"]
                    context += "\n\n--- HEALTH DATA ---\n" + all_ctx["health"]
                    context += "\n\n--- SECURITY DATA ---\n" + all_ctx.get("security", "No data available")
            except Exception as e:
                print(f"[RAG ERROR] {e}", file=sys.stderr)
                context = f"Error retrieving context: {str(e)[:100]}"

        # Step 4: LLM reasoning
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context data:\n{context}\n\nUser query: {user_text_english}"},
        ]
        try:
            response_english = chat_completion(messages, temperature=0.3, max_tokens=2000)
        except Exception as e:
            print(f"[LLM ERROR] {e}", file=sys.stderr)
            response_english = f"Error processing query: {str(e)[:100]}"

        # Step 5: Translate response back to user's language
        try:
            if reply_language != "en-IN":
                response_translated = translate_text(
                    response_english,
                    source_language="en-IN",
                    target_language=reply_language,
                )
            else:
                response_translated = response_english
        except Exception as e:
            print(f"[Translation ERROR] {e}", file=sys.stderr)
            response_translated = response_english

        # Step 6: Text to Speech
        try:
            response_audio = text_to_speech(response_translated, language_code=reply_language)
        except Exception as e:
            print(f"[TTS ERROR] {e}", file=sys.stderr)
            response_audio = b""

        return {
            "user_text": user_text,
            "user_text_english": user_text_english,
            "detected_language": reply_language,
            "response_english": response_english,
            "response_translated": response_translated,
            "response_audio": response_audio,
            "sector": sector or "cross-sector",
            "emergency_detected": _detect_emergency(user_text_english),
        }
    except Exception as e:
        print(f"[VOICE PIPELINE ERROR] {e}", file=sys.stderr)
        raise


def process_text_query(text: str, language_code: str = "en-IN") -> dict:
    """
    Text-based query pipeline (no audio).
    """
    try:
        detected_language = _detect_text_language(text) if language_code == "auto" else language_code

        # Translate to English if needed
        if detected_language != "en-IN":
            try:
                text_english = translate_text(text, source_language=detected_language, target_language="en-IN")
            except Exception as e:
                print(f"[TRANSLATE ERROR] {e}", file=sys.stderr)
                text_english = text
        else:
            text_english = text

        # RAG + LLM
        sector = _detect_sector(text_english)
        if DEMO_MODE:
            # In demo mode, use minimal context to avoid RAG query delays
            context = f"User query about {sector or 'general intelligence'} topic: {text_english}"
            print(f"[DEMO MODE] Skipping RAG query, using quick context", file=sys.stderr)
        else:
            try:
                if sector:
                    context = get_context_string(text_english, sector=sector)
                else:
                    all_ctx = get_all_sectors_context(text_english)
                    context = "\n\n--- AGRICULTURE DATA ---\n" + all_ctx["agriculture"]
                    context += "\n\n--- DISASTER DATA ---\n" + all_ctx["disaster"]
                    context += "\n\n--- HEALTH DATA ---\n" + all_ctx["health"]
                    context += "\n\n--- SECURITY DATA ---\n" + all_ctx.get("security", "No data available")
            except Exception as e:
                print(f"[RAG ERROR] {e}", file=sys.stderr)
                context = f"Error retrieving context: {str(e)[:100]}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context data:\n{context}\n\nUser query: {text_english}"},
        ]
        
        try:
            response_english = chat_completion(messages, temperature=0.3, max_tokens=2000)
        except Exception as e:
            print(f"[LLM ERROR] {e}", file=sys.stderr)
            response_english = f"Error processing query: {str(e)[:100]}"

        # Translate back
        try:
            if detected_language != "en-IN":
                response_translated = translate_text(
                    response_english,
                    source_language="en-IN",
                    target_language=detected_language,
                )
            else:
                response_translated = response_english
        except Exception as e:
            print(f"[TRANSLATE BACK ERROR] {e}", file=sys.stderr)
            response_translated = response_english

        return {
            "user_text": text,
            "user_text_english": text_english,
            "detected_language": detected_language,
            "response_english": response_english,
            "response_translated": response_translated,
            "sector": sector or "cross-sector",
            "emergency_detected": _detect_emergency(text_english),
        }
    except Exception as e:
        print(f"[TEXT PIPELINE ERROR] {e}", file=sys.stderr)
        raise


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

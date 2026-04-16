import os
import sys
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
SARVAM_BASE_URL = "https://api.sarvam.ai"

# Warn if API key is not configured
if not SARVAM_API_KEY or SARVAM_API_KEY == "your_sarvam_api_key_here":
    print("⚠️  WARNING: SARVAM_API_KEY not configured. Set it in .env file.", file=sys.stderr)
    print("   Export: export SARVAM_API_KEY=<your_key>", file=sys.stderr)
    print("   Or create .env file with: SARVAM_API_KEY=<your_key>", file=sys.stderr)

# Model IDs
STT_MODEL = "saaras:v3"
TTS_MODEL = "bulbul:v2"
TRANSLATE_MODEL = "mayura:v1"
EXTENDED_TRANSLATE_MODEL = "sarvam-translate:v1"
CHAT_MODEL = "sarvam-30b"
CHAT_MODEL_FLAGSHIP = "sarvam-105b"

# RAG settings
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RAG_TOP_K = 5

# Alert check interval in minutes
ALERT_CHECK_INTERVAL = 60

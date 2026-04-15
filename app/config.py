import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE_URL = "https://api.sarvam.ai"

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

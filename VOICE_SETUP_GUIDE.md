# Voice Chat Setup Guide — Complete Instructions

## Problem
Your voice chat button is not working with Sarvam AI voice I/O because:
1. **SARVAM_API_KEY environment variable is not set**
2. The system is running in DEMO_MODE (fake responses)
3. Voice output (TTS) is not being generated

## Solution: 3 Steps to Activate Voice Chat

### Step 1: Get Your Sarvam AI API Key

1. Visit: **https://console.sarvam.ai/**
2. Sign up for free (it's free for hackathons!)
3. Generate an API key from the dashboard
4. Copy the API key

### Step 2: Set the Environment Variable

#### Option A: Create/Update `.env` file (RECOMMENDED)

In the project root (`Hackathon_Noida/`), create or edit `.env`:

```env
SARVAM_API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with the key you copied above.

**Then restart your FastAPI server:**
```bash
# Stop the server (Ctrl+C)
# Run again:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option B: Set via PowerShell Terminal (Windows)

```powershell
$env:SARVAM_API_KEY="your_actual_api_key_here"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option C: Set via Terminal (Linux/Mac)

```bash
export SARVAM_API_KEY="your_actual_api_key_here"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Test Voice Chat

1. Open **http://localhost:8000** in your browser
2. Go to **Dashboard 2: Intelligence Assistant** (or any dashboard)
3. Click the **Ask Me** button (bottom-right floating panel)
4. Click the **🎤 Microphone icon**
5. Speak in any Indian language (Hindi, Tamil, Telugu, etc.)
6. Click **⏹ Stop** button
7. **You should hear an AI response in your language!**

---

## How It Works After Configuration

### Voice Pipeline Flow:

```
1. Browser captures audio 🎤
   ↓
2. Sends to /api/voice-query endpoint
   ↓
3. Sarvam AI STT (Saaras v3) converts audio → text
   ↓
4. RAG Engine retrieves relevant documents from knowledge base
   ↓
5. Sarvam AI LLM (sarvam-30b) generates response
   ↓
6. Sarvam AI TTS (Bulbul v2) converts response → audio 🔊
   ↓
7. Browser plays audio response
```

### Supported Languages:
- 🇮🇳 Hindi (hi-IN)
- 🇮🇳 Tamil (ta-IN)
- 🇮🇳 Telugu (te-IN)
- 🇮🇳 Marathi (mr-IN)
- 🇮🇳 Bengali (bn-IN)
- 🇮🇳 Gujarati (gu-IN)
- 🇮🇳 Kannada (kn-IN)
- 🇮🇳 Malayalam (ml-IN)
- 🇮🇳 Punjabi (pa-IN)
- 🇮🇳 Odia (od-IN)
- 🇬🇧 English (en-IN)

---

## Troubleshooting

### ❌ Problem: "Microphone unavailable on non-secure connection"

**Solution:** Make sure you're accessing the app at:
```
http://localhost:8000
```
NOT at an IP address like `192.168.x.x:8000`

### ❌ Problem: "Microphone permission denied"

**Solution:** 
1. Click the 🔒 lock icon in your browser address bar
2. Find "Microphone" settings
3. Change to "Allow"
4. Refresh the page and try again

### ❌ Problem: "Processing voice input..." hangs (>10 seconds)

**Solution:**
1. Check that SARVAM_API_KEY is configured
2. Look at the console/terminal logs (they'll show if DEMO_MODE is active)
3. Restart the FastAPI server

**To check if SARVAM_API_KEY is loaded:**
- Watch the terminal output when starting the server
- You should NOT see: "⚠️ WARNING: SARVAM_API_KEY not configured"

### ❌ Problem: Server outputs "DEMO_MODE: Using mock responses"

**Cause:** SARVAM_API_KEY is not set in the environment

**Solution:** Follow Step 1-2 above and restart the server

---

## Verify Configuration

You can verify the key is loaded by checking the server startup logs:

**Correct (with API key):**
```
✅ Sarvam AI Client initialized with API key
✅ STT (Saaras v3) ready
✅ TTS (Bulbul v2) ready
✅ LLM (sarvam-30b) ready
```

**Incorrect (without API key):**
```
⚠️ WARNING: SARVAM_API_KEY not configured. Set it in .env file.
⚠️ DEMO MODE: Using mock responses (API key not configured)
```

---

## Testing the Voice API Directly (Advanced)

If you want to test without the UI:

```bash
# Record audio (5 seconds)
# Then test with cURL (replace YOUR_KEY):

curl -X POST http://localhost:8000/api/voice-query \
  -F "audio=@recording.wav" \
  -F "language_code=hi-IN"
```

---

## Sample Voice Queries to Try

1. **Agriculture**: "चावल की फसल कैसी है?" (How's the rice crop?)
2. **Disaster**: "Brahmaputra में बाढ़ का खतरा है क्या?" (Is there flood risk in Brahmaputra?)
3. **Health**: "डेंगू के cases कहाँ बढ़ रहे हैं?" (Where are dengue cases increasing?)
4. **Incidents**: "कौन से incidents pending हैं?" (What incidents are pending?)
5. **Security**: "किसान आंदोलन की स्थिति क्या है?" (What's the status of the farmers protest?)

---

## Support

If voice chat still doesn't work after these steps:

1. **Check browser console:** Press F12 → Console tab → Look for errors
2. **Check server logs:** Watch the terminal running `uvicorn app.main:app`
3. **Verify .env file exists:** `cat .env` (Linux/Mac) or `type .env` (Windows)
4. **Restart everything:** Stop server, stop browser, clear cache, try again

---

## Next Steps

Once voice chat is working:

1. **Ask intelligence questions** across all sectors (agriculture, health, disaster, security)
2. **Try different languages** — speak in Hindi, get response in Tamil
3. **Enable emergency detection** — say "bachao" or "help" to trigger SOS
4. **Use RAG grounding** — notice how responses cite real intelligence documents

Enjoy your voice-enabled government intelligence platform! 🎤🎉

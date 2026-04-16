# Public Intelligence System

> **AI-Powered, Multilingual, Voice-Enabled Intelligence Platform for Indian Government Officials**

A comprehensive web application that gives government officials a single command-center to monitor agriculture, disasters, public health, weather, security threats, live events, and citizen-reported incidents — all queryable by voice or text in **11 Indian languages**.

## Overview

The **Public Intelligence System** uses **Sarvam AI** for speech recognition, translation, multilingual response generation, and text-to-speech, while **ChromaDB RAG** grounds answers in real intelligence data. Powered by FastAPI backend, Vanilla JS frontend, and an integrated voice pipeline.

## Key Features

| Feature | Description |
|---------|-------------|
| **10 Dashboards** | Alerts, Intelligence, Map, Analytics, Emergency, Agriculture, Health, Weather, Incidents, Weather Advisory |
| **Live Events Tracker** | Real-time monitoring of protests, wars, pandemics, strikes, disasters, Naxal activity |
| **AI Chat (Ask Me)** | Floating panel on every page — text or voice Q&A in 11 languages, RAG-grounded |
| **Voice Pipeline** | Full multilingual speech-to-speech with Sarvam AI |
| **Proactive Alerts** | LLM scans all sectors hourly to detect escalating risks |
| **Emergency SOS** | One-tap SOS with live GPS tracking and emergency contacts |
| **Incident Reporting** | Citizens report issues → auto-assigned to correct govt department |
| **Emergency Keyword Detection** | 60+ keywords (Hindi/English/Hinglish) trigger automatic SOS |
| **Multilingual** | 11 Indian languages for input, reasoning, and output |
| **Interactive Maps** | Leaflet.js with OpenStreetMap — free, no API key |
| **RAG-Grounded** | Every AI answer cites real intelligence documents |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.10+) |
| **AI Engine** | Sarvam AI (STT, TTS, Translation, LLM) |
| **Vector DB** | ChromaDB 0.5.0 |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **Scheduler** | APScheduler |
| **Maps** | Leaflet.js 1.9.4 |
| **Charts** | Chart.js 4.4.0 |
| **Frontend** | Vanilla HTML/CSS/JS (zero dependencies) |

## Requirements

- Python 3.10+
- pip
- Sarvam AI API Key (free tier available)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/hackathon-noida.git
cd Hackathon_Noida
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
# Windows
set SARVAM_API_KEY=your_api_key_here

# Linux/Mac
export SARVAM_API_KEY=your_api_key_here
```

## Running the Application

### Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

Open your browser and navigate to:

```
http://localhost:8000
```

## Project Structure

```
Hackathon_Noida/
│
├── app/
│   ├── __init__.py
│   ├── config.py              # Environment variables & model configs
│   ├── main.py                # FastAPI server & all endpoints
│   ├── voice_pipeline.py      # STT → Translate → RAG → LLM → TTS
│   ├── rag_engine.py          # ChromaDB vector store & retrieval
│   ├── alert_engine.py        # Proactive LLM-powered alert analysis
│   ├── sarvam_client.py       # Sarvam AI SDK wrapper
│   └── sample_data.py         # 28+ seed documents for RAG
│
├── frontend/
│   ├── index.html             # 10 dashboards + Ask Me panel
│   ├── app.js                 # Frontend logic & interactions
│   └── style.css              # Dark-themed responsive UI
│
├── chroma_db/                 # Persistent vector database storage
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── Sanket.ai_documentation.md # Full product documentation
```

## API Endpoints (49 Total)

### Voice & Text Q&A
- `POST /api/voice-query` — Audio in → AI response + audio out
- `POST /api/text-query` — Text query → AI response
- `POST /api/translate` — Translate text between languages
- `POST /api/tts` — Text-to-speech conversion

### Alerts
- `GET /api/alerts` — Active alerts
- `GET /api/alerts/all` — All alerts including acknowledged
- `POST /api/alerts/check` — Trigger LLM alert analysis
- `POST /api/alerts/acknowledge` — Mark alert as acknowledged

### Live Events
- `GET /api/live-events` — All events with filters
- `GET /api/live-events/{id}` — Single event detail
- `POST /api/live-events` — Add new event
- `PATCH /api/live-events/{id}` — Update event

### Agriculture (8 endpoints)
- `/api/agriculture/dashboard`, `/crops`, `/weather`, `/hygiene`, `/prices`, `/insights`, `/recommendations`, `/rain-advisory`

### Public Health (6 endpoints)
- `/api/health/dashboard`, `/outbreaks`, `/vaccination`, `/sanitation`, `/hospitals`, `/safety`

### Weather (7 endpoints)
- `/api/weather/dashboard`, `/current`, `/forecast`, `/historical`, `/alerts`, `/monsoon`, `/recommendations`

### Incidents (4 endpoints)
- `GET/POST /api/incidents` — List/create incidents
- `GET/PATCH /api/incidents/{id}` — Detail/update incident

### Emergency & SOS (7 endpoints)
- `/api/sos`, `/api/sos/location`, `/api/sos/{id}/trail`, etc.
- `/api/notify`, `/api/notifications`

### Knowledge Base & System
- `POST /api/ingest` — Ingest documents to RAG
- `GET /api/rag/stats` — KB statistics
- `GET /api/rag/search` — Search knowledge base
- `GET /api/health` — System health check

## Dashboards

### Dashboard 1 — Alerts & Live Events
Primary monitoring screen with live alerts feed, threat map, and India Situation Monitor.

### Dashboard 2 — Intelligence Assistant
AI-powered conversational Q&A with text and voice input, RAG-grounded responses.

### Dashboard 3 — National Threat & Risk Map
Full-screen interactive Leaflet.js map with color-coded alert markers.

### Dashboard 4 — Analytics
Sector distribution and risk levels by region using Chart.js.

### Dashboard 5 — Emergency & SOS
SOS button, live location tracking, emergency contacts, keyword detection.

### Dashboard 6 — Agriculture
Crop status, weather alerts, mandi prices, seasonal recommendations, rain advisory.

### Dashboard 7 — Public Health & Safety
Disease outbreaks, vaccination status, water & sanitation, hospital capacity.

### Dashboard 8 — Weather
Current conditions, 7-day forecast, historical trends, monsoon prediction, severe weather alerts.

### Dashboard 9 — Incident Reporting
Citizen reporting system with auto-assignment to government departments.

### Dashboard 10 — Weather Advisory & Impact Desk
Decision-oriented weather operations with state-wise guidance and sector impact analysis.

## Languages Supported

11 Indian languages + English:
- Hindi (hi-IN)
- Bengali (bn-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Marathi (mr-IN)
- Gujarati (gu-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Odia (od-IN)
- Punjabi (pa-IN)
- English (en-IN)

Auto-detect mode available for language identification.

## Knowledge Base (RAG)

28+ intelligence documents across sectors:

| Sector | Documents | Topics |
|--------|-----------|--------|
| **Agriculture** | 6 | Kharif rainfall, wheat procurement, coffee, Rabi forecast, tea, paddy |
| **Disaster** | 6 | Brahmaputra floods, cyclones, landslides, Chennai floods, earthquakes, dams |
| **Health** | 6 | Dengue, Cholera, JE, Nipah, Malaria, Heat illness |
| **Security** | 4 | Farmer protests, communal tension, Manipur violence, bandh |
| **Security Threats** | 4 | Naxal activity, LoC tensions, transport strike, cyber threats |
| **Cross-Sector** | 2 | Flood-health, climate-agriculture |
| **Live Events** | 8 | Auto-ingested from tracker |

## Startup Behavior

On application startup, the system automatically:
- Seeds 28+ intelligence documents into ChromaDB
- Starts the background alert scheduler (60-minute cycle)
- Serves the frontend dashboard

## Configuration

Key environment variables in `app/config.py`:

```python
SARVAM_API_KEY          # Sarvam AI API key
MODEL_IDS               # Sarvam models for STT, TTS, LLM
CHROMA_DB_PATH          # ChromaDB persistence location
ALERT_CHECK_INTERVAL    # Alert scan frequency (default: 3600s)
```

## Future Enhancements

- **Live Data Feeds** — Real-time APIs from IMD, NDMA, IDSP
- **Role-Based Access** — District Collector vs. State HQ vs. Central views
- **Persistent Storage** — Database-backed alert history
- **Mobile PWA** — Lightweight app for field officials
- **SMS/WhatsApp Integration** — Push critical alerts via messaging
- **Feedback Loop** — Official ratings improve LLM accuracy

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is built for the Hackathon Noida 2026.

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the development team.

## Built With

- **Sarvam AI** — Multilingual AI capabilities
- **FastAPI** — Modern Python web framework
- **ChromaDB** — Vector database for RAG
- **Leaflet.js** — Interactive mapping
- **Chart.js** — Data visualization
- **Vanilla JS** — Frontend logic (zero dependencies)

---

*Built with Sarvam AI · FastAPI · ChromaDB · Leaflet.js · Chart.js for Indian Government Intelligence Operations*

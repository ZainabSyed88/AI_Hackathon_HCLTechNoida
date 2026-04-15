# Public Intelligence System — Product Documentation

> AI-Powered, Multilingual, Voice-Enabled Intelligence Platform for Indian Government Officials

---

## Overview

The **Public Intelligence System** is a web application that gives government officials a single command-center to monitor agriculture, disasters, public health, weather, security threats, live events (protests, wars, pandemics), and citizen-reported incidents — all queryable by voice or text in **11 Indian languages**. It uses **Sarvam AI** for speech, translation, and reasoning, and **ChromaDB RAG** to ground every answer in real intelligence data.

**At a Glance:**

| Metric | Value |
|--------|-------|
| Dashboards | 9 full-featured dashboards |
| API Endpoints | 49 REST endpoints |
| Languages Supported | 11 Indian languages + auto-detect |
| AI Models | Sarvam Saaras v3 (STT), Bulbul v2 (TTS), Mayura v1 (Translation), sarvam-30b/105b (LLM) |
| External API Keys | 1 (Sarvam AI only) |
| Maps | OpenStreetMap + CARTO (free, no key) |
| Frontend Framework | Zero-dependency vanilla HTML/CSS/JS |
| Backend | Python FastAPI, single process |

---

## Dashboards

### Dashboard 1 — Alerts & Live Events

The primary monitoring screen for officials.

**Live Alerts Feed**
- AI-generated alerts across 6 types: protest, civil unrest, security threat, disaster, health, agriculture
- Severity-graded: CRITICAL / HIGH / MODERATE / LOW with color coding
- Filter by type and severity
- One-click acknowledge workflow
- Auto-scan every 60 minutes + manual "Scan Now" button

**Threat Map**
- Interactive Leaflet.js map of India with color-coded risk markers
- OpenStreetMap tiles (free, no API key)
- Click markers for alert details

**Notify Citizens**
- Send emergency notifications via SMS, WhatsApp, Call, or All Channels
- Per-alert or general broadcast
- Full notification log with timestamps

**🔴 Live Events Intelligence — India Situation Monitor**
- Real-time tracking of ongoing protests, wars, pandemics, strikes, disasters, and insurgency
- 8 pre-seeded live events including:
  - ✊ Farmers Protest — Delhi-Haryana Border (MSP demands, NH-44 blockade)
  - ⚔️ LoC Tensions — Poonch & Rajouri ceasefire violations
  - 🦠 Nipah Virus Alert — Kerala Kozhikode
  - 🚛 Nationwide Transport Strike — fuel price protest
  - 🔥 Manipur Ethnic Violence — Churachandpur & Bishnupur
  - 🌊 Brahmaputra Flood Warning — Assam
  - 🎯 Naxal Activity Surge — Chhattisgarh Bastar
  - ✊ Anti-Reservation Bharat Bandh — Rajasthan & Gujarat
- Each event card shows: severity badge, escalation status, key facts, timeline, impact (people + economic), affected areas, government response, source, tags
- Filter by event type (protest/war/pandemic/strike/disaster/naxal) and severity
- LIVE pulse indicator
- Stats strip: active events, critical, escalating, protests, security, health
- Events are auto-ingested into the RAG knowledge base so the AI assistant can answer questions about them

### Dashboard 2 — Intelligence Assistant

AI-powered conversational Q&A.

- **Text chat**: Type questions about crop status, flood risk, disease outbreaks, protests — get grounded answers with source citations
- **Voice input**: Record voice in any Indian language; system transcribes, translates, reasons, and responds with audio
- **Knowledge Base stats**: Document count, 4 sectors, 11 languages
- RAG-grounded — every answer cites real intelligence data

### Dashboard 3 — National Threat & Risk Map

Full-screen interactive map of India.

- Color-coded markers for all active alerts
- Legend: 🔴 Critical, 🟠 High, 🟡 Moderate, 🟢 Low
- Click markers for detailed alert information
- Auto-populated from alert engine data

### Dashboard 4 — Analytics

Visual data analysis with charts.

- **Sector Distribution** — Pie/doughnut chart of alerts by sector (agriculture, disaster, health, security)
- **Risk Levels by Region** — Bar chart showing threat concentration across Indian states
- Powered by Chart.js 4.4.0

### Dashboard 5 — Emergency & SOS

Citizen safety and emergency response.

- **SOS Button** — Sends live GPS location to Police + Ambulance
- **Live Location Tracking** — Continuous GPS watchPosition streaming to server
- **Location trail** — Full movement history during active SOS
- **Emergency contacts grid** — Police (100), Ambulance (108), Fire (101), Women Helpline (181), Disaster (1078), Child Helpline (1098)
- **Dual-layer emergency keyword detection** — 60+ keywords in English, Hindi, and Hinglish (bachao, help, sos, madat, etc.) trigger automatic SOS from voice/text queries

### Dashboard 6 — Agriculture

Comprehensive farming intelligence.

- **Crop Status** — District-wise crop health with yield predictions
- **Weather Alerts** — Agricultural weather impacts
- **Mandi Prices** — Current commodity prices across mandis
- **Hygiene Reports** — Food safety and farm hygiene
- **Seasonal Recommendations** — Kharif/Rabi/Zaid crop and fertilizer recommendations with state-specific guidance
- **Unpredicted Rain Advisory** — Protective measures for standing crops vs harvested produce
- **RAG-powered insights** — AI-analyzed agricultural intelligence

### Dashboard 7 — Public Health & Safety

Disease surveillance and health infrastructure monitoring.

- **Disease Outbreaks** — 8 tracked diseases (Dengue, Cholera, Malaria, Japanese Encephalitis, TB, COVID-19, Chikungunya, Typhoid) with case counts, deaths, affected districts, status badges, filterable
- **Vaccination Status** — 8 programs with coverage percentages and target groups
- **Water & Sanitation** — 7 regions with water quality index, sanitation coverage, open defecation status
- **Hospital Capacity** — 6 regions showing total beds, ICU beds, ventilators, occupancy rates with color-coded load indicators
- **Public Safety Alerts** — Active safety alerts with severity and recommended actions

### Dashboard 8 — Weather Forecasting

Multi-layer weather intelligence.

- **Current Conditions** — 8 major Indian cities with temperature, humidity, wind, UV index, AQI
- **7-Day Forecast** — Daily forecast strip with Chart.js temperature trend line
- **Historical Trends** — 12-month temperature and rainfall visualization
- **Geography Zones** — 7 climate zones plotted on an interactive map (Himalayan, Indo-Gangetic, Coastal, Desert, Peninsular, NE, Island)
- **Monsoon Prediction** — Onset date, withdrawal date, overall rainfall percentage, La Niña/El Niño status, IMD forecast
- **Severe Weather Alerts** — Active warnings with affected regions and timeline

### Dashboard 9 — Incident Reporting

Government issue tracking system for citizens and officials.

- **Raise New Incident** — Form with:
  - Title, category (10 types: Infrastructure, Health & Sanitation, Environment, Agriculture, Law & Order, Disaster, Education, Corruption, Women Safety, Other)
  - Severity (Moderate / High / Critical)
  - Description, GPS-enabled location detect, reporter name & contact
- **Auto-assignment** — Incidents auto-assigned to correct government department:
  - Infrastructure → Public Works Department (PWD)
  - Health → Public Health Engineering / Municipal Corp
  - Environment → State Forest Dept / Pollution Control Board
  - Agriculture → Agriculture Dept / PMFBY Cell
  - Law & Order → District Police / Home Dept
  - Disaster → NDMA / State Disaster Management Authority
  - Corruption → Anti-Corruption Bureau / Lokayukta
  - Women Safety → Women & Child Development Dept / Police
- **Incident Tracker** — Status-coded list with filters (Submitted → Under Review → Assigned → In Progress → Resolved)
- **Stats bar** — Total, Submitted, Under Review, In Progress, Resolved counts
- **Update timeline** — Each incident tracks status changes and notes

### Global — Ask Me Panel (Floating)

Available on every dashboard.

- Floating action button (bottom-right) opens sliding chat panel
- **Text chat** with Sarvam AI LLM — ask anything about the intelligence data
- **Voice recording** — Record in any language, get voice + text response
- **TTS toggle** — Enable/disable spoken responses
- **11-language selector** + Auto-detect mode
- Uses RAG to answer from the knowledge base

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | **FastAPI** (Python 3.10+) | Async REST API server |
| AI Engine | **Sarvam AI** | STT (Saaras v3), TTS (Bulbul v2), Translation (Mayura v1), LLM (sarvam-30b/105b) |
| Vector DB | **ChromaDB 0.5.0** | RAG knowledge base with persistent storage |
| Embeddings | **Sentence Transformers** (all-MiniLM-L6-v2) | Semantic document embeddings |
| Scheduler | **APScheduler** | Hourly proactive alert analysis |
| Maps | **Leaflet.js 1.9.4** | Interactive maps (OpenStreetMap + CARTO tiles — free, no key) |
| Charts | **Chart.js 4.4.0** | Data visualization (sector, risk, weather, forecast charts) |
| Frontend | **Vanilla HTML/CSS/JS** | Zero-dependency, fast-loading, works on low-bandwidth |

**Only 1 API key required:** `SARVAM_API_KEY`
**Maps are 100% free:** OpenStreetMap + CARTO dark tiles — no API key needed.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     BROWSER (9 Dashboards)                         │
│                                                                    │
│  Alerts & Live Events │ Intelligence │ Map │ Analytics │ Emergency │
│  Agriculture │ Health │ Weather │ Incidents │ Ask Me (floating)    │
│                                                                    │
│  Leaflet.js Maps  ·  Chart.js Charts  ·  MediaRecorder (Voice)   │
└────────────────────────────┬───────────────────────────────────────┘
                             │ REST API (fetch)
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    FastAPI BACKEND (Python)                         │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ Voice        │  │ Alert Engine │  │ Live Events Tracker     │  │
│  │ Pipeline     │  │ (APScheduler │  │ (Protests, Wars,        │  │
│  │ STT→RAG→LLM │  │  hourly scan │  │  Pandemics, Strikes,    │  │
│  │ →Translate   │  │  across all  │  │  Disasters, Naxal)      │  │
│  │ →TTS         │  │  sectors)    │  │  → Auto-ingested to RAG │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬────────────┘  │
│         │                 │                        │               │
│         ▼                 ▼                        ▼               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              RAG Engine (ChromaDB + Sentence Transformers)   │  │
│  │  28+ documents: Agriculture, Disaster, Health, Security     │  │
│  │  + Live events auto-ingested for real-time AI awareness     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │         Sarvam AI Client (single API key)                    │  │
│  │  STT: Saaras v3 │ TTS: Bulbul v2 │ Translate: Mayura v1    │  │
│  │  LLM: sarvam-30b / sarvam-105b (chat completion)            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  In-Memory Data Stores:                                            │
│  _agriculture_data · _health_data · _weather_data                  │
│  _live_events · _incidents · _alerts · _sos_requests               │
└────────────────────────────────────────────────────────────────────┘
```

---

## API Reference (49 Endpoints)

### Voice & Text Q&A
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice-query` | Audio in → transcription + AI response + audio out |
| `POST` | `/api/text-query` | Text query in any language → AI response |
| `POST` | `/api/translate` | Translate text between Indian languages |
| `POST` | `/api/tts` | Text-to-speech conversion |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/alerts` | Active alerts (filterable by severity) |
| `GET` | `/api/alerts/all` | All alerts including acknowledged |
| `POST` | `/api/alerts/check` | Manually trigger LLM alert analysis |
| `POST` | `/api/alerts/acknowledge` | Mark alert as acknowledged |
| `POST` | `/api/alerts/translate` | Translate alert to target language |

### Live Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/live-events` | All events with type/state/severity/status filters + stats |
| `GET` | `/api/live-events/{id}` | Single event detail |
| `POST` | `/api/live-events` | Add new live event (auto-ingested to RAG) |
| `PATCH` | `/api/live-events/{id}` | Update event status/escalation, add timeline entry |

### Agriculture (8 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agriculture/dashboard` | Full agriculture dashboard |
| `GET` | `/api/agriculture/crops` | Crop status by district |
| `GET` | `/api/agriculture/weather` | Agricultural weather alerts |
| `GET` | `/api/agriculture/hygiene` | Farm hygiene reports |
| `GET` | `/api/agriculture/prices` | Mandi commodity prices |
| `GET` | `/api/agriculture/insights` | RAG-powered AI insights |
| `GET` | `/api/agriculture/recommendations` | Seasonal crop & fertilizer guidance |
| `GET` | `/api/agriculture/rain-advisory` | Unpredicted rain protection advice |

### Public Health (6 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/dashboard` | Full health dashboard |
| `GET` | `/api/health/outbreaks` | Disease outbreaks (8 diseases) |
| `GET` | `/api/health/vaccination` | Vaccination program status |
| `GET` | `/api/health/sanitation` | Water quality & sanitation data |
| `GET` | `/api/health/hospitals` | Hospital capacity & ICU beds |
| `GET` | `/api/health/safety` | Public safety alerts |

### Weather (6 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/weather/dashboard` | Full weather dashboard |
| `GET` | `/api/weather/current` | Current conditions (8 cities) |
| `GET` | `/api/weather/forecast` | 7-day forecast |
| `GET` | `/api/weather/historical` | 12-month historical trends |
| `GET` | `/api/weather/alerts` | Severe weather alerts |
| `GET` | `/api/weather/monsoon` | Monsoon prediction data |

### Incidents (4 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/incidents` | All incidents with status/category/severity filters + stats |
| `POST` | `/api/incidents` | Submit new incident (auto-assigns department) |
| `PATCH` | `/api/incidents/{id}` | Update status, add notes |
| `GET` | `/api/incidents/{id}` | Single incident detail |

### Notifications & SOS
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/notify` | Send emergency notification (SMS/WhatsApp/Call) |
| `GET` | `/api/notifications` | Notification history |
| `POST` | `/api/sos` | Create SOS with live GPS location |
| `POST` | `/api/sos/location` | Stream location updates during SOS |
| `GET` | `/api/sos/{id}/trail` | Full location trail for an SOS |
| `POST` | `/api/sos/{id}/stop` | Stop SOS tracking |
| `GET` | `/api/sos` | Active SOS requests |

### Knowledge Base & System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest` | Ingest new documents into RAG |
| `GET` | `/api/rag/stats` | Knowledge base statistics |
| `GET` | `/api/rag/search` | Search the knowledge base |
| `GET` | `/api/health` | System health check |
| `GET` | `/` | Serve the frontend application |

---

## Knowledge Base (RAG)

28+ intelligence documents across 4 sectors, auto-seeded on first run:

| Sector | Documents | Topics |
|--------|-----------|--------|
| **Agriculture** | 6 | Kharif rainfall (Maharashtra), wheat procurement (Punjab), coffee plantations (Kerala), Rabi forecast (AP), tea production (Assam), paddy cultivation (Tamil Nadu) |
| **Disaster** | 6 | Brahmaputra floods (Assam), Bay of Bengal cyclones, Uttarakhand landslides, Chennai floods, Gujarat earthquakes, MP dam safety |
| **Health** | 6 | Dengue 8,500 cases (Maharashtra), Cholera 340 cases (Bihar), JE 180 cases (UP), Nipah alert (Kerala), Malaria (Odisha), Heat illness (Rajasthan) |
| **Security** | 4 | Farmer protests (Delhi-Haryana), communal tension (UP), Manipur violence, anti-reservation bandh (Rajasthan-Gujarat) |
| **Security Threats** | 4 | Naxal activity (Chhattisgarh), LoC ceasefire violations (J&K), transport strike (Pan-India), cyber threat (CERT-In) |
| **Cross-Sector** | 2 | Flood health-agriculture impact (Bihar), climate-agriculture nexus (Western Ghats) |
| **Live Events** | 8 | Auto-ingested from live events tracker (farmers protest, Manipur violence, Nipah alert, transport strike, LoC tensions, Brahmaputra flood, Naxal surge, bandh) |

---

## Languages Supported

| # | Language | Code | STT | TTS | Translation | LLM Chat |
|---|----------|------|-----|-----|-------------|----------|
| 1 | Hindi | hi-IN | ✅ | ✅ | ✅ | ✅ |
| 2 | Bengali | bn-IN | ✅ | ✅ | ✅ | ✅ |
| 3 | Tamil | ta-IN | ✅ | ✅ | ✅ | ✅ |
| 4 | Telugu | te-IN | ✅ | ✅ | ✅ | ✅ |
| 5 | Marathi | mr-IN | ✅ | ✅ | ✅ | ✅ |
| 6 | Gujarati | gu-IN | ✅ | ✅ | ✅ | ✅ |
| 7 | Kannada | kn-IN | ✅ | ✅ | ✅ | ✅ |
| 8 | Malayalam | ml-IN | ✅ | ✅ | ✅ | ✅ |
| 9 | Odia | od-IN | ✅ | ✅ | ✅ | ✅ |
| 10 | Punjabi | pa-IN | ✅ | ✅ | ✅ | ✅ |
| 11 | English | en-IN | ✅ | ✅ | ✅ | ✅ |

Auto-detect mode available — system identifies the spoken language automatically.

---

## Project Structure

```
public-intelligence-system/
│
├── app/
│   ├── __init__.py
│   ├── config.py            # Environment variables, model IDs
│   ├── main.py              # FastAPI server — 49 endpoints, all data stores
│   ├── voice_pipeline.py    # STT → Translate → RAG → LLM → Translate → TTS
│   ├── rag_engine.py        # ChromaDB vector store + semantic retrieval
│   ├── alert_engine.py      # Proactive LLM-powered alert analysis (hourly)
│   ├── sarvam_client.py     # Sarvam AI SDK wrapper (STT, TTS, Translate, LLM)
│   └── sample_data.py       # 28+ seed documents for RAG knowledge base
│
├── frontend/
│   ├── index.html           # 9 dashboard pages + sidebar + Ask Me panel
│   ├── app.js               # All frontend logic (~2,100 lines)
│   └── style.css            # Dark-themed responsive UI (~1,500 lines)
│
├── requirements.txt         # Python dependencies
└── APPROACH_DOCUMENT.md     # This document
```

---

## Setup & Running

**Prerequisites:** Python 3.10+, pip

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Set environment variable:**
```bash
# Linux/Mac
export SARVAM_API_KEY=your_key_here

# Windows
set SARVAM_API_KEY=your_key_here
```

**3. Run the server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**4. Open in browser:**
```
http://localhost:8000
```

---

## Key Features Summary

| Feature | Description |
|---------|-------------|
| **9 Dashboards** | Alerts, Intelligence, Map, Analytics, Emergency, Agriculture, Health, Weather, Incidents |
| **Live Events Tracker** | Real-time monitoring of protests, wars, pandemics, strikes, disasters, Naxal activity across India |
| **AI Chat (Ask Me)** | Floating panel on every page — text or voice Q&A in 11 languages, RAG-grounded |
| **Voice Pipeline** | Full speech-to-speech: Speak in Hindi → get answer in Hindi audio |
| **Proactive Alerts** | LLM scans all sectors hourly to detect escalating risks before they happen |
| **Emergency SOS** | One-tap SOS with live GPS tracking, emergency contacts, keyword detection |
| **Incident Reporting** | Citizens report issues → auto-assigned to correct govt department → tracked to resolution |
| **Emergency Keyword Detection** | 60+ keywords (Hindi/English/Hinglish) trigger automatic SOS from voice/text |
| **Multilingual** | 11 Indian languages for input, output, translation, and TTS |
| **Cross-Sector AI** | Connects agriculture + disaster + health + security data to find compound risks |
| **Interactive Maps** | Leaflet.js with OpenStreetMap — free, no API key |
| **RAG-Grounded** | Every AI answer cites real intelligence documents — no hallucination |
| **Zero Dependencies** | Vanilla JS frontend — loads fast on government networks |

---

## 12. How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variable
echo SARVAM_API_KEY=your_api_key > .env

# 3. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Open browser
# → http://localhost:8000
```

On startup, the system automatically:
- Seeds 20+ intelligence documents into ChromaDB
- Starts the background alert scheduler (60-minute cycle)
- Serves the frontend dashboard

---

## 13. Future Scope

- **Live Data Feeds** — Integrate real-time APIs from IMD (weather), NDMA (disasters), IDSP (disease surveillance)
- **Role-Based Access** — District Collector vs. State HQ vs. Central Ministry views
- **Persistent Alert Storage** — Move from in-memory to database-backed alert history
- **Mobile App** — Lightweight PWA for field officials with offline caching
- **SMS/WhatsApp Alerts** — Push critical alerts via SMS or WhatsApp for areas with poor internet
- **Feedback Loop** — Officials rate alert accuracy, improving LLM prompts over time

---

*Built with Sarvam AI · FastAPI · ChromaDB · Leaflet.js · Chart.js*

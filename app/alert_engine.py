"""
Proactive Alert Engine
Periodically analyzes data to generate early warnings for
crop failure, floods, disease outbreaks, etc.
"""
import json
import time
from datetime import datetime
from app.sarvam_client import chat_completion, translate_text
from app.rag_engine import get_all_sectors_context

# In-memory alert store — pre-seeded with live sample data
_alerts: list[dict] = [
    {
        "id": "alert_001",
        "severity": "CRITICAL",
        "sector": "disaster",
        "alert_type": "disaster",
        "title": "Flood Risk: Brahmaputra Approaching Danger Mark — Assam",
        "description": "Brahmaputra water level at 49.2m, approaching danger mark of 49.68m. Rising 0.15m/day from upstream Bhutan dam releases. NDRF teams on standby. Risk of displacement for 45+ lakh people in Kamrup.",
        "affected_regions": ["Assam", "Kamrup", "Guwahati"],
        "recommended_actions": ["Deploy NDRF teams immediately", "Prepare evacuation routes for low-lying villages", "Issue flood early warning to district collectors"],
        "confidence": 0.92,
        "acknowledged": False,
        "timestamp": "2026-04-15T08:00:00",
    },
    {
        "id": "alert_002",
        "severity": "HIGH",
        "sector": "security",
        "alert_type": "civil_unrest",
        "title": "Farmer Protest: NH-44 Blockade — Punjab-Haryana Border",
        "description": "Large-scale farmer agitation blocking NH-44 at Shambhu barrier. ~10,000 protestors gathered. Supply chain disruption risk to Delhi NCR — fuel, vegetables, dairy in short supply.",
        "affected_regions": ["Punjab", "Haryana", "Delhi NCR"],
        "recommended_actions": ["Deploy additional security forces", "Open alternate highway routes NH-58 and NH-709", "Initiate dialogue with protest leaders"],
        "confidence": 0.88,
        "acknowledged": False,
        "timestamp": "2026-04-15T07:30:00",
    },
    {
        "id": "alert_003",
        "severity": "HIGH",
        "sector": "health",
        "alert_type": "health",
        "title": "Dengue Spike: 437 New Cases in 48h — Maharashtra",
        "description": "437 new dengue cases in Mumbai, Pune, Nagpur — 3x the weekly average. Hospital capacity under pressure in Dharavi and Govandi. Aedes aegypti breeding detected in 12 municipal wards.",
        "affected_regions": ["Mumbai", "Pune", "Nagpur", "Maharashtra"],
        "recommended_actions": ["Activate vector control teams citywide", "Issue public health advisory", "Scale up hospital preparedness for 500+ additional cases"],
        "confidence": 0.85,
        "acknowledged": False,
        "timestamp": "2026-04-15T06:45:00",
    },
    {
        "id": "alert_004",
        "severity": "MODERATE",
        "sector": "agriculture",
        "alert_type": "agriculture",
        "title": "Drought Stress: 40% Soybean Yield Reduction Risk — Vidarbha",
        "description": "30% below-normal rainfall in Vidarbha region. Soil moisture at 45% against normal 70%. Soybean sowing delayed 3 weeks in Yavatmal, Akola, Amravati. Historical 2015 parallel suggests 40% yield loss.",
        "affected_regions": ["Vidarbha", "Yavatmal", "Akola", "Amravati"],
        "recommended_actions": ["Fast-track crop insurance claims", "Distribute drought-resistant seed varieties", "Issue advisory to delay sowing until moisture improves"],
        "confidence": 0.78,
        "acknowledged": False,
        "timestamp": "2026-04-15T05:00:00",
    },
    {
        "id": "alert_005",
        "severity": "MODERATE",
        "sector": "security",
        "alert_type": "security_threat",
        "title": "Border Tension Escalation — Manipur-Myanmar Frontier",
        "description": "Increased militant activity along Manipur-Myanmar border. 3 security incidents in 72 hours near Moreh and Churachandpur. Villages within 10km of border advised to remain vigilant.",
        "affected_regions": ["Manipur", "Churachandpur", "Moreh"],
        "recommended_actions": ["Increase border patrolling frequency", "Coordinate with Assam Rifles for joint ops", "Issue security advisory for border villages"],
        "confidence": 0.74,
        "acknowledged": False,
        "timestamp": "2026-04-14T22:00:00",
    },
    {
        "id": "alert_006",
        "severity": "LOW",
        "sector": "disaster",
        "alert_type": "disaster",
        "title": "Cyclone Watch: Low Pressure — Bay of Bengal",
        "description": "Low pressure system over Bay of Bengal may intensify to a cyclone in 72 hours. Potential impact track covers Odisha and Andhra Pradesh coastlines. IMD monitoring closely.",
        "affected_regions": ["Odisha", "Andhra Pradesh", "Bay of Bengal"],
        "recommended_actions": ["Pre-position NDRF teams at Puri, Visakhapatnam", "Alert coastal fishermen to return to shore", "Activate coastal monitoring stations"],
        "confidence": 0.61,
        "acknowledged": False,
        "timestamp": "2026-04-14T18:00:00",
    },
]

ALERT_ANALYSIS_PROMPT = """You are an early warning analysis system for the Indian government.
Analyze the following multi-sector data and identify ANY potential risks or emerging threats.
Pay special attention to LIVE EVENTS — ongoing protests, wars, pandemics, strikes, civil unrest, and disasters.
Detect escalation patterns, cross-sector impacts, and emerging situations.

Alert types you should detect:
- "protest" — mass gatherings, demonstrations, bandh calls, strikes, farmer protests
- "civil_unrest" — riots, communal tension, mob violence, arson, ethnic clashes
- "security_threat" — terrorist activity, border tensions, militant activity, war-like situations, Naxal activity, ceasefire violations
- "disaster" — floods, earthquakes, cyclones, landslides, dam failures
- "health" — disease outbreaks, epidemics, pandemics, contamination, virus alerts
- "agriculture" — crop failure, drought, food security risks

For each risk found, output a JSON array of alert objects with this structure:
[
  {
    "severity": "CRITICAL" | "HIGH" | "MODERATE" | "LOW",
    "sector": "agriculture" | "disaster" | "health" | "security",
    "alert_type": "protest" | "civil_unrest" | "security_threat" | "disaster" | "health" | "agriculture",
    "title": "Brief alert title",
    "description": "Detailed description of the risk",
    "affected_regions": ["region1", "region2"],
    "recommended_actions": ["action1", "action2"],
    "confidence": 0.0 to 1.0
  }
]

If no risks are detected, return an empty array: []

Be specific with regions, timeframes, and data points. Only flag genuine risks supported by the data.
"""


def run_alert_check() -> list[dict]:
    """
    Run a proactive analysis across all sectors.
    Returns list of new alerts generated.
    """
    # Gather cross-sector data
    analysis_queries = [
        "current weather conditions rainfall forecast flood risk",
        "crop health yield predictions agricultural stress",
        "disease outbreak cases infection trends public health pandemic virus",
        "protest demonstration bandh strike civil unrest communal tension farmer agitation",
        "security threat border tension militant activity law and order war ceasefire naxal",
        "live event escalating active ongoing situation critical alert",
    ]

    all_context = ""
    for q in analysis_queries:
        sector_data = get_all_sectors_context(q)
        all_context += f"\n\n=== Query: {q} ===\n"
        for sector, ctx in sector_data.items():
            all_context += f"\n--- {sector.upper()} ---\n{ctx}\n"

    if "No relevant data" in all_context and all_context.count("No relevant data") >= 3:
        return []

    # Ask LLM to analyze
    messages = [
        {"role": "system", "content": ALERT_ANALYSIS_PROMPT},
        {"role": "user", "content": f"Analyze this data for risks and early warnings:\n{all_context}"},
    ]

    response = chat_completion(messages, temperature=0.2, max_tokens=3000)

    # Parse alerts from response
    new_alerts = _parse_alerts(response)

    # Store alerts
    for alert in new_alerts:
        alert["id"] = f"alert_{int(time.time())}_{len(_alerts)}"
        alert["timestamp"] = datetime.now().isoformat()
        alert["acknowledged"] = False
        _alerts.append(alert)

    return new_alerts


def _parse_alerts(response: str) -> list[dict]:
    """Extract JSON alerts from LLM response."""
    try:
        # Try to find JSON array in response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return []


def get_active_alerts(severity: str = None) -> list[dict]:
    """Get all active (unacknowledged) alerts, optionally filtered by severity."""
    alerts = [a for a in _alerts if not a.get("acknowledged")]
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity.upper()]
    return sorted(alerts, key=lambda a: _severity_order(a.get("severity", "LOW")), reverse=True)


def get_all_alerts() -> list[dict]:
    """Get all alerts including acknowledged ones."""
    return sorted(_alerts, key=lambda a: a.get("timestamp", ""), reverse=True)


def acknowledge_alert(alert_id: str) -> bool:
    """Mark an alert as acknowledged."""
    for alert in _alerts:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            return True
    return False


def translate_alert(alert: dict, target_language: str) -> dict:
    """Translate alert title and description to target language."""
    translated = alert.copy()
    translated["title"] = translate_text(
        alert["title"], source_language="en-IN", target_language=target_language
    )
    translated["description"] = translate_text(
        alert["description"], source_language="en-IN", target_language=target_language
    )
    actions = []
    for action in alert.get("recommended_actions", []):
        actions.append(
            translate_text(action, source_language="en-IN", target_language=target_language)
        )
    translated["recommended_actions"] = actions
    return translated


def _severity_order(severity: str) -> int:
    return {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}.get(severity, 0)

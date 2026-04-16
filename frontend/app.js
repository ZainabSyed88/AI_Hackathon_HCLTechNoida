// =================== State ===================
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let allAlerts = [];
let alertsMap = null;
let fullMap = null;
let sosMap = null;
let selectedAlertId = null;
let chartsInitialized = false;
let notificationLog = [];

// Live Location Tracking State
let liveTrackingActive = false;
let liveTrackingWatchId = null;
let liveTrackingSosId = null;
let liveTrackingTrail = [];
let liveTrackingPolyline = null;
let liveTrackingMarker = null;
let liveTrackingInterval = null;

// Agriculture Dashboard State
let agriLoaded = false;
let agriData = null;

// Health Dashboard State
let healthLoaded = false;
let healthData = null;

// Weather Dashboard State
let weatherLoaded = false;
let weatherData = null;
let wxGeoMap = null;

// Weather Reco Dashboard State
let weatherRecoLoaded = false;

// Incidents Dashboard State
let incidentsLoaded = false;
let allIncidents = [];

const API = "";

// =================== Chart.js Defaults ===================
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
}

// =================== Init ===================
document.addEventListener("DOMContentLoaded", () => {
    setupWeatherDashboardCopy();
    loadAlerts();
    loadLiveEvents();
    loadRAGStats();
    initAlertsMap();
    updateOpsTimestamp();
});

function setupWeatherDashboardCopy() {
    const weatherTab = document.querySelector('[data-dashboard="weather"] .nav-label');
    if (weatherTab) weatherTab.textContent = "Weather";

    const advisoryTab = document.querySelector('[data-dashboard="weather-reco"] .nav-label');
    if (advisoryTab) advisoryTab.textContent = "Advisory";

    const weatherPage = document.getElementById("dashboard-weather");
    if (weatherPage) {
        const weatherTitles = weatherPage.querySelectorAll("h2");
        if (weatherTitles[0]) weatherTitles[0].textContent = "Operational Weather Snapshot";
    }

    const advisoryPage = document.getElementById("dashboard-weather-reco");
    if (advisoryPage) {
        const headerTitle = advisoryPage.querySelector("div[style='margin-bottom:20px;'] h2");
        const headerText = advisoryPage.querySelector("div[style='margin-bottom:20px;'] .muted");
        if (headerTitle) headerTitle.textContent = "Weather Advisory & Impact Desk";
        if (headerText) headerText.textContent = "Action-oriented state advisories, sector impacts, and response guidance for all 28 states and 8 union territories";

        const sectionTitles = advisoryPage.querySelectorAll("h2");
        if (sectionTitles[1]) sectionTitles[1].textContent = "Sector-wise Impact Matrix";
        if (sectionTitles[2]) sectionTitles[2].textContent = "Regional Advisory - Do's & Don'ts";

        const sectionMuted = advisoryPage.querySelectorAll("p.muted");
        if (sectionMuted[1]) sectionMuted[1].textContent = "How current weather patterns affect agriculture, health, infrastructure, and transport across India";
        if (sectionMuted[2]) sectionMuted[2].textContent = "Actionable guidance per region based on current conditions and short-range outlook";
    }
}

function updateOpsTimestamp() {
    const el = document.getElementById("opsLastRefresh");
    if (!el) return;
    el.textContent = new Date().toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// =================== Dashboard Navigation ===================
function switchDashboard(name) {
    // Hide all dashboard pages
    document.querySelectorAll(".dashboard-page").forEach(p => {
        p.classList.remove("active");
        p.style.display = "none";
    });
    // Deactivate all nav items
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    // Show selected
    const page = document.getElementById(`dashboard-${name}`);
    if (page) {
        page.classList.add("active");
        page.style.display = "block";
    }
    const navBtn = document.querySelector(`[data-dashboard="${name}"]`);
    if (navBtn) navBtn.classList.add("active");

    // Lazy-init maps/charts when switching
    if (name === "map-view" && !fullMap) initFullMap();
    if (name === "emergency" && !sosMap) initSOSMap();
    if (name === "analytics" && !chartsInitialized) { initCharts(); chartsInitialized = true; }
    if (name === "agriculture" && !agriLoaded) loadAgricultureDashboard();
    if (name === "health" && !healthLoaded) loadHealthDashboard();
    if (name === "weather" && !weatherLoaded) loadWeatherDashboard();
    if (name === "weather-reco" && !weatherRecoLoaded) loadWeatherReco();
    if (name === "incidents" && !incidentsLoaded) loadIncidentsDashboard();

    // Fix map resize on tab switch
    setTimeout(() => {
        if (name === "alerts" && alertsMap) alertsMap.invalidateSize();
        if (name === "map-view" && fullMap) fullMap.invalidateSize();
        if (name === "emergency" && sosMap) sosMap.invalidateSize();
        if (name === "weather" && wxGeoMap) wxGeoMap.invalidateSize();
    }, 100);
}

// =================== Emergency Keyword Detection ===================
const EMERGENCY_KEYWORDS = [
    "help", "help me", "bachao", "bachaao", "baचाओ", "sos", "emergency",
    "danger", "attack", "attacking", "murder", "killing", "bomb", "fire",
    "kidnap", "abduct", "rape", "assault", "robbery", "theft", "gun", "shoot",
    "stabbing", "bleeding", "dying", "accident", "trapped", "threat",
    "madad", "khatara", "khatre", "khatra", "jaan", "maro", "maaro", "police bulao",
    "ambulance", "call police", "save me", "i am in danger", "under attack",
    "riot", "mob", "violence"
];

function detectEmergency(text) {
    const lower = text.toLowerCase().trim();
    return EMERGENCY_KEYWORDS.some(kw => {
        // Match as whole word or as the full message
        const regex = new RegExp(`(^|\\s|!)${kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}($|\\s|!|\\.|,)`, 'i');
        return regex.test(lower) || lower === kw;
    });
}

function triggerEmergencyFromChat(userText) {
    // Show emergency banner in chat
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message bot-message emergency-chat-alert";
    div.innerHTML = `
        <div style="background:rgba(231,76,60,0.15);border:1px solid var(--red);border-radius:8px;padding:12px;">
            <strong style="color:var(--red);font-size:14px;">🚨 EMERGENCY DETECTED</strong>
            <p style="margin:6px 0 10px;font-size:12px;">Your message "<em>${userText}</em>" indicates a threat or emergency. Initiating emergency protocol:</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="btn btn-siren" style="font-size:12px;padding:6px 12px;" onclick="autoSOS()">🆘 Send SOS + Share Location</button>
                <button class="btn btn-call" style="font-size:12px;padding:6px 12px;" onclick="makeEmergencyCall('police')">👮 Call Police (100)</button>
                <button class="btn btn-call" style="font-size:12px;padding:6px 12px;" onclick="makeEmergencyCall('ambulance')">🚑 Call Ambulance (108)</button>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    // Auto-trigger SOS with location
    autoSOS();
}

function autoSOS() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const { latitude, longitude } = pos.coords;
                try {
                    const res = await fetch(`${API}/api/sos`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ latitude, longitude, timestamp: new Date().toISOString() }),
                    });
                    const data = await res.json();
                    // Start live tracking with the SOS ID
                    if (data.sos_id) {
                        startLiveTracking(data.sos_id, latitude, longitude);
                    }
                    // Also send notification to police channel
                    await fetch(`${API}/api/notify`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            channel: "call",
                            message: `EMERGENCY SOS — Citizen in danger at location ${latitude.toFixed(4)}, ${longitude.toFixed(4)}. Live tracking enabled. Immediate police response required.`,
                            regions: ["Current Location"],
                        }),
                    });
                } catch {}
                addMessage(
                    `🚨 SOS ACTIVATED — LIVE TRACKING ON\n📍 Location: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}\n📡 Your location is being shared in real-time\n👮 Police (100) notified\n🚑 Ambulance (108) notified\n\nStay calm. Help is on the way.`,
                    "bot"
                );
            },
            () => {
                addMessage("⚠️ Location access denied. Please call Police: 100 or Ambulance: 108 directly.", "bot");
            },
            { enableHighAccuracy: true }
        );
    } else {
        addMessage("⚠️ Geolocation not available. Please call Police: 100 or Ambulance: 108 directly.", "bot");
    }
}

// =================== Live Location Tracking ===================
function startLiveTracking(sosId, initialLat, initialLng) {
    if (liveTrackingActive) return; // Already tracking

    liveTrackingActive = true;
    liveTrackingSosId = sosId;
    liveTrackingTrail = [{ lat: initialLat, lng: initialLng, time: new Date().toISOString() }];

    // Show tracking indicator
    updateTrackingUI(true, initialLat, initialLng);

    // Add initial marker to SOS map
    if (sosMap) {
        addTrackingMarkerToMap(initialLat, initialLng);
    }

    // Start watching position continuously
    if (navigator.geolocation) {
        liveTrackingWatchId = navigator.geolocation.watchPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                onLiveLocationUpdate(latitude, longitude);
            },
            (err) => {
                console.warn("Live tracking GPS error:", err.message);
            },
            { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
        );
    }

    // Also send location to server every 10 seconds
    liveTrackingInterval = setInterval(() => {
        if (liveTrackingTrail.length > 0) {
            const last = liveTrackingTrail[liveTrackingTrail.length - 1];
            sendLocationToServer(last.lat, last.lng);
        }
    }, 10000);
}

function onLiveLocationUpdate(lat, lng) {
    const point = { lat, lng, time: new Date().toISOString() };
    liveTrackingTrail.push(point);

    // Update marker position on map
    if (sosMap && liveTrackingMarker) {
        liveTrackingMarker.setLatLng([lat, lng]);
        sosMap.panTo([lat, lng]);
    }

    // Update polyline trail on map
    if (sosMap && liveTrackingPolyline) {
        liveTrackingPolyline.addLatLng([lat, lng]);
    } else if (sosMap && liveTrackingTrail.length >= 2) {
        const latlngs = liveTrackingTrail.map(p => [p.lat, p.lng]);
        liveTrackingPolyline = L.polyline(latlngs, {
            color: '#e74c3c', weight: 3, opacity: 0.8, dashArray: '10 6',
        }).addTo(sosMap);
    }

    // Update tracking UI
    updateTrackingUI(true, lat, lng);
}

async function sendLocationToServer(lat, lng) {
    if (!liveTrackingSosId) return;
    try {
        await fetch(`${API}/api/sos/location`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sos_id: liveTrackingSosId,
                latitude: lat,
                longitude: lng,
                timestamp: new Date().toISOString(),
            }),
        });
    } catch {}
}

function addTrackingMarkerToMap(lat, lng) {
    if (!sosMap) return;
    const icon = L.divIcon({
        html: `<div class="live-tracking-dot"></div>`,
        iconSize: [20, 20],
        className: '',
    });
    liveTrackingMarker = L.marker([lat, lng], { icon }).addTo(sosMap)
        .bindPopup(`<strong>📡 Live Tracking</strong><br>SOS ID: ${liveTrackingSosId}<br>Status: Tracking Active`);
    sosMap.setView([lat, lng], 14);
}

async function stopLiveTracking() {
    if (!liveTrackingActive) return;

    // Stop watching GPS
    if (liveTrackingWatchId !== null) {
        navigator.geolocation.clearWatch(liveTrackingWatchId);
        liveTrackingWatchId = null;
    }

    // Stop server updates
    if (liveTrackingInterval) {
        clearInterval(liveTrackingInterval);
        liveTrackingInterval = null;
    }

    // Tell server to stop tracking
    if (liveTrackingSosId) {
        try {
            await fetch(`${API}/api/sos/${liveTrackingSosId}/stop`, { method: "POST" });
        } catch {}
    }

    liveTrackingActive = false;
    updateTrackingUI(false);
    addMessage("📡 Live location tracking stopped. Your location is no longer being shared.", "bot");

    // Reset state
    liveTrackingSosId = null;
    liveTrackingTrail = [];
    liveTrackingPolyline = null;
    liveTrackingMarker = null;
}

function updateTrackingUI(active, lat, lng) {
    const indicator = document.getElementById("trackingIndicator");
    const coordsEl = document.getElementById("trackingCoords");
    const pointsEl = document.getElementById("trackingPoints");
    const durationEl = document.getElementById("trackingDuration");

    if (!indicator) return;

    if (active) {
        indicator.classList.remove("hidden");
        if (coordsEl && lat !== undefined) coordsEl.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
        if (pointsEl) pointsEl.textContent = liveTrackingTrail.length;
        if (durationEl && liveTrackingTrail.length > 0) {
            const start = new Date(liveTrackingTrail[0].time);
            const now = new Date();
            const secs = Math.floor((now - start) / 1000);
            const mins = Math.floor(secs / 60);
            const sec = secs % 60;
            durationEl.textContent = `${mins}m ${sec}s`;
        }
    } else {
        indicator.classList.add("hidden");
    }
}

// =================== Text Query ===================
async function sendTextQuery() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    const lang = document.getElementById("languageSelect").value;

    addMessage(text, "user");
    input.value = "";

    // Check for emergency keywords FIRST
    if (detectEmergency(text)) {
        triggerEmergencyFromChat(text);
        return; // Skip normal query — prioritize emergency
    }

    addMessage("Thinking...", "bot", "thinkingMsg");

    try {
        const res = await fetch(`${API}/api/text-query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, language_code: lang }),
        });
        const data = await res.json();
        removeMessage("thinkingMsg");

        const display = lang === "en-IN" ? data.response_english : data.response_translated;
        addMessage(display, "bot");

        // Check if LLM response indicates emergency
        if (data.emergency_detected) {
            triggerEmergencyFromChat(text);
        } else if (data.sector) {
            addMessage(`📌 Sector: ${data.sector}`, "bot");
        }
    } catch (err) {
        removeMessage("thinkingMsg");
        addMessage("Error: Could not reach the server. Is the backend running?", "bot");
    }
}

// =================== Voice Query ===================
async function toggleVoiceRecording() {
    const btn = document.getElementById("voiceBtn");
    const status = document.getElementById("voiceStatus");

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            audioChunks = [];

            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = () => sendVoiceQuery();

            mediaRecorder.start();
            isRecording = true;
            btn.classList.add("recording");
            btn.textContent = "⏹";
            status.textContent = "🔴 Recording... Click stop when done.";
            status.classList.remove("hidden");
        } catch (err) {
            if (!navigator.mediaDevices || !window.isSecureContext) {
                addMessage("🎤 Microphone unavailable on non-secure connection.\n\n✅ Fix: Open the app at:\n   http://localhost:8000\n   (not via IP address)\n\nThen try the mic again.", "bot");
            } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                addMessage("🎤 Microphone permission denied.\n\nTo fix:\n1. Click the 🔒 lock icon in your browser address bar\n2. Set Microphone → Allow\n3. Refresh the page and try again.", "bot");
            } else {
                addMessage(`🎤 Microphone error: ${err.message}`, "bot");
            }
        }
    } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach((t) => t.stop());
        isRecording = false;
        btn.classList.remove("recording");
        btn.textContent = "🎤";
        status.textContent = "Processing voice...";
    }
}

async function sendVoiceQuery() {
    const status = document.getElementById("voiceStatus");
    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");
    
    const selectedLanguage = document.getElementById("languageSelect")?.value || "auto";
    formData.append("language_code", selectedLanguage);

    addMessage("🎤 [Voice message sent]", "user");
    addMessage("🔄 Processing voice (STT → RAG → LLM → TTS)...", "bot", "thinkingMsg");
    status.textContent = "🔄 Processing voice...";

    try {
        // Create a timeout promise (30 seconds)
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Voice processing timeout: Server took >30 seconds")), 30000)
        );
        
        const fetchPromise = fetch(`${API}/api/voice-query`, {
            method: "POST",
            body: formData,
        });
        
        const res = await Promise.race([fetchPromise, timeoutPromise]);
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: "Unknown error" }));
            throw new Error(errorData.detail || `Server error: ${res.status}`);
        }
        
        const data = await res.json();
        removeMessage("thinkingMsg");

        console.log("Voice response:", {
            user_text: data.user_text,
            detected_language: data.detected_language,
            response_length: data.response_translated?.length || 0,
            audio_generated: !!data.response_audio_base64
        });

        // Check if voice input was an emergency
        if (detectEmergency(data.user_text) || detectEmergency(data.user_text_english || "") || data.emergency_detected) {
            triggerEmergencyFromChat(data.user_text);
            status.classList.add("hidden");
            return;
        }

        // Show what user said
        addMessage(`🎤 You (${data.detected_language}): "${data.user_text}"`, "user");

        // Show AI response text
        if (data.response_translated) {
            addMessage(`🤖 Response:\n\n${data.response_translated}`, "bot");
        } else if (data.response_english) {
            addMessage(`🤖 Response:\n\n${data.response_english}`, "bot");
        }

        // Play audio response if available
        if (data.response_audio_base64) {
            status.textContent = "🔊 Playing audio response...";
            playAudio(data.response_audio_base64);
            setTimeout(() => {
                status.textContent = "✅ Voice response ready";
                setTimeout(() => status.classList.add("hidden"), 2000);
            }, 1000);
        } else {
            status.textContent = "⚠️ No audio response (check Sarvam API key)";
            addMessage("⚠️ Audio response not available. Check if SARVAM_API_KEY is configured.", "bot");
        }

    } catch (error) {
        removeMessage("thinkingMsg");
        let errorMsg = error.message;
        
        // Better error messages
        if (errorMsg.includes("Failed to fetch")) {
            errorMsg = "❌ Server connection failed. Is FastAPI running on http://localhost:8000?";
        } else if (errorMsg.includes("timeout")) {
            errorMsg = "❌ Voice processing timeout (>30 seconds). Check Sarvam API key and network.";
        } else if (errorMsg.includes("not configured")) {
            errorMsg = "❌ SARVAM_API_KEY not configured.\n\n👉 Setup: Create .env file with:\nSARVAM_API_KEY=your_key\n\nThen restart server.";
        }
        
        console.error("Voice query error:", error);
        addMessage(errorMsg, "bot");
        status.textContent = "❌ Voice processing failed";
        status.classList.remove("hidden");
    }
}

        status.classList.add("hidden");
    } catch (err) {
        removeMessage("thinkingMsg");
        console.error("Voice query error:", err);
        
        let errorMsg = "Error: Could not process voice query.";
        if (err.message.includes("timeout")) {
            errorMsg = "Error: Request timeout. Server is not responding. Please try again.";
        } else if (err.message.includes("Network")) {
            errorMsg = "Error: Network error. Please check your connection.";
        } else if (err.message) {
            errorMsg = "Error: " + err.message;
        }
        
        addMessage(errorMsg, "bot");
        status.classList.add("hidden");
    }
}

function playAudio(base64Audio) {
    if (!base64Audio || base64Audio.length === 0) {
        console.warn("⚠️ Empty audio data - cannot play");
        return;
    }
    
    try {
        // Decode base64 audio
        const bytes = atob(base64Audio);
        const arr = new Uint8Array(bytes.length);
        for (let i = 0; i < bytes.length; i++) {
            arr[i] = bytes.charCodeAt(i);
        }
        
        // Create blob and play
        const blob = new Blob([arr], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        
        audio.onplay = () => console.log("🔊 Audio playback started");
        audio.onended = () => console.log("✅ Audio playback ended");
        audio.onerror = (e) => console.error("❌ Audio playback error:", e);
        
        audio.play().catch(e => {
            console.error("❌ Audio play error:", e.message);
            addMessage(`⚠️ Audio playback blocked: ${e.message}`, "bot");
        });
    } catch (e) {
        console.error("❌ Audio decode error:", e);
        addMessage(`⚠️ Could not decode audio: ${e.message}`, "bot");
    }
}

// =================== Chat UI Helpers ===================
function addMessage(text, role, id = null) {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = `message ${role === "user" ? "user-message" : "bot-message"}`;
    if (id) div.id = id;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// =================== Alerts ===================
async function loadAlerts() {
    try {
        const res = await fetch(`${API}/api/alerts`);
        const data = await res.json();
        allAlerts = data.alerts || [];
        renderAlerts(allAlerts);
        updateAlertStats(allAlerts);
        updateAlertsMapMarkers(allAlerts);
    } catch {
        document.getElementById("alertsList").innerHTML =
            '<p class="muted">Could not load alerts.</p>';
    }
}

function updateAlertStats(alerts) {
    const counts = { CRITICAL: 0, HIGH: 0, MODERATE: 0, LOW: 0 };
    alerts.forEach(a => {
        const sev = (a.severity || "LOW").toUpperCase();
        if (counts[sev] !== undefined) counts[sev]++;
    });
    document.getElementById("criticalCount").textContent = counts.CRITICAL;
    document.getElementById("highCount").textContent = counts.HIGH;
    document.getElementById("moderateCount").textContent = counts.MODERATE;
    document.getElementById("lowCount").textContent = counts.LOW;
    document.getElementById("totalAlertCount").textContent = alerts.length;
    const shellAlert = document.getElementById("shellAlertCount");
    const shellCritical = document.getElementById("shellCriticalCount");
    if (shellAlert) shellAlert.textContent = alerts.length;
    if (shellCritical) shellCritical.textContent = counts.CRITICAL;
    updateOpsTimestamp();
}

function filterAlerts() {
    const typeFilter = document.getElementById("alertTypeFilter").value;
    const sevFilter = document.getElementById("alertSeverityFilter").value;

    let filtered = allAlerts;
    if (typeFilter !== "all") {
        filtered = filtered.filter(a => (a.alert_type || a.sector || "").toLowerCase() === typeFilter);
    }
    if (sevFilter !== "all") {
        filtered = filtered.filter(a => (a.severity || "").toUpperCase() === sevFilter);
    }
    renderAlerts(filtered);
}

function renderAlerts(alerts) {
    const container = document.getElementById("alertsList");

    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="muted">No active alerts. System is monitoring.</p>';
        return;
    }

    container.innerHTML = alerts
        .map(a => `
        <div class="alert-item ${(a.severity || "low").toLowerCase()}" onclick="showAlertDetail('${a.id}')">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <span class="alert-title">${a.title || "Alert"}</span>
                <div style="display:flex;gap:4px;align-items:center;flex-shrink:0;">
                    ${a.alert_type ? `<span class="alert-type-badge">${a.alert_type}</span>` : ''}
                    <span class="severity-badge ${(a.severity || "low").toLowerCase()}">${a.severity || "LOW"}</span>
                </div>
            </div>
            <div class="alert-meta">
                <span>📍 ${(a.affected_regions || []).join(", ") || "Unknown"}</span>
                <span>🏷️ ${a.sector || "General"}</span>
                ${a.timestamp ? `<span>🕐 ${new Date(a.timestamp).toLocaleTimeString()}</span>` : ''}
            </div>
        </div>
    `).join("");
}

function showAlertDetail(alertId) {
    const alert = allAlerts.find(a => a.id === alertId);
    if (!alert) return;
    selectedAlertId = alertId;

    document.getElementById("modalAlertTitle").textContent = alert.title || "Alert Details";
    document.getElementById("modalAlertBody").innerHTML = `
        <div class="detail-row">
            <div class="detail-label">Severity</div>
            <div class="detail-value"><span class="severity-badge ${(alert.severity || 'low').toLowerCase()}">${alert.severity}</span></div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Type</div>
            <div class="detail-value">${alert.alert_type || alert.sector || 'General'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Description</div>
            <div class="detail-value">${alert.description || 'No description available.'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Affected Regions</div>
            <div class="detail-value">${(alert.affected_regions || []).join(", ") || "Unknown"}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Confidence</div>
            <div class="detail-value">${alert.confidence ? (alert.confidence * 100).toFixed(0) + '%' : 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Recommended Actions</div>
            <div class="detail-value">
                ${(alert.recommended_actions || []).map(a => `• ${a}`).join('<br>') || 'None specified'}
            </div>
        </div>
        ${alert.timestamp ? `
        <div class="detail-row">
            <div class="detail-label">Time</div>
            <div class="detail-value">${new Date(alert.timestamp).toLocaleString()}</div>
        </div>` : ''}
    `;
    document.getElementById("alertDetailModal").classList.remove("hidden");
}

function closeAlertModal() {
    document.getElementById("alertDetailModal").classList.add("hidden");
    selectedAlertId = null;
}

async function acknowledgeAlertFromModal() {
    if (!selectedAlertId) return;
    try {
        await fetch(`${API}/api/alerts/acknowledge`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ alert_id: selectedAlertId }),
        });
        closeAlertModal();
        loadAlerts();
    } catch {
        alert("Failed to acknowledge alert.");
    }
}

function notifyFromModal(channel) {
    sendEmergencyNotification(channel, selectedAlertId);
}

async function runAlertCheck() {
    try {
        const btn = document.querySelector('.alerts-left .btn-primary');
        if (btn) { btn.disabled = true; btn.textContent = "⏳ Scanning..."; }

        const res = await fetch(`${API}/api/alerts/check`, { method: "POST" });
        const data = await res.json();
        loadAlerts();

        if (btn) { btn.disabled = false; btn.textContent = "🔄 Scan Now"; }
    } catch {
        const btn = document.querySelector('.alerts-left .btn-primary');
        if (btn) { btn.disabled = false; btn.textContent = "🔄 Scan Now"; }
    }
}

// =================== LIVE EVENTS INTELLIGENCE ===================
let allLiveEvents = [];

async function loadLiveEvents() {
    try {
        const res = await fetch(`${API}/api/live-events`);
        const data = await res.json();
        allLiveEvents = data.events || [];
        renderLiveEventsStats(data.stats);
        renderLiveEventsFeed(allLiveEvents);
    } catch (e) {
        console.error("Failed to load live events:", e);
        document.getElementById("liveEventsFeed").innerHTML = '<p class="muted">Failed to load live events feed.</p>';
    }
}

function renderLiveEventsStats(stats) {
    if (!stats) return;
    document.getElementById("leStatTotal").textContent = stats.active || 0;
    document.getElementById("leStatCritical").textContent = stats.critical || 0;
    document.getElementById("leStatEscalating").textContent = stats.escalating || 0;
    document.getElementById("leStatProtests").textContent = (stats.by_type?.protest || 0);
    document.getElementById("leStatSecurity").textContent =
        (stats.by_type?.war || 0) + (stats.by_type?.naxal || 0) + (stats.by_type?.civil_unrest || 0);
    document.getElementById("leStatHealth").textContent = (stats.by_type?.pandemic || 0);
    const shellLive = document.getElementById("shellLiveCount");
    const shellHealth = document.getElementById("shellHealthCount");
    if (shellLive) shellLive.textContent = stats.active || 0;
    if (shellHealth) shellHealth.textContent = stats.by_type?.pandemic || 0;
    updateOpsTimestamp();
}

function renderLiveEventsFeed(events) {
    const container = document.getElementById("liveEventsFeed");
    if (!events || events.length === 0) {
        container.innerHTML = '<p class="muted">No live events tracked.</p>';
        return;
    }
    const typeIcons = {
        protest: "✊", war: "⚔️", pandemic: "🦠", civil_unrest: "🔥",
        strike: "🚛", disaster: "🌊", naxal: "🎯", other: "📌"
    };
    const escColors = {
        escalating: "#ef4444", stable: "#facc15", monitoring: "#3b82f6", "de-escalating": "#22c55e"
    };
    container.innerHTML = events.map(ev => {
        const icon = typeIcons[ev.type] || "📌";
        const escColor = escColors[ev.escalation] || "#94a3b8";
        const sevClass = ev.severity.toLowerCase();
        const updated = new Date(ev.last_updated).toLocaleString("en-IN", {
            day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
        });
        const timelineHtml = (ev.timeline || []).slice(-4).map(t =>
            `<div class="le-timeline-item"><span class="le-tl-date">${t.date}</span> ${t.event}</div>`
        ).join("");
        const factsHtml = (ev.key_facts || []).slice(0, 5).map(f =>
            `<li>${f}</li>`
        ).join("");
        const tagsHtml = (ev.tags || []).map(tag =>
            `<span class="le-tag">${tag}</span>`
        ).join("");
        const impactHtml = ev.impact ? `
            <div class="le-impact">
                <span>👥 ${ev.impact.people_affected || "N/A"}</span>
                <span>💰 ${ev.impact.economic_loss || "N/A"}</span>
            </div>` : "";

        return `
        <div class="le-card le-card-${sevClass}">
            <div class="le-card-top">
                <div class="le-card-title-row">
                    <span class="le-type-icon">${icon}</span>
                    <div>
                        <h3 class="le-title">${ev.title}</h3>
                        <div class="le-meta">
                            <span class="le-badge le-sev-${sevClass}">${ev.severity}</span>
                            <span class="le-esc-badge" style="color:${escColor};border-color:${escColor}">▲ ${ev.escalation}</span>
                            <span>📍 ${ev.region}</span>
                            <span>🕐 Updated: ${updated}</span>
                            <span class="le-source">📰 ${ev.source}</span>
                        </div>
                    </div>
                </div>
                <span class="le-event-id">${ev.id}</span>
            </div>
            <p class="le-summary">${ev.summary}</p>
            <div class="le-details-grid">
                <div class="le-facts-col">
                    <strong>Key Facts</strong>
                    <ul class="le-facts">${factsHtml}</ul>
                    ${impactHtml}
                </div>
                <div class="le-timeline-col">
                    <strong>Timeline</strong>
                    <div class="le-timeline">${timelineHtml}</div>
                </div>
            </div>
            <div class="le-footer">
                <div class="le-tags">${tagsHtml}</div>
                <div class="le-affected">📍 ${(ev.affected_areas || []).join(", ")}</div>
            </div>
            ${ev.govt_response ? `<div class="le-govt">🏛️ <strong>Govt Response:</strong> ${ev.govt_response}</div>` : ""}
        </div>`;
    }).join("");
}

function filterLiveEvents() {
    const typeVal = document.getElementById("liveEvtTypeFilter").value;
    const sevVal = document.getElementById("liveEvtSeverityFilter").value;
    let filtered = allLiveEvents;
    if (typeVal !== "all") filtered = filtered.filter(e => e.type === typeVal);
    if (sevVal !== "all") filtered = filtered.filter(e => e.severity === sevVal);
    renderLiveEventsFeed(filtered);
}

// =================== Emergency Notifications ===================
async function sendEmergencyNotification(channel, alertId = null) {
    const targetAlert = alertId ? allAlerts.find(a => a.id === alertId) : null;
    const message = targetAlert
        ? `[${targetAlert.severity}] ${targetAlert.title} — Regions: ${(targetAlert.affected_regions || []).join(', ')}`
        : "General emergency notification triggered.";
    const regions = targetAlert ? (targetAlert.affected_regions || []) : ["All Regions"];

    try {
        const res = await fetch(`${API}/api/notify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                channel,
                message,
                regions,
                alert_id: alertId,
            }),
        });
        const data = await res.json();
        addNotificationLog(channel, message, data.status || "sent");
    } catch {
        // Backend not available — log locally
        addNotificationLog(channel, message, "queued (offline)");
    }
}

function addNotificationLog(channel, message, status) {
    const channelIcons = { sms: "📱", whatsapp: "💬", call: "📞", all: "🚨" };
    const channelNames = { sms: "SMS", whatsapp: "WhatsApp", call: "Call", all: "All Channels" };

    notificationLog.unshift({
        channel,
        message,
        status,
        time: new Date().toLocaleTimeString(),
    });

    const container = document.getElementById("notificationLog");
    container.innerHTML = notificationLog.slice(0, 20).map(n => `
        <div class="notif-item">
            <span class="notif-channel">${channelIcons[n.channel] || "📢"} ${channelNames[n.channel] || n.channel}</span>
            <span style="flex:1;margin:0 8px;font-size:11px;color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${n.message}</span>
            <span class="notif-time">${n.status} · ${n.time}</span>
        </div>
    `).join("");
}

// =================== SOS / Emergency ===================
function triggerSOS() {
    if (liveTrackingActive) {
        if (confirm("Live tracking is already active. Do you want to stop tracking?")) {
            stopLiveTracking();
        }
        return;
    }

    if (!confirm("This will share your LIVE location continuously and alert Police + Ambulance. Continue?")) return;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const { latitude, longitude } = pos.coords;
                try {
                    const res = await fetch(`${API}/api/sos`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ latitude, longitude, timestamp: new Date().toISOString() }),
                    });
                    const data = await res.json();
                    if (data.sos_id) {
                        startLiveTracking(data.sos_id, latitude, longitude);
                    }
                } catch {}
                alert(`SOS Triggered! Live Tracking Active!\nLocation: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}\nPolice (100) and Ambulance (108) have been notified.\nYour location is being shared continuously.`);
                addSOSToMap(latitude, longitude);
            },
            () => alert("Location access denied. Please enable location services."),
            { enableHighAccuracy: true }
        );
    } else {
        alert("Geolocation not supported by your browser.");
    }
}

function addSOSToMap(lat, lng) {
    if (!sosMap) return;
    const icon = L.divIcon({
        html: '<div style="background:red;width:16px;height:16px;border-radius:50%;border:3px solid white;animation:pulse 1.5s infinite;"></div>',
        iconSize: [16, 16],
        className: '',
    });
    L.marker([lat, lng], { icon }).addTo(sosMap)
        .bindPopup(`<strong>SOS Alert</strong><br>Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>Time: ${new Date().toLocaleTimeString()}`);
}

function makeEmergencyCall(service) {
    const numbers = { police: "100", ambulance: "108", fire: "101", disaster: "1078", women: "1091", child: "1098" };
    const num = numbers[service];
    if (num) {
        alert(`Dialing ${service.toUpperCase()}: ${num}\n(In production, this would initiate a call via the device telephony API)`);
    }
}

// =================== RAG Stats ===================
async function loadRAGStats() {
    try {
        const res = await fetch(`${API}/api/rag/stats`);
        const data = await res.json();
        const totalDocs = data.total_documents || 0;
        document.getElementById("totalDocs").textContent = totalDocs;
        // Update Intelligence Repository section
        const ku = document.getElementById("intelKnowledgeUnits");
        if (ku) ku.textContent = totalDocs;
        const aq = document.getElementById("intelActiveQueries");
        if (aq) aq.textContent = '0';
    } catch {
        document.getElementById("totalDocs").textContent = "--";
    }
}

// =================== Maps ===================
const colorIcons = {
    red: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    orange: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
    yellow: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png",
    green: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
};

const severityColors = { CRITICAL: "red", HIGH: "orange", MODERATE: "yellow", LOW: "green" };

const regionCoordinates = {
    "assam": [26.14, 91.73], "maharashtra": [19.07, 72.87], "vidarbha": [20.59, 78.96],
    "uttarakhand": [30.33, 78.74], "chennai": [13.08, 80.27], "bihar": [25.61, 85.14],
    "uttar pradesh": [26.76, 80.95], "punjab": [30.73, 76.78], "kerala": [10.85, 76.27],
    "andhra pradesh": [15.91, 79.74], "tamil nadu": [11.13, 78.66], "west bengal": [22.99, 87.75],
    "rajasthan": [27.02, 74.22], "gujarat": [22.31, 72.14], "madhya pradesh": [23.47, 77.95],
    "odisha": [20.94, 84.80], "karnataka": [15.32, 75.71], "delhi": [28.61, 77.21],
    "jammu and kashmir": [33.78, 76.58], "manipur": [24.82, 93.95], "nagaland": [26.16, 94.56],
    "jharkhand": [23.61, 85.28], "chhattisgarh": [21.27, 81.87], "goa": [15.30, 74.08],
    "telangana": [17.12, 79.02], "haryana": [29.06, 76.09], "pune": [18.52, 73.86],
    "mumbai": [19.08, 72.88], "kolkata": [22.57, 88.36], "bengaluru": [12.97, 77.59],
    "hyderabad": [17.39, 78.49], "jaipur": [26.91, 75.79], "lucknow": [26.85, 80.95],
    "gorakhpur": [26.76, 83.37], "kutch": [23.24, 69.67],
};

function getCoordForRegion(regionName) {
    const lower = regionName.toLowerCase().trim();
    for (const [key, coords] of Object.entries(regionCoordinates)) {
        if (lower.includes(key) || key.includes(lower)) return coords;
    }
    // Fallback: center India with some random offset
    return [22.5 + (Math.random() - 0.5) * 4, 80 + (Math.random() - 0.5) * 4];
}

function createMapInstance(elementId) {
    const map = L.map(elementId).setView([22.5, 80], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap",
        maxZoom: 18,
    }).addTo(map);
    return map;
}

let alertsMapMarkers = [];

function initAlertsMap() {
    alertsMap = createMapInstance("alertsMap");

    // Add static risk markers
    const staticMarkers = [
        { lat: 26.14, lng: 91.73, title: "Assam — Flood Risk", color: "red", info: "Brahmaputra at 49.2m" },
        { lat: 19.07, lng: 72.87, title: "Maharashtra — Dengue Hotspot", color: "orange", info: "8,500 cases" },
        { lat: 20.59, lng: 78.96, title: "Vidarbha — Crop Stress", color: "yellow", info: "30% below-normal rainfall" },
        { lat: 30.33, lng: 78.74, title: "Uttarakhand — Landslide Risk", color: "red", info: "17 vulnerable zones" },
        { lat: 13.08, lng: 80.27, title: "Chennai — Flood Preparedness", color: "orange", info: "200mm+ forecast" },
        { lat: 25.61, lng: 85.14, title: "Bihar — Cholera Alert", color: "red", info: "340 cases" },
        { lat: 26.76, lng: 83.37, title: "UP — Japanese Encephalitis", color: "orange", info: "180 cases" },
    ];

    staticMarkers.forEach(m => {
        const icon = L.icon({
            iconUrl: colorIcons[m.color], iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
            shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        });
        L.marker([m.lat, m.lng], { icon }).addTo(alertsMap)
            .bindPopup(`<strong>${m.title}</strong><br>${m.info}`);
    });
}

function updateAlertsMapMarkers(alerts) {
    if (!alertsMap) return;
    // Remove previous dynamic markers
    alertsMapMarkers.forEach(m => alertsMap.removeLayer(m));
    alertsMapMarkers = [];

    alerts.forEach(a => {
        const color = severityColors[(a.severity || "LOW").toUpperCase()] || "yellow";
        (a.affected_regions || []).forEach(region => {
            const coords = getCoordForRegion(region);
            const icon = L.icon({
                iconUrl: colorIcons[color], iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
                shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
            });
            const marker = L.marker(coords, { icon }).addTo(alertsMap)
                .bindPopup(`<strong>${a.title}</strong><br>📍 ${region}<br>⚠️ ${a.severity}<br>${a.description || ''}`);
            alertsMapMarkers.push(marker);
        });
    });
}

function initFullMap() {
    fullMap = createMapInstance("fullMap");
    // Copy all markers from alerts map data
    const staticMarkers = [
        { lat: 26.14, lng: 91.73, title: "Assam — Flood Risk", color: "red", info: "Brahmaputra at 49.2m, danger mark 49.68m" },
        { lat: 19.07, lng: 72.87, title: "Maharashtra — Dengue Hotspot", color: "orange", info: "8,500 cases, Pune highest" },
        { lat: 20.59, lng: 78.96, title: "Vidarbha — Crop Stress", color: "yellow", info: "30% below-normal rainfall" },
        { lat: 30.33, lng: 78.74, title: "Uttarakhand — Landslide Risk", color: "red", info: "17 vulnerable zones on Char Dham route" },
        { lat: 13.08, lng: 80.27, title: "Chennai — Flood Preparedness", color: "orange", info: "200mm+ rainfall forecast" },
        { lat: 25.61, lng: 85.14, title: "Bihar — Cholera Alert", color: "red", info: "340 cases, contaminated water" },
        { lat: 26.76, lng: 83.37, title: "UP — Japanese Encephalitis", color: "orange", info: "180 suspected cases, Gorakhpur" },
    ];
    staticMarkers.forEach(m => {
        const icon = L.icon({
            iconUrl: colorIcons[m.color], iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
            shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        });
        L.marker([m.lat, m.lng], { icon }).addTo(fullMap)
            .bindPopup(`<strong>${m.title}</strong><br>${m.info}`);
    });
}

function initSOSMap() {
    sosMap = createMapInstance("sosMap");
    // Load existing SOS requests and display on map
    loadSOSRequests();
}

async function loadSOSRequests() {
    try {
        const res = await fetch(`${API}/api/sos`);
        const data = await res.json();
        const requests = data.sos_requests || [];

        // Show on map
        requests.forEach(sos => {
            const isTracking = sos.tracking;
            const icon = L.divIcon({
                html: `<div class="${isTracking ? 'live-tracking-dot' : 'sos-static-dot'}"></div>`,
                iconSize: [16, 16],
                className: '',
            });
            if (sosMap) {
                L.marker([sos.latitude, sos.longitude], { icon }).addTo(sosMap)
                    .bindPopup(`<strong>${isTracking ? '📡 Live Tracking' : '🆘 SOS Alert'}</strong><br>ID: ${sos.id}<br>📍 ${sos.latitude.toFixed(4)}, ${sos.longitude.toFixed(4)}<br>🕐 ${new Date(sos.timestamp).toLocaleTimeString()}`);

                // Draw trail if exists
                if (sos.location_trail && sos.location_trail.length > 1) {
                    const latlngs = sos.location_trail.map(p => [p.latitude, p.longitude]);
                    L.polyline(latlngs, {
                        color: isTracking ? '#e74c3c' : '#e67e22',
                        weight: 2, opacity: 0.7, dashArray: '8 5',
                    }).addTo(sosMap);
                }
            }
        });

        // Update SOS requests list
        const container = document.getElementById("sosRequests");
        if (!container) return;
        if (requests.length === 0) {
            container.innerHTML = '<p class="muted">No active SOS requests.</p>';
            return;
        }
        container.innerHTML = requests.map(s => `
            <div class="sos-item">
                <div class="sos-info">
                    <strong>${s.tracking ? '📡' : '🔴'} ${s.id}</strong><br>
                    📍 ${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}
                    ${s.tracking ? '<span class="tracking-badge">LIVE</span>' : ''}
                    ${s.location_trail ? `<span class="trail-count">${s.location_trail.length} points</span>` : ''}
                </div>
                <div class="sos-time">${new Date(s.timestamp).toLocaleTimeString()}</div>
            </div>
        `).join("");
    } catch {
        const container = document.getElementById("sosRequests");
        if (container) container.innerHTML = '<p class="muted">Could not load SOS requests.</p>';
    }
}

// =================== Analytics Intelligence ===================
async function initCharts() {
    try {
        const res = await fetch(`${API}/api/analytics`);
        const d = await res.json();
        renderAnalyticsDashboard(d);
    } catch(e) {
        console.error('Analytics load error:', e);
    }
}

function renderAnalyticsDashboard(d) {
    const s = d.summary;
    const cOpts = {responsive:true, maintainAspectRatio:false};
    const darkGrid = 'rgba(255,255,255,0.04)';
    const tickColor = '#94a3b8';
    const legendLabels = {color:'#94a3b8', font:{size:10, family:'Inter'}, padding:12};

    // ── Summary Stats Bar ──
    const statsBar = document.getElementById('anStatsBar');
    if(statsBar) statsBar.innerHTML = [
        {v:s.total_incidents.toLocaleString(), l:'Total Incidents', c:'#60a5fa'},
        {v:s.active_alerts, l:'Active Alerts', c:'#f87171'},
        {v:s.risk_zones, l:'Risk Zones', c:'#fb923c'},
        {v:s.data_sources, l:'Data Sources', c:'#4ade80'},
        {v:s.confidence_index+'%', l:'AI Confidence', c:'#a78bfa'},
        {v:d.disaster_management.lives_saved.toLocaleString(), l:'Lives Saved', c:'#2dd4bf'}
    ].map(x=>`<div class="an-stat-card"><span class="an-stat-val" style="color:${x.c}">${x.v}</span><span class="an-stat-lbl">${x.l}</span></div>`).join('');

    // ── Predictive Alerts Ticker ──
    const ticker = document.getElementById('anAlertsTicker');
    if(ticker) ticker.innerHTML = d.predictive_alerts.map(a=>{
        const sc = a.severity==='critical'?'#f87171':a.severity==='high'?'#fb923c':'#facc15';
        return `<div class="an-alert-pill" style="border-color:${sc}">
            <span class="an-alert-sev" style="background:${sc}">${a.severity.toUpperCase()}</span>
            <span class="an-alert-type">${a.type}</span>
            <span class="an-alert-region">${a.region}</span>
            <span class="an-alert-prob">${a.probability}%</span>
            <span class="an-alert-time">${a.timeframe}</span>
        </div>`;
    }).join('');

    // ── Disaster Stats Summary ──
    const dm = d.disaster_management;
    const dStats = document.getElementById('anDisasterStats');
    if(dStats) dStats.innerHTML = `
        <div class="an-mini-stats">
            <div class="an-mini"><span class="an-mini-v" style="color:#f87171">${dm.total_events_ytd}</span><span class="an-mini-l">Events YTD</span></div>
            <div class="an-mini"><span class="an-mini-v" style="color:#4ade80">${dm.lives_saved.toLocaleString()}</span><span class="an-mini-l">Lives Saved</span></div>
            <div class="an-mini"><span class="an-mini-v" style="color:#60a5fa">${dm.evacuations}</span><span class="an-mini-l">Evacuations</span></div>
            <div class="an-mini"><span class="an-mini-v" style="color:#facc15">${dm.response_time_avg_min}m</span><span class="an-mini-l">Avg Response</span></div>
        </div>`;

    // ── Disaster Type Chart ──
    const dtTypes = dm.by_type;
    new Chart(document.getElementById('disasterTypeChart'), {
        type: 'bar',
        data: {
            labels: dtTypes.map(t=>t.type),
            datasets: [
                {label:'Events', data:dtTypes.map(t=>t.count), backgroundColor:'rgba(96,165,250,0.7)', borderRadius:4, barPercentage:0.6},
                {label:'Deaths', data:dtTypes.map(t=>t.deaths), backgroundColor:'rgba(248,113,113,0.7)', borderRadius:4, barPercentage:0.6}
            ]
        },
        options: {...cOpts, indexAxis:'y', scales:{
            x:{ticks:{color:tickColor}, grid:{color:darkGrid}},
            y:{ticks:{color:tickColor, font:{size:10}}, grid:{display:false}}
        }, plugins:{legend:{position:'top', labels:legendLabels}}}
    });

    // ── Geographic Risk Chart ──
    const gr = d.geographic_risk.high_risk_zones;
    new Chart(document.getElementById('geoRiskChart'), {
        type: 'bar',
        data: {
            labels: gr.map(z=>z.state),
            datasets: [{
                label:'Risk Score',
                data: gr.map(z=>z.risk_score),
                backgroundColor: gr.map(z=> z.risk_score>=85?'rgba(248,113,113,0.8)': z.risk_score>=75?'rgba(251,146,60,0.8)': z.risk_score>=70?'rgba(250,204,21,0.7)':'rgba(96,165,250,0.6)'),
                borderRadius:6, barPercentage:0.65
            }]
        },
        options: {...cOpts, scales:{
            x:{ticks:{color:tickColor, font:{size:9}}, grid:{display:false}},
            y:{ticks:{color:tickColor}, grid:{color:darkGrid}, max:100, beginAtZero:true}
        }, plugins:{legend:{display:false}}}
    });

    // ── Region Grid ──
    const rg = document.getElementById('anRegionGrid');
    if(rg) {
        const reg = d.geographic_risk.region_distribution;
        rg.innerHTML = Object.entries(reg).map(([name,r])=>{
            const rc = r.risk_avg>=75?'#f87171':r.risk_avg>=60?'#fb923c':'#4ade80';
            return `<div class="an-region-pill">
                <span class="an-rg-name">${name}</span>
                <span class="an-rg-risk" style="color:${rc}">${r.risk_avg}</span>
                <span class="an-rg-threat">${r.top_threat}</span>
            </div>`;
        }).join('');
    }

    // ── Historical Trends Chart ──
    const ht = d.historical_trends.yearly_comparison;
    new Chart(document.getElementById('historicalTrendChart'), {
        type: 'line',
        data: {
            labels: ht.map(y=>y.year),
            datasets: [
                {label:'Disasters', data:ht.map(y=>y.disasters), borderColor:'#60a5fa', backgroundColor:'rgba(96,165,250,0.08)', tension:0.4, fill:true, borderWidth:2, pointRadius:4, pointBackgroundColor:'#60a5fa'},
                {label:'Deaths', data:ht.map(y=>y.deaths), borderColor:'#f87171', backgroundColor:'rgba(248,113,113,0.08)', tension:0.4, fill:true, borderWidth:2, pointRadius:4, pointBackgroundColor:'#f87171'},
                {label:'Loss (₹100Cr)', data:ht.map(y=>Math.round(y.loss_cr/100)), borderColor:'#facc15', backgroundColor:'rgba(250,204,21,0.06)', tension:0.4, fill:false, borderWidth:2, borderDash:[5,3], pointRadius:3, pointBackgroundColor:'#facc15'}
            ]
        },
        options: {...cOpts, scales:{
            x:{ticks:{color:tickColor}, grid:{display:false}},
            y:{ticks:{color:tickColor}, grid:{color:darkGrid}}
        }, plugins:{legend:{position:'bottom', labels:legendLabels}}}
    });

    // ── Insights ──
    const ins = document.getElementById('anInsights');
    if(ins) ins.innerHTML = d.historical_trends.insights.map(i=>
        `<div class="an-insight"><span class="an-insight-icon">⚡</span><span>${i}</span></div>`
    ).join('');

    // ── Flood Summary ──
    const fa = d.flood_analysis;
    const fs = document.getElementById('anFloodSummary');
    if(fs) fs.innerHTML = `<div class="an-mini-stats">
        <div class="an-mini"><span class="an-mini-v" style="color:#60a5fa">${fa.total_events_2025_26}</span><span class="an-mini-l">Flood Events</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#f87171">${fa.total_deaths}</span><span class="an-mini-l">Deaths</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#fb923c">${(fa.total_displaced/1000000).toFixed(1)}M</span><span class="an-mini-l">Displaced</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#facc15">${(fa.total_area_inundated_sqkm/1000).toFixed(0)}K</span><span class="an-mini-l">km² Inundated</span></div>
    </div>`;

    // ── Flood Inundation Chart ──
    const fi = fa.monthly_inundation_sqkm;
    new Chart(document.getElementById('floodInundationChart'), {
        type: 'bar',
        data: {
            labels: fi.map(m=>m.month),
            datasets: [{
                label:'Inundation (sq km)',
                data: fi.map(m=>m.area),
                backgroundColor: fi.map(m=> m.area>40000?'rgba(248,113,113,0.8)': m.area>20000?'rgba(251,146,60,0.7)': m.area>5000?'rgba(250,204,21,0.6)':'rgba(96,165,250,0.5)'),
                borderRadius:6
            }]
        },
        options: {...cOpts, scales:{
            x:{ticks:{color:tickColor}, grid:{display:false}},
            y:{ticks:{color:tickColor, callback:v=>(v/1000)+'K'}, grid:{color:darkGrid}}
        }, plugins:{legend:{display:false}}}
    });

    // ── Disease Outbreak List ──
    const ol = document.getElementById('anOutbreakList');
    if(ol) ol.innerHTML = d.disease_outbreaks.active_outbreaks.map(o=>{
        const sc = o.status==='spreading'?'#f87171':o.status==='contained'?'#4ade80':'#facc15';
        return `<div class="an-outbreak-row">
            <span class="an-ob-disease">${o.disease}</span>
            <span class="an-ob-state">${o.state}</span>
            <span class="an-ob-cases" style="color:#60a5fa">${o.cases.toLocaleString()}</span>
            <span class="an-ob-deaths" style="color:#f87171">${o.deaths}</span>
            <span class="an-ob-status" style="color:${sc}">${o.status.toUpperCase()}</span>
        </div>`;
    }).join('');

    // ── Disease Trend Chart ──
    const dc = d.disease_outbreaks.monthly_cases;
    new Chart(document.getElementById('diseaseTrendChart'), {
        type: 'line',
        data: {
            labels: dc.map(m=>m.month),
            datasets: [
                {label:'Dengue', data:dc.map(m=>m.dengue), borderColor:'#f87171', backgroundColor:'rgba(248,113,113,0.1)', tension:0.4, fill:true, borderWidth:2},
                {label:'Malaria', data:dc.map(m=>m.malaria), borderColor:'#60a5fa', backgroundColor:'rgba(96,165,250,0.1)', tension:0.4, fill:true, borderWidth:2},
                {label:'Cholera', data:dc.map(m=>m.cholera), borderColor:'#facc15', backgroundColor:'rgba(250,204,21,0.08)', tension:0.4, fill:true, borderWidth:2},
                {label:'Others', data:dc.map(m=>m.others), borderColor:'#a78bfa', backgroundColor:'rgba(167,139,250,0.08)', tension:0.4, fill:true, borderWidth:2}
            ]
        },
        options: {...cOpts, scales:{
            x:{ticks:{color:tickColor}, grid:{display:false}},
            y:{ticks:{color:tickColor}, grid:{color:darkGrid}}
        }, plugins:{legend:{position:'bottom', labels:legendLabels}}}
    });

    // ── Correlation Note ──
    const cn = document.getElementById('anCorrelation');
    if(cn) cn.innerHTML = `<div class="an-corr-note">🔗 ${d.disease_outbreaks.correlation_note}</div>`;

    // ── Crop Failure Stats ──
    const cf = d.crop_failure;
    const cs = document.getElementById('anCropStats');
    if(cs) cs.innerHTML = `<div class="an-mini-stats">
        <div class="an-mini"><span class="an-mini-v" style="color:#fb923c">${(cf.total_area_affected_hectares/1000000).toFixed(1)}M ha</span><span class="an-mini-l">Area Affected</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#f87171">₹${(cf.estimated_loss_cr/1000).toFixed(1)}K Cr</span><span class="an-mini-l">Est. Loss</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#facc15">${(cf.farmers_affected/1000000).toFixed(1)}M</span><span class="an-mini-l">Farmers Affected</span></div>
        <div class="an-mini"><span class="an-mini-v" style="color:#4ade80">₹${(cf.compensation_disbursed_cr/1000).toFixed(1)}K Cr</span><span class="an-mini-l">Compensation</span></div>
    </div>`;

    // ── Crop Failure Chart ──
    new Chart(document.getElementById('cropFailureChart'), {
        type: 'bar',
        data: {
            labels: cf.by_crop.map(c=>c.crop),
            datasets: [
                {label:'Area (Lakh ha)', data:cf.by_crop.map(c=>Math.round(c.area_affected_ha/100000)), backgroundColor:'rgba(251,146,60,0.7)', borderRadius:4, barPercentage:0.55},
                {label:'Loss %', data:cf.by_crop.map(c=>c.loss_percent), backgroundColor:'rgba(248,113,113,0.7)', borderRadius:4, barPercentage:0.55}
            ]
        },
        options: {...cOpts, indexAxis:'y', scales:{
            x:{ticks:{color:tickColor}, grid:{color:darkGrid}},
            y:{ticks:{color:tickColor, font:{size:9}}, grid:{display:false}}
        }, plugins:{legend:{position:'top', labels:legendLabels}}}
    });

    // ── River Systems ──
    const rl = document.getElementById('anRiverList');
    if(rl) rl.innerHTML = fa.river_systems_at_risk.map(r=>{
        const rc = r.risk==='extreme'?'#f87171':r.risk==='very high'?'#fb923c':r.risk==='high'?'#facc15':'#4ade80';
        return `<div class="an-river-row">
            <div class="an-river-name">${r.river}</div>
            <span class="an-river-risk" style="background:${rc}">${r.risk.toUpperCase()}</span>
            <span class="an-river-detail">${r.states.join(', ')}</span>
            <span class="an-river-stat">${r.flood_events} events · ${r.peak_discharge_cumecs.toLocaleString()} cumecs</span>
        </div>`;
    }).join('');

    // ── Dam Levels ──
    const dl = document.getElementById('anDamList');
    if(dl) dl.innerHTML = fa.dam_levels.map(dm=>{
        const dc = dm.status==='critical'?'#f87171':dm.status==='warning'?'#fb923c':dm.status==='watch'?'#facc15':'#4ade80';
        const barW = dm.capacity_percent;
        return `<div class="an-dam-row">
            <div class="an-dam-info">
                <span class="an-dam-name">${dm.dam}</span>
                <span class="an-dam-state">${dm.state}</span>
            </div>
            <div class="an-dam-bar-wrap">
                <div class="an-dam-bar" style="width:${barW}%;background:${dc}"></div>
            </div>
            <div class="an-dam-meta">
                <span class="an-dam-pct" style="color:${dc}">${dm.capacity_percent}%</span>
                <span class="an-dam-status" style="color:${dc}">${dm.status.toUpperCase()}</span>
            </div>
        </div>`;
    }).join('');

    // ── Monthly Disaster Chart ──
    const mt = dm.monthly_trend;
    new Chart(document.getElementById('monthlyDisasterChart'), {
        type: 'bar',
        data: {
            labels: mt.map(m=>m.month),
            datasets: [
                {label:'Total Events', data:mt.map(m=>m.events), backgroundColor:'rgba(96,165,250,0.6)', borderRadius:4},
                {label:'Critical', data:mt.map(m=>m.critical), backgroundColor:'rgba(248,113,113,0.7)', borderRadius:4}
            ]
        },
        options: {...cOpts, scales:{
            x:{ticks:{color:tickColor}, grid:{display:false}},
            y:{ticks:{color:tickColor}, grid:{color:darkGrid}}
        }, plugins:{legend:{position:'top', labels:legendLabels}}}
    });

    // ── Sector Impact Distribution ──
    new Chart(document.getElementById('sectorChart'), {
        type: 'doughnut',
        data: {
            labels: dtTypes.map(t=>t.type),
            datasets: [{
                data: dtTypes.map(t=>t.count),
                backgroundColor: ['#60a5fa','#f87171','#a78bfa','#fb923c','#facc15','#4ade80','#2dd4bf','#818cf8'],
                borderColor: 'rgba(6,8,16,0.8)', borderWidth: 2
            }]
        },
        options: {...cOpts, cutout:'55%', plugins:{legend:{position:'right', labels:{...legendLabels, padding:8}}}}
    });
}

// =================== Agriculture Dashboard ===================
async function loadAgricultureDashboard() {
    try {
        const res = await fetch(`${API}/api/agriculture/dashboard`);
        if (!res.ok) throw new Error(`Agriculture dashboard request failed: ${res.status}`);
        agriData = await res.json();
        agriLoaded = true;

        renderAgriStats(agriData);
        renderCropStatus(agriData.crop_status);
        renderMandiPrices(agriData.mandi_prices);
        renderWeatherAlerts(agriData.weather_alerts);
        renderHygieneReports(agriData.hygiene_reports);
        renderCropYieldChart(agriData.crop_status);
        renderSeasonRecommendations(agriData.seasonal_recommendations);
        renderRainAdvisory(agriData.unpredicted_rain_advisory);
    } catch (e) {
        agriData = null;
        agriLoaded = false;
        console.error("Agriculture dashboard load failed:", e);
    }
}

function renderAgriStats(data) {
    const crops = data.crop_status || [];
    const healthy = crops.filter(c => c.risk === "low").length;
    const atRisk = crops.filter(c => c.risk === "high" || c.risk === "moderate").length;

    document.getElementById("agriTotalCrops").textContent = crops.length;
    document.getElementById("agriHealthy").textContent = healthy;
    document.getElementById("agriAtRisk").textContent = atRisk;
    document.getElementById("agriWeatherAlerts").textContent = (data.weather_alerts || []).length;
    document.getElementById("agriHygieneIssues").textContent = (data.hygiene_reports || []).length;
}

function renderCropStatus(crops) {
    const tbody = document.getElementById("cropStatusBody");
    if (!crops || crops.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="muted">No crop data available.</td></tr>';
        return;
    }
    tbody.innerHTML = crops.map(c => {
        const riskClass = c.risk === "high" ? "risk-high" : c.risk === "moderate" ? "risk-moderate" : "risk-low";
        const statusIcon = c.risk === "high" ? "🔴" : c.risk === "moderate" ? "🟡" : "🟢";
        return `<tr class="${riskClass}">
            <td><strong>${c.crop}</strong></td>
            <td>${c.region}</td>
            <td>${statusIcon} ${c.status}</td>
            <td>${c.yield_forecast}</td>
            <td><span class="agri-risk-badge ${riskClass}">${c.risk.toUpperCase()}</span></td>
        </tr>`;
    }).join("");
}

function filterCropStatus() {
    if (!agriData) return;
    const filter = document.getElementById("agriRiskFilter").value;
    let filtered = agriData.crop_status;
    if (filter !== "all") {
        if (filter === "high") filtered = filtered.filter(c => c.risk === "high");
        else if (filter === "moderate") filtered = filtered.filter(c => c.risk === "moderate");
        else if (filter === "low") filtered = filtered.filter(c => c.risk === "low");
    }
    renderCropStatus(filtered);
}

function renderMandiPrices(prices) {
    const tbody = document.getElementById("mandiPriceBody");
    if (!prices || prices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted">No price data available.</td></tr>';
        return;
    }
    tbody.innerHTML = prices.map(p => {
        const diff = p.price_per_quintal - p.msp;
        const diffClass = diff >= 0 ? "price-above" : "price-below";
        const diffText = p.msp === 0 ? "N/A" : (diff >= 0 ? `+₹${diff}` : `-₹${Math.abs(diff)}`);
        const trendIcon = p.trend === "up" ? "📈" : "📉";
        return `<tr>
            <td><strong>${p.crop}</strong></td>
            <td>${p.mandi}</td>
            <td>₹${p.price_per_quintal.toLocaleString()}</td>
            <td>${p.msp === 0 ? 'N/A' : '₹' + p.msp.toLocaleString()}</td>
            <td><span class="${diffClass}">${diffText}</span></td>
            <td>${trendIcon} ${p.trend.charAt(0).toUpperCase() + p.trend.slice(1)}</td>
        </tr>`;
    }).join("");
}

function renderWeatherAlerts(alerts) {
    const container = document.getElementById("agriWeatherList");
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="muted">No weather alerts.</p>';
        return;
    }
    container.innerHTML = alerts.map(a => {
        const sevClass = a.severity === "CRITICAL" ? "critical" : a.severity === "HIGH" ? "high" : a.severity === "MODERATE" ? "moderate" : "low";
        const typeIcons = { Drought: "☀️", Flood: "🌊", Heatwave: "🌡️", Landslide: "⛰️", "Cyclone Risk": "🌀", "Stubble Burning": "🔥" };
        const icon = typeIcons[a.type] || "🌦️";
        return `<div class="agri-weather-item ${sevClass}">
            <div class="agri-weather-top">
                <span class="agri-weather-icon">${icon}</span>
                <strong>${a.type}</strong>
                <span class="severity-badge ${sevClass}">${a.severity}</span>
            </div>
            <div class="agri-weather-region">📍 ${a.region}</div>
            <div class="agri-weather-desc">${a.description}</div>
            <div class="agri-weather-date">🕐 ${a.date}</div>
        </div>`;
    }).join("");
}

function renderHygieneReports(reports) {
    const container = document.getElementById("agriHygieneList");
    if (!reports || reports.length === 0) {
        container.innerHTML = '<p class="muted">No hygiene reports.</p>';
        return;
    }
    container.innerHTML = reports.map(r => {
        const sevClass = r.severity === "CRITICAL" ? "critical" : r.severity === "HIGH" ? "high" : "moderate";
        return `<div class="agri-hygiene-item ${sevClass}">
            <div class="agri-hygiene-top">
                <strong>🏥 ${r.issue}</strong>
                <span class="severity-badge ${sevClass}">${r.severity}</span>
            </div>
            <div class="agri-hygiene-region">📍 ${r.region} · 👥 ${r.affected_population.toLocaleString()} affected</div>
            <div class="agri-hygiene-desc">${r.details}</div>
        </div>`;
    }).join("");
}

function renderCropYieldChart(crops) {
    if (!crops || crops.length === 0) return;
    const ctx = document.getElementById("cropYieldChart");
    if (!ctx) return;

    const labels = crops.map(c => c.crop.split(" ")[0]);
    const yields = crops.map(c => parseInt(c.yield_forecast));
    const colors = crops.map(c =>
        c.risk === "high" ? "rgba(231,76,60,0.7)" :
        c.risk === "moderate" ? "rgba(243,156,18,0.7)" :
        "rgba(46,204,113,0.7)"
    );

    new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Yield Forecast %",
                data: yields,
                backgroundColor: colors,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#4a5568", font: { size: 10 } }, grid: { display: false } },
                y: { ticks: { color: "#4a5568" }, grid: { color: "rgba(255,255,255,0.03)" }, max: 100, beginAtZero: true },
            },
            plugins: { legend: { display: false } },
        },
    });
}

// =================== Seasonal Recommendations ===================
function renderSeasonRecommendations(seasons) {
    const container = document.getElementById("seasonRecommendations");
    if (!seasons || seasons.length === 0) {
        container.innerHTML = '<p class="muted">No seasonal data available.</p>';
        return;
    }
    container.innerHTML = seasons.map(s => {
        const cropTags = s.best_crops.map(c => `<span class="season-crop-tag">${c}</span>`).join("");
        const fertRows = s.fertilizers.map(f =>
            `<tr>
                <td><strong>${f.name}</strong></td>
                <td><span class="fert-type-badge fert-${f.type.toLowerCase()}">${f.type}</span></td>
                <td>${f.usage}</td>
            </tr>`
        ).join("");
        const tips = s.prevention_tips.map(t => `<li>${t}</li>`).join("");

        return `<div class="season-rec-card">
            <div class="season-rec-header">
                <span class="season-rec-icon">${s.icon}</span>
                <h3>${s.season}</h3>
            </div>
            <div class="season-rec-body">
                <div class="season-rec-section">
                    <h4>🌱 Best Crops to Grow</h4>
                    <div class="season-crop-tags">${cropTags}</div>
                </div>
                <div class="season-rec-section">
                    <h4>🧪 Recommended Fertilizers</h4>
                    <table class="fert-table">
                        <thead><tr><th>Fertilizer</th><th>Type</th><th>Usage & Dosage</th></tr></thead>
                        <tbody>${fertRows}</tbody>
                    </table>
                </div>
                <div class="season-rec-section">
                    <h4>🛡️ Prevention Tips</h4>
                    <ul class="prevention-tips-list">${tips}</ul>
                </div>
            </div>
        </div>`;
    }).join("");
}

function filterSeasonRec() {
    if (!agriData || !agriData.seasonal_recommendations) return;
    const filter = document.getElementById("seasonFilter").value;
    let filtered = agriData.seasonal_recommendations;
    if (filter !== "all") {
        filtered = filtered.filter(s => s.season.toLowerCase().includes(filter.toLowerCase()));
    }
    renderSeasonRecommendations(filtered);
}

// =================== Unpredicted Rain Advisory ===================
function renderRainAdvisory(advisories) {
    const container = document.getElementById("rainAdvisoryList");
    if (!advisories || advisories.length === 0) {
        container.innerHTML = '<p class="muted">No rain advisories available.</p>';
        return;
    }
    container.innerHTML = advisories.map(a => {
        const sevClass = a.severity === "CRITICAL" ? "critical" : a.severity === "HIGH" ? "high" : "moderate";
        const cropTags = a.affected_crops.map(c => `<span class="rain-crop-tag">${c}</span>`).join("");
        const immediate = a.immediate_actions.map(act => `<li>${act}</li>`).join("");
        const prevention = a.prevention_measures.map(p => `<li>${p}</li>`).join("");

        return `<div class="rain-advisory-card ${sevClass}">
            <div class="rain-advisory-header">
                <div>
                    <strong>🌧️ ${a.scenario}</strong>
                    <span class="severity-badge ${sevClass}">${a.severity}</span>
                </div>
            </div>
            <div class="rain-advisory-crops">
                <span class="rain-label">Affected Crops:</span> ${cropTags}
            </div>
            <div class="rain-advisory-impact">
                <strong>⚡ Impact:</strong> ${a.impact}
            </div>
            <div class="rain-advisory-grid">
                <div class="rain-col">
                    <h4>🚨 Immediate Actions (0–48 hours)</h4>
                    <ul class="rain-actions-list">${immediate}</ul>
                </div>
                <div class="rain-col">
                    <h4>🛡️ Prevention & Preparedness</h4>
                    <ul class="rain-actions-list">${prevention}</ul>
                </div>
            </div>
        </div>`;
    }).join("");
}

// =================== Health Dashboard ===================
async function loadHealthDashboard() {
    try {
        const res = await fetch(`${API}/api/health/dashboard`);
        if (!res.ok) throw new Error(`Health dashboard request failed: ${res.status}`);
        healthData = await res.json();
        healthLoaded = true;
        renderHealthStats(healthData);
        renderDiseaseOutbreaks(healthData.disease_outbreaks);
        renderVaccinationStatus(healthData.vaccination_status);
        renderSanitationTable(healthData.water_sanitation);
        renderHospitalCapacity(healthData.hospital_capacity);
        renderPublicSafetyAlerts(healthData.public_safety_alerts);
    } catch (e) {
        healthLoaded = false;
        console.error("Health dashboard load failed:", e);
        document.getElementById("diseaseOutbreakList").innerHTML = '<p class="muted">Failed to load health data. Open the tab again to retry.</p>';
        document.getElementById("vaccinationList").innerHTML = '<p class="muted">Failed to load vaccination data.</p>';
        document.getElementById("sanitationTableBody").innerHTML = '<tr><td colspan="5" class="muted">Failed to load sanitation data.</td></tr>';
        document.getElementById("hospitalCapacityList").innerHTML = '<p class="muted">Failed to load hospital capacity.</p>';
        document.getElementById("publicSafetyAlertList").innerHTML = '<p class="muted">Failed to load safety alerts.</p>';
    }
}

function renderHealthStats(d) {
    const outbreaks = d.disease_outbreaks || [];
    const totalCases = outbreaks.reduce((s, o) => s + (o.active_cases || 0), 0);
    const totalDeaths = outbreaks.reduce((s, o) => s + (o.deaths || 0), 0);
    const vaccArr = d.vaccination_status || [];
    const avgVacc = vaccArr.length ? Math.round(vaccArr.reduce((s, v) => s + v.coverage_percent, 0) / vaccArr.length) : 0;
    const safetyCount = (d.public_safety_alerts || []).length;

    document.getElementById("hStatOutbreaks").textContent = outbreaks.length;
    document.getElementById("hStatCases").textContent = totalCases.toLocaleString();
    document.getElementById("hStatDeaths").textContent = totalDeaths.toLocaleString();
    document.getElementById("hStatVacc").textContent = avgVacc + "%";
    document.getElementById("hStatSafety").textContent = safetyCount;
}

function renderDiseaseOutbreaks(outbreaks) {
    const el = document.getElementById("diseaseOutbreakList");
    if (!outbreaks || !outbreaks.length) { el.innerHTML = '<p class="muted">No active outbreaks</p>'; return; }

    el.innerHTML = outbreaks.map((o, i) => {
        const trendIcon = o.trend === "rising" ? "📈" : o.trend === "declining" ? "📉" : "➡️";
        const trendClass = o.trend === "rising" ? "trend-rising" : o.trend === "declining" ? "trend-declining" : "trend-stable";
        const sevClass = `badge-${o.severity || "moderate"}`;
        const symptoms = (o.symptoms || []).map(s => `<span class="symptom-tag">${s}</span>`).join("");
        const prevention = (o.prevention || []).map(p => `<li>${p}</li>`).join("");
        return `<div class="outbreak-card ${trendClass}">
            <div class="outbreak-header">
                <div class="outbreak-title">
                    <h3>${o.disease}</h3>
                    <span class="outbreak-region">📍 ${o.region}</span>
                </div>
                <div class="outbreak-meta">
                    <span class="badge ${sevClass}">${(o.severity||"").toUpperCase()}</span>
                    <span class="outbreak-trend">${trendIcon} ${o.trend} (${o.week_change || ""})</span>
                </div>
            </div>
            <div class="outbreak-status-row">
                <span class="outbreak-status-badge">${o.status}</span>
                <span class="outbreak-transmission">⚙️ ${o.transmission || ""}</span>
            </div>
            <div class="outbreak-stats">
                <div class="ob-stat"><span class="ob-val">${(o.active_cases||0).toLocaleString()}</span><span class="ob-lbl">Active Cases</span></div>
                <div class="ob-stat ob-deaths"><span class="ob-val">${o.deaths||0}</span><span class="ob-lbl">Deaths</span></div>
                <div class="ob-stat"><span class="ob-val">${o.affected_districts||"N/A"}</span><span class="ob-lbl">Districts</span></div>
            </div>
            <div class="outbreak-detail" id="outbreakDetail${i}">
                <div class="outbreak-symptoms">
                    <strong>🩺 Symptoms:</strong> ${symptoms}
                </div>
                <div class="outbreak-prevention">
                    <strong>🛡️ Prevention & Response:</strong>
                    <ul>${prevention}</ul>
                </div>
                <div class="outbreak-footer">
                    <span class="muted">Last updated: ${o.last_updated || "N/A"}</span>
                </div>
            </div>
        </div>`;
    }).join("");
}

function renderVaccinationStatus(vaccines) {
    const el = document.getElementById("vaccinationList");
    if (!vaccines || !vaccines.length) { el.innerHTML = '<p class="muted">No data</p>'; return; }

    el.innerHTML = vaccines.map(v => {
        const pct = v.coverage_percent || 0;
        const barColor = pct >= 90 ? "#4ade80" : pct >= 70 ? "#facc15" : "#f87171";
        return `<div class="vacc-item">
            <div class="vacc-info">
                <span class="vacc-name">${v.program}</span>
                <span class="vacc-target">Target: ${v.target_group}</span>
            </div>
            <div class="vacc-bar-wrap">
                <div class="vacc-bar" style="width:${pct}%;background:${barColor}"></div>
            </div>
            <span class="vacc-pct">${pct}%</span>
            <span class="vacc-doses">${(v.doses_administered||0).toLocaleString()} doses</span>
        </div>`;
    }).join("");
}

function renderSanitationTable(data) {
    const tbody = document.getElementById("sanitationTableBody");
    if (!data || !data.length) { tbody.innerHTML = '<tr><td colspan="5" class="muted">No data</td></tr>'; return; }

    tbody.innerHTML = data.map(r => {
        const qualityClass = r.water_quality === "Safe" ? "badge-safe" : r.water_quality === "Moderate" ? "badge-warn" : "badge-danger";
        const odfClass = r.odf_status === "ODF+" ? "badge-safe" : r.odf_status === "ODF" ? "badge-warn" : "badge-danger";
        const scoreColor = r.sanitation_score >= 80 ? "#4ade80" : r.sanitation_score >= 60 ? "#facc15" : "#f87171";
        return `<tr>
            <td>${r.region}</td>
            <td><span class="badge ${qualityClass}">${r.water_quality}</span></td>
            <td>${r.contamination_source || "None"}</td>
            <td><span class="badge ${odfClass}">${r.odf_status}</span></td>
            <td><span style="color:${scoreColor};font-weight:600">${r.sanitation_score}/100</span></td>
        </tr>`;
    }).join("");
}

function renderHospitalCapacity(hospitals) {
    const el = document.getElementById("hospitalCapacityList");
    if (!hospitals || !hospitals.length) { el.innerHTML = '<p class="muted">No data</p>'; return; }

    el.innerHTML = hospitals.map(h => {
        const bedPct = h.total_beds ? Math.round((h.available_beds / h.total_beds) * 100) : 0;
        const icuPct = h.icu_beds ? Math.round((h.icu_available / h.icu_beds) * 100) : 0;
        const ventPct = h.ventilators ? Math.round((h.ventilators_available / h.ventilators) * 100) : 0;
        const barColor = p => p >= 40 ? "#4ade80" : p >= 20 ? "#facc15" : "#f87171";
        return `<div class="hospital-card">
            <h4>${h.region}</h4>
            <div class="hosp-row">
                <span class="hosp-label">Beds</span>
                <div class="hosp-bar-wrap"><div class="hosp-bar" style="width:${bedPct}%;background:${barColor(bedPct)}"></div></div>
                <span class="hosp-val">${h.available_beds}/${h.total_beds}</span>
            </div>
            <div class="hosp-row">
                <span class="hosp-label">ICU</span>
                <div class="hosp-bar-wrap"><div class="hosp-bar" style="width:${icuPct}%;background:${barColor(icuPct)}"></div></div>
                <span class="hosp-val">${h.icu_available}/${h.icu_beds}</span>
            </div>
            <div class="hosp-row">
                <span class="hosp-label">Ventilators</span>
                <div class="hosp-bar-wrap"><div class="hosp-bar" style="width:${ventPct}%;background:${barColor(ventPct)}"></div></div>
                <span class="hosp-val">${h.ventilators_available}/${h.ventilators}</span>
            </div>
        </div>`;
    }).join("");
}

function renderPublicSafetyAlerts(alerts) {
    const el = document.getElementById("publicSafetyAlertList");
    if (!alerts || !alerts.length) { el.innerHTML = '<p class="muted">No safety alerts</p>'; return; }

    const severityIcon = s => s === "critical" ? "🔴" : s === "high" ? "🟠" : s === "moderate" ? "🟡" : "🟢";
    el.innerHTML = alerts.map(a => {
        const actions = (a.action_required || []).map(act => `<li>${act}</li>`).join("");
        return `<div class="safety-alert-item severity-${a.severity}">
            <div class="safety-alert-header">
                <span class="safety-alert-icon">${severityIcon(a.severity)}</span>
                <div>
                    <h4>${a.alert_type}</h4>
                    <span class="safety-alert-region">${a.region} — ${a.date_issued}</span>
                </div>
                <span class="badge badge-${a.severity}">${a.severity.toUpperCase()}</span>
            </div>
            <p class="safety-alert-desc">${a.description}</p>
            <div class="safety-alert-actions">
                <strong>Action Required:</strong>
                <ul>${actions}</ul>
            </div>
        </div>`;
    }).join("");
}

// ===== Outbreak Filters =====
function filterOutbreaks() {
    if (!healthData || !healthData.disease_outbreaks) return;
    const sevFilter = document.getElementById("outbreakSeverityFilter").value;
    const trendFilter = document.getElementById("outbreakTrendFilter").value;
    let filtered = healthData.disease_outbreaks;
    if (sevFilter !== "all") filtered = filtered.filter(o => o.severity === sevFilter);
    if (trendFilter !== "all") filtered = filtered.filter(o => o.trend === trendFilter);
    renderDiseaseOutbreaks(filtered);
}

// =================== Weather Dashboard ===================
async function loadWeatherDashboard() {
    try {
        const res = await fetch(`${API}/api/weather/dashboard`);
        if (!res.ok) throw new Error(`Weather dashboard request failed: ${res.status}`);
        weatherData = await res.json();
        weatherLoaded = true;
        renderWeatherStats(weatherData);
        renderCityConditions(weatherData.current_conditions);
        renderWeeklyForecast(weatherData.weekly_forecast);
        renderForecastChart(weatherData.weekly_forecast);
        renderHistoricalChart(weatherData.historical_trends);
        renderGeoZones(weatherData.geography_zones);
        renderMonsoonPanel(weatherData.monsoon_prediction);
        renderSevereWeatherAlerts(weatherData.severe_weather_alerts);
    } catch (e) {
        weatherLoaded = false;
        console.error("Weather dashboard load failed:", e);
        document.getElementById("wxCityCards").innerHTML = '<p class="muted">Failed to load current conditions. Open the tab again to retry.</p>';
        document.getElementById("wxForecastStrip").innerHTML = '<p class="muted">Failed to load forecast.</p>';
        document.getElementById("wxGeoList").innerHTML = '<p class="muted">Failed to load geography zones.</p>';
        document.getElementById("wxMonsoonPanel").innerHTML = '<p class="muted">Failed to load monsoon data.</p>';
        document.getElementById("wxAlertList").innerHTML = '<p class="muted">Failed to load severe weather alerts.</p>';
    }
}

function renderWeatherStats(d) {
    const cities = d.current_conditions || [];
    const avgTemp = cities.length ? Math.round(cities.reduce((s, c) => s + c.temp_c, 0) / cities.length) : 0;
    const avgFeels = cities.length ? Math.round(cities.reduce((s, c) => s + c.feels_like, 0) / cities.length) : 0;
    const avgHum = cities.length ? Math.round(cities.reduce((s, c) => s + c.humidity, 0) / cities.length) : 0;
    const alertCount = (d.severe_weather_alerts || []).length;
    const monsoonFc = d.monsoon_prediction ? d.monsoon_prediction.overall_forecast : "N/A";

    document.getElementById("wxStatTemp").textContent = avgTemp + "°";
    document.getElementById("wxStatFeels").textContent = avgFeels + "°";
    document.getElementById("wxStatHumidity").textContent = avgHum + "%";
    document.getElementById("wxStatAlerts").textContent = alertCount;
    document.getElementById("wxStatMonsoon").textContent = monsoonFc.length > 20 ? monsoonFc.substring(0, 20) + "…" : monsoonFc;
}

function renderCityConditions(cities) {
    const el = document.getElementById("wxCityCards");
    if (!cities || !cities.length) { el.innerHTML = '<p class="muted">No data</p>'; return; }

    el.innerHTML = cities.map(c => {
        const tempColor = c.temp_c >= 42 ? "#ef4444" : c.temp_c >= 35 ? "#fb923c" : c.temp_c >= 28 ? "#facc15" : "#4ade80";
        const aqiColor = c.aqi > 150 ? "#ef4444" : c.aqi > 100 ? "#fb923c" : c.aqi > 50 ? "#facc15" : "#4ade80";
        const uvColor = c.uv_index >= 11 ? "#ef4444" : c.uv_index >= 8 ? "#fb923c" : c.uv_index >= 6 ? "#facc15" : "#4ade80";
        return `<div class="wx-city-card">
            <div class="wx-city-header">
                <span class="wx-city-icon">${c.icon}</span>
                <div>
                    <h4>${c.city}</h4>
                    <span class="wx-condition">${c.condition}</span>
                </div>
            </div>
            <div class="wx-city-temp" style="color:${tempColor}">${c.temp_c}°C</div>
            <div class="wx-city-feels">Feels ${c.feels_like}°C</div>
            <div class="wx-city-details">
                <span>💧 ${c.humidity}%</span>
                <span>💨 ${c.wind_kph} km/h ${c.wind_dir}</span>
            </div>
            <div class="wx-city-details">
                <span style="color:${aqiColor}">AQI ${c.aqi}</span>
                <span style="color:${uvColor}">UV ${c.uv_index}</span>
                <span>👁️ ${c.visibility_km}km</span>
            </div>
        </div>`;
    }).join("");
}

function renderWeeklyForecast(forecast) {
    const el = document.getElementById("wxForecastStrip");
    if (!forecast || !forecast.length) { el.innerHTML = '<p class="muted">No forecast</p>'; return; }

    el.innerHTML = forecast.map((f, i) => {
        const isToday = i === 0;
        return `<div class="wx-day-card ${isToday ? 'wx-today' : ''}">
            <span class="wx-day-name">${isToday ? 'TODAY' : f.day}</span>
            <span class="wx-day-icon">${f.icon}</span>
            <span class="wx-day-temps"><strong>${f.temp_max}°</strong> / ${f.temp_min}°</span>
            <span class="wx-day-rain">🌧 ${f.rain_chance}%</span>
            <span class="wx-day-wind">💨 ${f.wind_kph}</span>
            <span class="wx-day-cond">${f.condition}</span>
        </div>`;
    }).join("");
}

function renderForecastChart(forecast) {
    const ctx = document.getElementById("wxForecastChart");
    if (!ctx || !forecast || typeof Chart === "undefined") return;
    new Chart(ctx, {
        type: "line",
        data: {
            labels: forecast.map(f => f.day),
            datasets: [
                {
                    label: "Max Temp °C",
                    data: forecast.map(f => f.temp_max),
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239,68,68,.1)",
                    fill: true, tension: 0.3,
                },
                {
                    label: "Min Temp °C",
                    data: forecast.map(f => f.temp_min),
                    borderColor: "#60a5fa",
                    backgroundColor: "rgba(96,165,250,.1)",
                    fill: true, tension: 0.3,
                },
                {
                    label: "Rain %",
                    data: forecast.map(f => f.rain_chance),
                    borderColor: "#4ade80",
                    borderDash: [5, 5],
                    fill: false, tension: 0.3, yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#94a3b8" } } },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,.1)" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,.1)" }, title: { display: true, text: "°C", color: "#94a3b8" } },
                y1: { position: "right", min: 0, max: 100, ticks: { color: "#4ade80" }, grid: { display: false }, title: { display: true, text: "Rain %", color: "#4ade80" } },
            },
        },
    });
}

function renderHistoricalChart(hist) {
    const ctx = document.getElementById("wxHistoricalChart");
    if (!ctx || !hist || typeof Chart === "undefined") return;
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: hist.labels,
            datasets: [
                {
                    label: "Avg Temp °C",
                    data: hist.avg_temp,
                    backgroundColor: "rgba(239,68,68,.6)",
                    borderRadius: 4,
                    yAxisID: "y",
                    order: 2,
                },
                {
                    label: "Rainfall mm",
                    data: hist.avg_rainfall_mm,
                    type: "line",
                    borderColor: "#60a5fa",
                    backgroundColor: "rgba(96,165,250,.15)",
                    fill: true, tension: 0.3,
                    yAxisID: "y1",
                    order: 1,
                },
                {
                    label: "Humidity %",
                    data: hist.avg_humidity,
                    type: "line",
                    borderColor: "#4ade80",
                    borderDash: [4, 4],
                    fill: false, tension: 0.3,
                    yAxisID: "y2",
                    order: 0,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#94a3b8" } } },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,.1)" } },
                y: { position: "left", ticks: { color: "#ef4444" }, grid: { color: "rgba(148,163,184,.08)" }, title: { display: true, text: "Temp °C", color: "#ef4444" } },
                y1: { position: "right", ticks: { color: "#60a5fa" }, grid: { display: false }, title: { display: true, text: "Rainfall mm", color: "#60a5fa" } },
                y2: { position: "right", display: false, min: 0, max: 100 },
            },
        },
    });
}

function renderGeoZones(zones) {
    const el = document.getElementById("wxGeoList");
    if (!zones || !zones.length) {
        if (el) el.innerHTML = '<p class="muted">No geography data</p>';
        return;
    }

    const statusColorsMap = {
        "Heat Wave Active": "#ef4444",
        "Heat Wave â€” Red Alert": "#dc2626",
        "Extreme Heat": "#fb923c",
        "Pre-Monsoon Humidity": "#facc15",
        "Hot & Humid": "#fb923c",
        "Heavy Rain Active": "#3b82f6",
        "Snowmelt + Warming": "#a78bfa",
    };

    if (typeof L === "undefined") {
        el.innerHTML = zones.map(z => {
            const color = statusColorsMap[z.current_status] || "#94a3b8";
            return `<div class="wx-geo-item">
                <span class="wx-geo-dot" style="background:${color}"></span>
                <div class="wx-geo-info">
                    <strong>${z.zone}</strong>
                    <span class="muted">${z.climate} â€” ${z.current_status}</span>
                </div>
                <span class="wx-geo-risk">${z.key_risk}</span>
            </div>`;
        }).join("");
        return;
    }

    // Init Leaflet map
    if (!wxGeoMap) {
        wxGeoMap = L.map("wxGeoMap").setView([22.5, 79], 4.4);
        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
            attribution: '© CartoDB',
        }).addTo(wxGeoMap);
    }

    if (!zones || !zones.length) return;

    const statusColorsMap2 = {
        "Heat Wave Active": "#ef4444",
        "Heat Wave — Red Alert": "#dc2626",
        "Extreme Heat": "#fb923c",
        "Pre-Monsoon Humidity": "#facc15",
        "Hot & Humid": "#fb923c",
        "Heavy Rain Active": "#3b82f6",
        "Snowmelt + Warming": "#a78bfa",
    };

    zones.forEach(z => {
        const color = statusColorsMap[z.current_status] || "#94a3b8";
        L.circleMarker([z.lat, z.lon], {
            radius: 14, fillColor: color, color: "#fff", weight: 1, fillOpacity: 0.7,
        }).addTo(wxGeoMap).bindPopup(`
            <strong>${z.zone}</strong><br>
            Climate: ${z.climate}<br>
            Status: <b style="color:${color}">${z.current_status}</b><br>
            Monsoon Onset: ${z.monsoon_onset}<br>
            Key Risk: ${z.key_risk}
        `);
    });

    // Zone list below map
    const geoListEl = document.getElementById("wxGeoList");
    geoListEl.innerHTML = zones.map(z => {
        const color = statusColorsMap[z.current_status] || "#94a3b8";
        return `<div class="wx-geo-item">
            <span class="wx-geo-dot" style="background:${color}"></span>
            <div class="wx-geo-info">
                <strong>${z.zone}</strong>
                <span class="muted">${z.climate} — ${z.current_status}</span>
            </div>
            <span class="wx-geo-risk">${z.key_risk}</span>
        </div>`;
    }).join("");
}

function renderMonsoonPanel(m) {
    const el = document.getElementById("wxMonsoonPanel");
    if (!m) { el.innerHTML = '<p class="muted">No data</p>'; return; }

    const regional = (m.regional_forecast || []).map(r => {
        const riskColor = r.risk.includes("flood") || r.risk.includes("Flood") ? "#ef4444" : r.risk.includes("drought") || r.risk.includes("Drought") ? "#fb923c" : "#facc15";
        return `<div class="wx-monsoon-region">
            <strong>${r.region}</strong>
            <span class="wx-monsoon-fc">${r.forecast}</span>
            <span class="wx-monsoon-risk" style="color:${riskColor}">⚠️ ${r.risk}</span>
        </div>`;
    }).join("");

    el.innerHTML = `
        <div class="wx-monsoon-header">
            <div class="wx-monsoon-big">
                <span class="wx-monsoon-label">Overall Forecast</span>
                <span class="wx-monsoon-value">${m.overall_forecast}</span>
            </div>
            <div class="wx-monsoon-stats">
                <div><span class="ob-val">${m.predicted_mm}</span><span class="ob-lbl">Predicted mm</span></div>
                <div><span class="ob-val">${m.lpa_mm}</span><span class="ob-lbl">LPA mm</span></div>
                <div><span class="ob-val">${m.confidence}</span><span class="ob-lbl">Confidence</span></div>
            </div>
        </div>
        <div class="wx-monsoon-dates">
            <span>🌊 Kerala Onset: <strong>${m.onset_kerala}</strong></span>
            <span>🏙️ Delhi Onset: <strong>${m.onset_delhi}</strong></span>
            <span>📅 Withdrawal: <strong>${m.withdrawal_start}</strong></span>
        </div>
        <div class="wx-monsoon-climate">
            <span>🌡️ El Niño: <em>${m.el_nino_status}</em></span>
            <span>🌊 IOD: <em>${m.iod_status}</em></span>
        </div>
        <h4 style="margin:12px 0 8px;">Regional Breakdown</h4>
        <div class="wx-monsoon-regions">${regional}</div>
    `;
}

function renderSevereWeatherAlerts(alerts) {
    const el = document.getElementById("wxAlertList");
    if (!alerts || !alerts.length) { el.innerHTML = '<p class="muted">No severe weather alerts</p>'; return; }

    const sevIcon = s => s === "critical" ? "🔴" : s === "high" ? "🟠" : s === "moderate" ? "🟡" : "🟢";
    el.innerHTML = alerts.map(a => {
        const advisories = (a.advisory || []).map(adv => `<li>${adv}</li>`).join("");
        return `<div class="wx-alert-item severity-${a.severity}">
            <div class="wx-alert-header">
                <span>${sevIcon(a.severity)}</span>
                <div>
                    <h4>${a.type}</h4>
                    <span class="muted">${a.region} — ${a.valid_from} to ${a.valid_until}</span>
                </div>
                <span class="badge badge-${a.severity}">${a.severity.toUpperCase()}</span>
            </div>
            <p class="wx-alert-desc">${a.description}</p>
            <div class="wx-alert-advisory">
                <strong>Advisory:</strong>
                <ul>${advisories}</ul>
            </div>
        </div>`;
    }).join("");
}

// =================== GLOBAL ASK ME PANEL ===================
let askMePanelOpen = false;
let askMeRecording = false;
let askMeRecorder = null;
let askMeAudioChunks = [];
let askMeTTSEnabled = true;

const ASKME_LANGUAGE_NAMES = {
    "auto": "Auto Detect",
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
};

function askMeLanguageName(code) {
    return ASKME_LANGUAGE_NAMES[code] || code || "Unknown";
}

function updateAskMeStatus(modeText, detectedCode) {
    const modeEl = document.getElementById("askMeModeLabel");
    const langEl = document.getElementById("askMeDetectedLang");
    if (modeEl && modeText) modeEl.textContent = modeText;
    if (langEl) langEl.textContent = askMeLanguageName(detectedCode);
}

function askMeDetectionChip(code, prefix = "Detected") {
    return `<div class="askme-detected-chip"><span>${prefix}</span><span>${askMeLanguageName(code)}</span></div>`;
}

function toggleAskMePanel() {
    const panel = document.getElementById("askMePanel");
    const fab = document.getElementById("askMeFab");
    askMePanelOpen = !askMePanelOpen;
    panel.classList.toggle("hidden", !askMePanelOpen);
    fab.classList.toggle("askme-fab-active", askMePanelOpen);
    if (askMePanelOpen) {
        updateAskMeStatus(askMeTTSEnabled ? "Text + Voice" : "Text Only", document.getElementById("askMeLang")?.value || "auto");
        setTimeout(() => document.getElementById("askMeInput").focus(), 200);
    }
}

function toggleAskMeTTS() {
    askMeTTSEnabled = !askMeTTSEnabled;
    const btn = document.getElementById("askMeTtsToggle");
    btn.classList.toggle("active", askMeTTSEnabled);
    updateAskMeStatus(askMeTTSEnabled ? "Text + Voice" : "Text Only", document.getElementById("askMeLang")?.value || "auto");
    btn.textContent = askMeTTSEnabled ? "🔊" : "🔇";
}

function askMeAddMsg(text, role, id) {
    const el = document.getElementById("askMeMessages");
    const avatar = role === "user" ? "👤" : "🤖";
    const div = document.createElement("div");
    div.className = `askme-msg ${role}`;
    if (id) div.id = id;
    div.innerHTML = `<span class="askme-msg-avatar">${avatar}</span><div class="askme-msg-body">${text}</div>`;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}

function askMeRemoveMsg(id) {
    const m = document.getElementById(id);
    if (m) m.remove();
}

async function askMeSend() {
    const input = document.getElementById("askMeInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";

    askMeAddMsg(text, "user");

    // Emergency detection
    if (typeof detectEmergency === "function" && detectEmergency(text)) {
        askMeAddMsg("🚨 <strong>Emergency detected!</strong> Redirecting to Emergency SOS...", "bot");
        setTimeout(() => switchDashboard("emergency"), 1500);
        return;
    }

    askMeAddMsg("<span class='askme-typing'>Thinking...</span>", "bot", "askMeThinking");

    const lang = document.getElementById("askMeLang").value;
    const sendLang = lang;

    try {
        const res = await fetch(`${API}/api/text-query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, language_code: sendLang }),
        });
        const data = await res.json();
        askMeRemoveMsg("askMeThinking");

        // Show detected language
        const detectedLang = data.detected_language || (lang === "auto" ? "en-IN" : sendLang);
        const display = (detectedLang === "en-IN" && (lang === "auto" || lang === "en-IN")) ? data.response_english : (data.response_translated || data.response_english);
        const langLabel = detectedLang !== "en-IN" ? ` <span class="askme-lang-tag">${detectedLang}</span>` : "";
        updateAskMeStatus(askMeTTSEnabled ? "Text + Voice" : "Text Only", detectedLang);
        askMeAddMsg(display + langLabel + askMeDetectionChip(detectedLang), "bot");

        if (data.sector) {
            askMeAddMsg(`📌 Sector: <strong>${data.sector}</strong>`, "bot");
        }

        // Auto TTS if enabled
        if (askMeTTSEnabled && display.length < 2000) {
            askMeTTS(data.response_translated || data.response_english, detectedLang);
        }

        if (data.emergency_detected) {
            askMeAddMsg("🚨 <strong>Emergency detected in your query!</strong> Opening Emergency dashboard...", "bot");
            setTimeout(() => switchDashboard("emergency"), 2000);
        }
    } catch (err) {
        askMeRemoveMsg("askMeThinking");
        askMeAddMsg("❌ Could not reach the server. Is the backend running?", "bot");
    }
}

async function askMeToggleVoice() {
    const btn = document.getElementById("askMeMicBtn");
    const status = document.getElementById("askMeVoiceStatus");

    if (!askMeRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            askMeRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            askMeAudioChunks = [];

            askMeRecorder.ondataavailable = (e) => askMeAudioChunks.push(e.data);
            askMeRecorder.onstop = () => askMeSendVoice();

            askMeRecorder.start();
            askMeRecording = true;
            btn.classList.add("recording");
            btn.textContent = "⏹";
            status.textContent = "🔴 Recording... Speak in any language. Tap ⏹ when done.";
            status.classList.remove("hidden");
        } catch (err) {
            askMeAddMsg("❌ Microphone access denied. Please allow microphone.", "bot");
        }
    } else {
        askMeRecorder.stop();
        askMeRecorder.stream.getTracks().forEach(t => t.stop());
        askMeRecording = false;
        btn.classList.remove("recording");
        btn.textContent = "🎤";
        status.textContent = "⏳ Processing your voice...";
    }
}

async function askMeSendVoice() {
    const status = document.getElementById("askMeVoiceStatus");
    const blob = new Blob(askMeAudioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "askme_recording.webm");
    formData.append("language_code", document.getElementById("askMeLang")?.value || "auto");

    askMeAddMsg("🎤 <em>[Voice message]</em>", "user");
    askMeAddMsg("<span class='askme-typing'>Processing voice input...</span>", "bot", "askMeThinking");

    try {
        // Create a timeout promise
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Request timeout: Server took too long to respond")), 30000)
        );
        
        const fetchPromise = fetch(`${API}/api/voice-query`, {
            method: "POST",
            body: formData,
        });
        
        const res = await Promise.race([fetchPromise, timeoutPromise]);
        
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Server error: " + res.status);
        }
        
        const data = await res.json();
        askMeRemoveMsg("askMeThinking");

        const detectedLang = data.detected_language || "en-IN";
        updateAskMeStatus(askMeTTSEnabled ? "Voice Reply On" : "Voice Reply Off", detectedLang);
        askMeAddMsg(askMeDetectionChip(detectedLang, "Heard"), "user");
        askMeAddMsg(`🎤 You: "${data.user_text}"`, "user");

        // Emergency check
        if ((typeof detectEmergency === "function" && (detectEmergency(data.user_text) || detectEmergency(data.user_text_english || ""))) || data.emergency_detected) {
            askMeAddMsg("🚨 <strong>Emergency detected!</strong> Redirecting to Emergency SOS...", "bot");
            setTimeout(() => switchDashboard("emergency"), 1500);
            status.classList.add("hidden");
            return;
        }

        if (data.response_translated || data.response_english) {
            askMeAddMsg((data.response_translated || data.response_english) + askMeDetectionChip(detectedLang, "Reply"), "bot");
        }

        // Play audio response
        if (askMeTTSEnabled && data.response_audio_base64) {
            askMePlayAudio(data.response_audio_base64);
        }

        status.classList.add("hidden");
    } catch (err) {
        askMeRemoveMsg("askMeThinking");
        console.error("AskMe voice query error:", err);
        
        let errorMsg = "❌ Could not process voice query.";
        if (err.message.includes("timeout")) {
            errorMsg = "❌ Request timeout. Server is not responding. Please try again.";
        } else if (err.message.includes("Network")) {
            errorMsg = "❌ Network error. Please check your connection.";
        } else if (err.message) {
            errorMsg = "❌ Error: " + err.message;
        }
        
        askMeAddMsg(errorMsg, "bot");
        status.classList.add("hidden");
    }
}

async function askMeTTS(text, langCode) {
    try {
        const res = await fetch(`${API}/api/tts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text.substring(0, 500), language_code: langCode || "en-IN" }),
        });
        const data = await res.json();
        if (data.audio_base64) askMePlayAudio(data.audio_base64);
    } catch (e) {
        console.warn("TTS failed:", e);
    }
}

function askMePlayAudio(base64Audio) {
    if (!base64Audio || base64Audio.length === 0) {
        console.warn("⚠️ Empty audio data - cannot play");
        return;
    }
    
    try {
        const bytes = atob(base64Audio);
        const arr = new Uint8Array(bytes.length);
        for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
        const blob = new Blob([arr], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        
        audio.onplay = () => console.log("🔊 Ask Me audio playback started");
        audio.onended = () => console.log("✅ Ask Me audio playback ended");
        audio.onerror = (e) => console.error("❌ Ask Me audio error:", e);
        
        audio.play().catch(e => console.warn("Audio play blocked:", e));
    } catch (e) {
        console.error("❌ Ask Me audio decode error:", e);
    }
}

// =================== WEATHER FORECASTING RECOMMENDATIONS ===================
async function loadWeatherReco() {
    try {
        const res = await fetch(`${API}/api/weather/recommendations`);
        if (!res.ok) throw new Error(`Weather recommendations request failed: ${res.status}`);
        const data = await res.json();
        weatherRecoLoaded = true;
        const states = data.states || [];
        const summary = data.national_summary || {};
        const sectors = data.sector_matrix || [];

        // --- National Summary ---
        const summaryEl = document.getElementById('wrNationalSummary');
        if (summaryEl) {
            summaryEl.innerHTML = `
                <div class="wr-summary-banner wr-risk-${summary.overall_risk?.toLowerCase() || 'moderate'}">
                    <div class="wr-summary-headline">
                        <span class="wr-risk-badge">${summary.overall_risk || 'N/A'} RISK</span>
                        <span class="wr-monsoon-countdown">Monsoon in <strong>${summary.monsoon_countdown_days || '—'}</strong> days</span>
                    </div>
                    <p class="wr-headline-text">${summary.headline || ''}</p>
                    <div class="wr-summary-stats">
                        <div class="wr-stat"><span class="wr-stat-num wr-critical">${summary.critical_states || 0}</span><span class="wr-stat-label">Critical States</span></div>
                        <div class="wr-stat"><span class="wr-stat-num wr-high">${summary.high_risk_states || 0}</span><span class="wr-stat-label">High Risk</span></div>
                        <div class="wr-stat"><span class="wr-stat-num wr-alerts">${summary.active_alerts || 0}</span><span class="wr-stat-label">Active Alerts</span></div>
                    </div>
                </div>`;
        }

        // --- State Grid ---
        const stateGrid = document.getElementById('wrStateGrid');
        if (stateGrid) {
            stateGrid.innerHTML = states.map(s => `
                <div class="wr-state-card wr-risk-border-${s.risk_level?.toLowerCase() || 'low'}" onclick="expandStateCard(this)">
                    <div class="wr-state-header">
                        <span class="wr-state-icon">${s.icon || '🌡️'}</span>
                        <div>
                            <h4 class="wr-state-name">${s.state}</h4>
                            <span class="wr-state-condition">${s.condition}</span>
                        </div>
                        <span class="wr-risk-pill wr-risk-${s.risk_level?.toLowerCase() || 'low'}">${s.risk_level}</span>
                    </div>
                    <div class="wr-state-temp">${s.temp_range}</div>
                    <p class="wr-state-forecast">${s.forecast_7d}</p>
                    <div class="wr-state-reco">
                        <strong>Key Recommendations:</strong>
                        <ul>${(s.recommendations || []).map(r => `<li>${r}</li>`).join('')}</ul>
                    </div>
                    <div class="wr-state-sectors">
                        ${Object.entries(s.sectors || {}).map(([k, v]) => `
                            <div class="wr-sector-item">
                                <span class="wr-sector-label">${k.charAt(0).toUpperCase() + k.slice(1)}</span>
                                <span class="wr-sector-detail">${v}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        }

        // --- Sector Impact Matrix ---
        const sectorMatrix = document.getElementById('wrSectorMatrix');
        if (sectorMatrix) {
            sectorMatrix.innerHTML = sectors.map(s => `
                <div class="wr-sector-card">
                    <div class="wr-sector-head">
                        <span class="wr-sector-icon">${s.icon}</span>
                        <h4>${s.sector}</h4>
                        <span class="wr-risk-pill wr-risk-${s.national_risk?.toLowerCase() || 'moderate'}">${s.national_risk}</span>
                    </div>
                    <p class="wr-sector-summary">${s.summary}</p>
                    <div class="wr-sector-meta">
                        <span><strong>${s.affected_states}</strong> states affected</span>
                    </div>
                    <div class="wr-sector-advisory">
                        <strong>Advisory:</strong> ${s.advisory}
                    </div>
                </div>
            `).join('');
        }

    } catch (err) {
        weatherRecoLoaded = false;
        console.error('Weather Reco load error:', err);
    }
}

function expandStateCard(card) {
    card.classList.toggle('expanded');
}

// =================== INCIDENT REPORTING DASHBOARD ===================
async function loadIncidentsDashboard() {
    try {
        const res = await fetch(`${API}/api/incidents`);
        if (!res.ok) throw new Error(`Incidents request failed: ${res.status}`);
        const data = await res.json();
        incidentsLoaded = true;
        allIncidents = data.incidents || [];
        renderIncidentStats(data.stats);
        renderIncidentList(allIncidents);
    } catch (e) {
        incidentsLoaded = false;
        console.error("Failed to load incidents:", e);
        document.getElementById("incidentList").innerHTML = '<p class="muted">Failed to load incidents.</p>';
    }
}

function renderIncidentStats(stats) {
    if (!stats) return;
    document.getElementById("incStatTotal").textContent = stats.total || 0;
    document.getElementById("incStatSubmitted").textContent = stats.submitted || 0;
    document.getElementById("incStatReview").textContent = stats.under_review || 0;
    document.getElementById("incStatProgress").textContent = stats.in_progress || 0;
    document.getElementById("incStatResolved").textContent = stats.resolved || 0;
}

function renderIncidentList(incidents) {
    const container = document.getElementById("incidentList");
    if (!incidents || incidents.length === 0) {
        container.innerHTML = '<p class="muted">No incidents found.</p>';
        return;
    }
    container.innerHTML = incidents.map(inc => {
        const severityEmoji = { critical: "🔴", high: "🟠", moderate: "🟡" };
        const statusClass = inc.status.replace(/\s+/g, "-");
        const date = new Date(inc.reported_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
        return `
            <div class="inc-card">
                <div class="inc-card-header">
                    <span class="inc-id">#INC-${String(inc.id).padStart(4, "0")}</span>
                    <span class="inc-badge inc-badge-${statusClass}">${inc.status.replace(/-/g, " ")}</span>
                </div>
                <h3 class="inc-card-title">${inc.title}</h3>
                <p class="inc-card-desc">${inc.description.length > 120 ? inc.description.substring(0, 120) + "..." : inc.description}</p>
                <div class="inc-card-meta">
                    <span>${severityEmoji[inc.severity] || "🟡"} ${inc.severity}</span>
                    <span>📂 ${inc.category}</span>
                    <span>📍 ${inc.location}</span>
                    <span>📅 ${date}</span>
                </div>
                ${inc.assigned_to ? `<div class="inc-card-assigned">🏛️ Assigned: ${inc.assigned_to}</div>` : ""}
                ${inc.updates && inc.updates.length > 0 ? `
                    <div class="inc-timeline">
                        <strong>Updates:</strong>
                        ${inc.updates.map(u => `<div class="inc-update"><span class="inc-update-time">${new Date(u.timestamp).toLocaleString("en-IN")}</span> — ${u.note} <em>(${u.status})</em></div>`).join("")}
                    </div>
                ` : ""}
            </div>
        `;
    }).join("");
}

async function submitIncident(e) {
    e.preventDefault();
    const statusDiv = document.getElementById("incFormStatus");
    statusDiv.className = "inc-form-status";
    statusDiv.textContent = "Submitting...";

    const payload = {
        title: document.getElementById("incTitle").value.trim(),
        category: document.getElementById("incCategory").value,
        severity: document.getElementById("incSeverity").value,
        description: document.getElementById("incDescription").value.trim(),
        location: document.getElementById("incLocation").value.trim(),
        reported_by: document.getElementById("incReportedBy").value.trim() || "Anonymous Citizen",
        contact: document.getElementById("incContact").value.trim()
    };

    try {
        const res = await fetch(`${API}/api/incidents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        statusDiv.className = "inc-form-status success";
        statusDiv.textContent = `✅ Incident #INC-${String(data.id).padStart(4, "0")} submitted successfully! Assigned to: ${data.assigned_to}`;
        document.getElementById("incidentForm").reset();
        // Reload list
        incidentsLoaded = false;
        loadIncidentsDashboard();
    } catch (err) {
        statusDiv.className = "inc-form-status error";
        statusDiv.textContent = "❌ Failed to submit incident. Please try again.";
    }
}

function incDetectLocation() {
    const input = document.getElementById("incLocation");
    if (!navigator.geolocation) { input.value = "Geolocation not supported"; return; }
    input.value = "Detecting...";
    navigator.geolocation.getCurrentPosition(
        pos => { input.value = `Lat ${pos.coords.latitude.toFixed(5)}, Lng ${pos.coords.longitude.toFixed(5)}`; },
        () => { input.value = "Location detection failed"; },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

function filterIncidents() {
    const status = document.getElementById("incFilterStatus").value;
    const category = document.getElementById("incFilterCategory").value;
    let filtered = allIncidents;
    if (status !== "all") filtered = filtered.filter(i => i.status === status);
    if (category !== "all") filtered = filtered.filter(i => i.category === category);
    renderIncidentList(filtered);
}

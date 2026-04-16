"""
FastAPI Backend — Sanket.AI
"""
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

from app.voice_pipeline import process_voice_query, process_text_query
from app.rag_engine import ingest_documents, get_stats, query as rag_query, get_context_string


# ---------- Agriculture Dashboard Data ----------

# In-memory agriculture dashboard data (in production: from live APIs/databases)
_agriculture_data = {
    "crop_status": [
        {"crop": "Rice (Kharif)", "region": "Punjab", "status": "Healthy", "yield_forecast": "92%", "area_hectares": 3100000, "risk": "low"},
        {"crop": "Wheat (Rabi)", "region": "Uttar Pradesh", "status": "Harvesting", "yield_forecast": "88%", "area_hectares": 9700000, "risk": "low"},
        {"crop": "Soybean", "region": "Maharashtra - Vidarbha", "status": "Water Stress", "yield_forecast": "60%", "area_hectares": 4200000, "risk": "high"},
        {"crop": "Cotton", "region": "Gujarat", "status": "Growing", "yield_forecast": "78%", "area_hectares": 2600000, "risk": "moderate"},
        {"crop": "Groundnut", "region": "Andhra Pradesh", "status": "Healthy", "yield_forecast": "85%", "area_hectares": 1800000, "risk": "low"},
        {"crop": "Tea", "region": "Assam", "status": "First Flush", "yield_forecast": "95%", "area_hectares": 320000, "risk": "low"},
        {"crop": "Coffee", "region": "Kerala - Wayanad", "status": "Yield Drop", "yield_forecast": "75%", "area_hectares": 85000, "risk": "high"},
        {"crop": "Paddy (Samba)", "region": "Tamil Nadu", "status": "Sowing", "yield_forecast": "82%", "area_hectares": 1520000, "risk": "moderate"},
        {"crop": "Sugarcane", "region": "Karnataka", "status": "Growing", "yield_forecast": "90%", "area_hectares": 520000, "risk": "low"},
        {"crop": "Mustard", "region": "Rajasthan", "status": "Harvested", "yield_forecast": "87%", "area_hectares": 3100000, "risk": "low"},
    ],
    "weather_alerts": [
        {"region": "Vidarbha, Maharashtra", "type": "Drought", "severity": "HIGH", "description": "30% below-normal rainfall. Soil moisture critically low at 45%. Soybean & cotton at risk.", "date": "2026-04-10"},
        {"region": "Assam - Brahmaputra Belt", "type": "Flood", "severity": "CRITICAL", "description": "Brahmaputra at 49.2m vs danger mark 49.68m. Rice paddies in low-lying areas at risk of submersion.", "date": "2026-04-12"},
        {"region": "Western Rajasthan", "type": "Heatwave", "severity": "HIGH", "description": "Temperatures 46-48°C forecast. Wheat post-harvest storage at risk. Livestock heat stress advisory.", "date": "2026-04-14"},
        {"region": "Uttarakhand Hills", "type": "Landslide", "severity": "MODERATE", "description": "Monsoon pre-season rainfall causing soil saturation. Apple orchards in Shimla-Kullu belt at risk.", "date": "2026-04-13"},
        {"region": "Odisha Coast", "type": "Cyclone Risk", "severity": "MODERATE", "description": "Low pressure forming in Bay of Bengal. Paddy harvest in coastal districts may need early scheduling.", "date": "2026-04-15"},
        {"region": "Punjab-Haryana", "type": "Stubble Burning", "severity": "LOW", "description": "Post-harvest residue management advisory. Air quality impact on next sowing cycle.", "date": "2026-04-08"},
    ],
    "hygiene_reports": [
        {"region": "Bihar - Muzaffarpur", "issue": "Water Contamination", "severity": "CRITICAL", "details": "35% tube wells show E.coli. Post-flood contamination affecting farmworker health. 340 cholera cases.", "affected_population": 125000},
        {"region": "UP - Gorakhpur", "issue": "Japanese Encephalitis", "severity": "HIGH", "details": "180 suspected cases near rice paddies. Stagnant water breeding mosquitoes. Vaccination at 62%.", "affected_population": 85000},
        {"region": "Maharashtra - Pune", "issue": "Dengue in Farm Belt", "severity": "HIGH", "details": "2,100 cases. Post-monsoon Aedes breeding in irrigation channels and stored water containers.", "affected_population": 200000},
        {"region": "Rajasthan - Barmer", "issue": "Heat Stroke in Workers", "severity": "MODERATE", "details": "1,200 heat stroke cases among agricultural laborers. 48°C peak temperatures during harvest.", "affected_population": 50000},
        {"region": "Kerala - Wayanad", "issue": "Pesticide Exposure", "severity": "MODERATE", "details": "Increased respiratory complaints among coffee plantation workers. Improper PPE usage reported.", "affected_population": 12000},
        {"region": "Odisha - Tribal Belt", "issue": "Malaria in Farmlands", "severity": "HIGH", "details": "P.falciparum cases up 60% near irrigated fields. Drug resistance detected in 3% of samples.", "affected_population": 95000},
    ],
    "mandi_prices": [
        {"crop": "Wheat", "mandi": "Indore", "price_per_quintal": 2420, "msp": 2375, "trend": "up"},
        {"crop": "Rice", "mandi": "Karnal", "price_per_quintal": 2280, "msp": 2300, "trend": "down"},
        {"crop": "Soybean", "mandi": "Latur", "price_per_quintal": 4650, "msp": 4600, "trend": "up"},
        {"crop": "Cotton", "mandi": "Rajkot", "price_per_quintal": 6800, "msp": 7020, "trend": "down"},
        {"crop": "Groundnut", "mandi": "Junagadh", "price_per_quintal": 5950, "msp": 6220, "trend": "down"},
        {"crop": "Mustard", "mandi": "Jaipur", "price_per_quintal": 5450, "msp": 5650, "trend": "down"},
        {"crop": "Sugarcane", "mandi": "Kolhapur", "price_per_quintal": 350, "msp": 315, "trend": "up"},
        {"crop": "Tea (CTC)", "mandi": "Guwahati", "price_per_quintal": 28500, "msp": 0, "trend": "up"},
    ],
    "seasonal_recommendations": [
        {
            "season": "Kharif (June–October)",
            "icon": "🌧️",
            "best_crops": ["Rice", "Maize", "Soybean", "Cotton", "Groundnut", "Sugarcane", "Jowar", "Bajra", "Tur Dal"],
            "fertilizers": [
                {"name": "Urea (46-0-0)", "usage": "Basal + top-dressing at 30 & 60 days. 120-150 kg/ha for rice, 80-100 kg/ha for maize.", "type": "Nitrogen"},
                {"name": "DAP (18-46-0)", "usage": "Basal application at sowing. 100-125 kg/ha. Promotes root development in monsoon waterlogging.", "type": "Phosphorus"},
                {"name": "MOP (0-0-60)", "usage": "50-60 kg/ha basal. Critical for cotton & sugarcane stalk strength during monsoon winds.", "type": "Potassium"},
                {"name": "Zinc Sulphate", "usage": "25 kg/ha for rice paddies. Prevents khaira disease in waterlogged conditions.", "type": "Micronutrient"},
                {"name": "Neem-coated Urea", "usage": "Slow-release nitrogen. Reduces leaching loss by 15-20% during heavy monsoon rains.", "type": "Nitrogen"},
            ],
            "prevention_tips": [
                "Prepare field bunds & drainage channels before monsoon onset to prevent waterlogging",
                "Use short-duration rice varieties (PR-126, Pusa-44) if monsoon is delayed",
                "Apply Trichoderma bio-fungicide to seed before sowing to prevent root rot in wet conditions",
                "Install pheromone traps for bollworm in cotton fields by mid-July",
                "Maintain 5-7cm standing water in rice paddies — excess water reduces tillering",
            ],
        },
        {
            "season": "Rabi (November–March)",
            "icon": "❄️",
            "best_crops": ["Wheat", "Mustard", "Barley", "Gram (Chana)", "Peas", "Lentil (Masoor)", "Potato", "Sunflower"],
            "fertilizers": [
                {"name": "DAP (18-46-0)", "usage": "125 kg/ha at sowing for wheat. Essential for early root establishment in cool soil.", "type": "Phosphorus"},
                {"name": "Urea (46-0-0)", "usage": "Split application: 1/3 basal, 1/3 at first irrigation (21 days), 1/3 at second irrigation (45 days).", "type": "Nitrogen"},
                {"name": "SSP (0-16-0)", "usage": "250 kg/ha for mustard. Provides phosphorus + sulphur for oil content improvement.", "type": "Phosphorus"},
                {"name": "Potash (MOP)", "usage": "40-50 kg/ha for potato. Improves tuber size and storage quality.", "type": "Potassium"},
                {"name": "Borax", "usage": "10 kg/ha for mustard. Prevents flower drop and improves seed setting in cold weather.", "type": "Micronutrient"},
            ],
            "prevention_tips": [
                "Light irrigation before frost nights (Dec-Jan) to protect wheat at flowering stage",
                "Apply 1% Bordeaux mixture on potato 45 days after planting to prevent late blight",
                "Avoid excess nitrogen in gram — promotes vegetative growth over pod formation",
                "Mustard: sow by Oct 25 (irrigated) or Oct 15 (rainfed) to escape aphid peak in Feb",
                "Use yellow sticky traps for whitefly monitoring in mustard from January onwards",
            ],
        },
        {
            "season": "Zaid (March–June)",
            "icon": "☀️",
            "best_crops": ["Watermelon", "Muskmelon", "Cucumber", "Moong Dal", "Sunflower", "Fodder crops", "Bitter Gourd"],
            "fertilizers": [
                {"name": "Vermicompost", "usage": "5 tonnes/ha. Improves water retention in summer-stressed soil. Mix before sowing.", "type": "Organic"},
                {"name": "NPK 10-26-26", "usage": "150 kg/ha for cucurbits. Balanced nutrition for rapid fruiting in short season.", "type": "Complex"},
                {"name": "Calcium Nitrate", "usage": "25 kg/ha foliar spray. Prevents blossom-end rot in watermelon & tomato during heat.", "type": "Calcium"},
                {"name": "Humic Acid", "usage": "2 litres/ha with irrigation. Improves nutrient uptake efficiency in heat-stressed crops.", "type": "Organic"},
            ],
            "prevention_tips": [
                "Mulch with paddy straw (5cm layer) to conserve soil moisture & reduce ground temperature by 4-5°C",
                "Irrigate in early morning or late evening — avoid midday to reduce evaporation loss by 30%",
                "Moong: sow immediately after wheat harvest to utilize residual soil moisture",
                "Use shade nets (50%) for nursery plants during May heatwave period",
                "Apply neem oil (5ml/litre) weekly for sucking pest control — whitefly peaks in April-May",
            ],
        },
    ],
    "unpredicted_rain_advisory": [
        {
            "scenario": "Unseasonal Rain During Wheat Harvest (March-April)",
            "severity": "HIGH",
            "affected_crops": ["Wheat", "Gram", "Mustard"],
            "impact": "Grain discoloration, sprouting in ears, shriveling. Wheat quality downgrade by 15-20%. MSP rejection risk.",
            "immediate_actions": [
                "Harvest standing mature wheat within 24 hours if rain forecast exceeds 20mm",
                "Do NOT stack harvested bundles in open — use tarpaulin or move to covered threshing floor",
                "Run combine harvester at reduced speed to minimize grain breakage of rain-soaked crop",
                "If wheat already cut, dry on elevated platforms (not ground) to prevent mold within 48 hours",
            ],
            "prevention_measures": [
                "Pre-position tarpaulins at procurement centers by February-end",
                "Insure crop under PMFBY (Pradhan Mantri Fasal Bima Yojana) — claim within 72 hours of damage",
                "Grow short-duration varieties (HD-3226, DBW-187) that mature 7-10 days earlier",
                "Coordinate with FCI for early procurement window to minimize field exposure",
            ],
        },
        {
            "scenario": "Heavy Rain During Kharif Sowing (June Start)",
            "severity": "MODERATE",
            "affected_crops": ["Soybean", "Cotton", "Maize"],
            "impact": "Seed rot, poor germination (below 50%), waterlogging in flat fields. Re-sowing cost ₹3,000-5,000/ha.",
            "immediate_actions": [
                "Drain excess water from soybean fields within 24 hours — crop cannot survive 48h waterlogging",
                "If germination below 50%, re-sow with treated seed within 7 days of rain event",
                "Apply Thiram/Captan seed treatment (3g/kg seed) for re-sowing to prevent damping-off",
                "For cotton, raise nursery on elevated beds and transplant when field drains",
            ],
            "prevention_measures": [
                "Use broad bed & furrow (BBF) method for soybean — improves drainage by 40%",
                "Keep 20% extra seed stock for emergency re-sowing",
                "Install field drainage at 0.5% slope before monsoon onset",
                "Prefer ridge sowing for cotton to keep root zone above waterlog level",
            ],
        },
        {
            "scenario": "Hailstorm During Flowering (Feb-March)",
            "severity": "CRITICAL",
            "affected_crops": ["Mango", "Grape", "Wheat", "Mustard", "Vegetables"],
            "impact": "70-100% flower/fruit drop in mango & grape. Wheat ear damage. Total loss possible for open-field vegetables.",
            "immediate_actions": [
                "Spray 0.1% Boron + 1% Urea solution within 24 hours to promote recovery flowering",
                "Remove damaged fruit/branches from orchard floor to prevent fungal infection",
                "Apply copper oxychloride fungicide spray within 48 hours to hail-wounded plant tissue",
                "For vegetables, harvest whatever is salvageable immediately — damaged produce degrades within 2 days",
            ],
            "prevention_measures": [
                "Install anti-hail nets (HDPE 35gsm) over high-value crops — mango, grape, pomegranate",
                "Insure orchard crops under restructured weather-based crop insurance scheme",
                "Maintain windbreak tree lines (Casuarina, Eucalyptus) around orchards",
                "Diversify: don't plant 100% of area with single flowering-stage crop",
            ],
        },
        {
            "scenario": "Dry Spell Mid-Monsoon (July-August Break)",
            "severity": "HIGH",
            "affected_crops": ["Rice", "Soybean", "Cotton", "Maize"],
            "impact": "Rice tillering failure, soybean flower drop. Yield loss 30-50% if dry spell exceeds 15 days during reproductive stage.",
            "immediate_actions": [
                "Prioritize irrigation for crops at flowering/grain-filling stage over vegetative stage",
                "Apply 2% KCl (Potassium Chloride) foliar spray to improve drought tolerance",
                "Thin out excess tillers in rice to reduce water demand per plant",
                "Skip one urea top-dressing — excess nitrogen increases water stress vulnerability",
            ],
            "prevention_measures": [
                "Build farm ponds (20m x 20m x 3m) to harvest initial monsoon rain for supplemental irrigation",
                "Use System of Rice Intensification (SRI) — saves 40% water vs conventional puddled transplanting",
                "Select drought-tolerant varieties: Sahbhagi Dhan (rice), JS 95-60 (soybean)",
                "Apply mulch between crop rows to reduce evaporation loss by 25-30%",
            ],
        },
    ],
}


# =================== Imports & Lifespan (must be before app) ===================
from app.alert_engine import (
    run_alert_check,
    get_active_alerts,
    get_all_alerts,
    acknowledge_alert,
    translate_alert,
)
from app.sample_data import seed_sample_data
from app.sarvam_client import text_to_speech, translate_text

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    seed_sample_data()
    _ingest_live_events_to_rag()
    scheduler.add_job(run_alert_check, "interval", minutes=60, id="alert_check")
    scheduler.start()
    yield
    scheduler.shutdown()


# =================== App Instance (must be before any @app routes) ===================
app = FastAPI(
    title="Sanket.AI",
    description="AI-Powered Public Intelligence & Civilian Safety Platform using Sarvam AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/api/agriculture/dashboard")
async def agriculture_dashboard():
    """Get full agriculture dashboard data"""
    return _agriculture_data


@app.get("/api/agriculture/crops")
async def agriculture_crops():
    """Get crop status data"""
    return {"crops": _agriculture_data["crop_status"]}


@app.get("/api/agriculture/weather")
async def agriculture_weather():
    """Get weather alerts affecting agriculture"""
    return {"weather_alerts": _agriculture_data["weather_alerts"]}


@app.get("/api/agriculture/hygiene")
async def agriculture_hygiene():
    """Get hygiene / health reports for agricultural regions"""
    return {"hygiene_reports": _agriculture_data["hygiene_reports"]}


@app.get("/api/agriculture/prices")
async def agriculture_prices():
    """Get mandi crop prices"""
    return {"mandi_prices": _agriculture_data["mandi_prices"]}


@app.get("/api/agriculture/insights")
async def agriculture_insights(q: str = "agriculture crop weather forecast India"):
    """Get RAG-powered agriculture insights"""
    context = get_context_string(q, sector="agriculture")
    return {"query": q, "insights": context}


@app.get("/api/agriculture/recommendations")
async def agriculture_recommendations():
    """Get seasonal crop & fertilizer recommendations"""
    return {"seasonal_recommendations": _agriculture_data["seasonal_recommendations"]}


@app.get("/api/agriculture/rain-advisory")
async def agriculture_rain_advisory():
    """Get unpredicted rain impact advisory"""
    return {"unpredicted_rain_advisory": _agriculture_data["unpredicted_rain_advisory"]}


# ---------- Public Health & Disease Dashboard Data ----------

_health_data = {
    "disease_outbreaks": [
        {
            "disease": "Dengue Fever",
            "status": "Active Outbreak",
            "severity": "high",
            "region": "Maharashtra — Pune, Mumbai, Nagpur",
            "affected_districts": 14,
            "active_cases": 8500,
            "deaths": 23,
            "trend": "rising",
            "week_change": "+40%",
            "transmission": "Mosquito-borne (Aedes aegypti)",
            "symptoms": ["High fever", "Severe headache", "Joint/muscle pain", "Skin rash", "Bleeding gums"],
            "prevention": [
                "Eliminate stagnant water sources — flower pots, tyres, coolers",
                "Use mosquito nets and DEET-based repellents",
                "Wear full-sleeve clothing during dawn and dusk",
                "Community fogging operations in hotspot wards",
                "Report fever lasting >2 days to nearest PHC immediately",
            ],
            "last_updated": "2026-04-14",
        },
        {
            "disease": "Cholera",
            "status": "Active Outbreak",
            "severity": "critical",
            "region": "Bihar — Muzaffarpur, East Champaran",
            "affected_districts": 5,
            "active_cases": 340,
            "deaths": 12,
            "trend": "stable",
            "week_change": "+5%",
            "transmission": "Waterborne (contaminated drinking water)",
            "symptoms": ["Severe watery diarrhea", "Vomiting", "Rapid dehydration", "Leg cramps", "Low blood pressure"],
            "prevention": [
                "Boil or chlorinate drinking water — 35% tube wells contaminated",
                "Use ORS (Oral Rehydration Solution) at first sign of watery diarrhea",
                "Avoid street food and uncooked vegetables in affected areas",
                "Wash hands with soap before eating and after toilet use",
                "Report any case of acute watery diarrhea to district health officer within 24 hours",
            ],
            "last_updated": "2026-04-13",
        },
        {
            "disease": "Japanese Encephalitis",
            "status": "Seasonal Alert",
            "severity": "high",
            "region": "UP — Gorakhpur, Eastern UP",
            "affected_districts": 8,
            "active_cases": 180,
            "deaths": 8,
            "trend": "rising",
            "week_change": "+22%",
            "transmission": "Mosquito-borne (Culex — breeds in rice paddies)",
            "symptoms": ["High fever", "Headache", "Neck stiffness", "Confusion/seizures", "Paralysis (severe)"],
            "prevention": [
                "JE vaccination for all children 1-15 years — current coverage only 62%",
                "Drain stagnant water from rice fields weekly during non-critical growth stages",
                "Use insecticide-treated bed nets (ITNs) — especially for children",
                "Pig farming should be relocated >5km from residential areas (pigs are amplifying hosts)",
                "Report any fever with altered consciousness to BRD Medical College hotline",
            ],
            "last_updated": "2026-04-12",
        },
        {
            "disease": "Malaria (P.falciparum)",
            "status": "Endemic Alert",
            "severity": "high",
            "region": "Odisha — Koraput, Malkangiri, Rayagada",
            "affected_districts": 11,
            "active_cases": 4200,
            "deaths": 15,
            "trend": "declining",
            "week_change": "-12%",
            "transmission": "Mosquito-borne (Anopheles — breeds near irrigation canals)",
            "symptoms": ["Cyclic fever with chills", "Sweating", "Fatigue", "Nausea/vomiting", "Anemia"],
            "prevention": [
                "Sleep under LLIN (Long-Lasting Insecticidal Net) every night — coverage at 95%",
                "Indoor Residual Spraying (IRS) in high-risk tribal villages every 3 months",
                "Rapid Diagnostic Test (RDT) within 24 hours for any fever case in endemic area",
                "ACT (Artemisinin Combination Therapy) — monitor for drug resistance (3% detected)",
                "Clear vegetation and drain breeding sites within 500m of habitation",
            ],
            "last_updated": "2026-04-14",
        },
        {
            "disease": "Nipah Virus",
            "status": "Level 2 Alert (Surveillance)",
            "severity": "moderate",
            "region": "Kerala — Kozhikode",
            "affected_districts": 1,
            "active_cases": 1,
            "deaths": 0,
            "trend": "stable",
            "week_change": "0%",
            "transmission": "Zoonotic (fruit bats) — person-to-person via body fluids",
            "symptoms": ["Fever", "Headache", "Drowsiness", "Respiratory distress", "Encephalitis"],
            "prevention": [
                "Do NOT consume fallen/partially eaten fruits (bat contamination risk)",
                "Avoid contact with sick pigs and bat colonies",
                "Healthcare workers must use full PPE (N95 + gown + eye shield) for suspect cases",
                "500-bed isolation facility on standby at Kozhikode Medical College",
                "Report any cluster of encephalitis-like illness to district surveillance unit",
            ],
            "last_updated": "2026-04-10",
        },
        {
            "disease": "Heat-Related Illness",
            "status": "Seasonal Active",
            "severity": "high",
            "region": "Rajasthan — Barmer, Jodhpur, Jaisalmer",
            "affected_districts": 9,
            "active_cases": 1200,
            "deaths": 34,
            "trend": "rising",
            "week_change": "+60%",
            "transmission": "Environmental (extreme heat exposure >45°C)",
            "symptoms": ["Body temp >40°C", "Confusion/delirium", "Hot dry skin", "Rapid pulse", "Loss of consciousness"],
            "prevention": [
                "Avoid outdoor work between 11 AM – 4 PM during heat advisory days",
                "Drink ORS/water every 20 minutes when working outdoors — minimum 6 litres/day",
                "Public cooling centers operational at 250 locations — seek shade immediately if dizzy",
                "Employers must provide shaded rest areas and water stations for outdoor workers",
                "Transport heat stroke patients to hospital IMMEDIATELY — mortality >50% if treatment delayed >2 hours",
            ],
            "last_updated": "2026-04-15",
        },
        {
            "disease": "Tuberculosis (MDR-TB)",
            "status": "Endemic — High Burden",
            "severity": "high",
            "region": "Uttar Pradesh — Lucknow, Varanasi, Allahabad",
            "affected_districts": 22,
            "active_cases": 52000,
            "deaths": 890,
            "trend": "stable",
            "week_change": "+2%",
            "transmission": "Airborne (Mycobacterium tuberculosis — droplet nuclei)",
            "symptoms": ["Persistent cough >2 weeks", "Weight loss", "Night sweats", "Blood in sputum", "Fatigue"],
            "prevention": [
                "Free DOTS treatment available at all govt PHCs — complete full 6-month course",
                "CBNAAT/TrueNat rapid testing for all presumptive TB cases within 48 hours",
                "Contact tracing for all confirmed cases — screen household members within 7 days",
                "Nutritional support (Nikshay Poshan Yojana) ₹500/month for all TB patients",
                "Ventilate closed spaces, use N95 mask in crowded indoor settings in high-burden areas",
            ],
            "last_updated": "2026-04-15",
        },
        {
            "disease": "Acute Diarrheal Disease",
            "status": "Seasonal Spike",
            "severity": "moderate",
            "region": "Assam — Flood-Affected Districts",
            "affected_districts": 15,
            "active_cases": 6800,
            "deaths": 18,
            "trend": "rising",
            "week_change": "+35%",
            "transmission": "Waterborne/fecal-oral (post-flood contamination)",
            "symptoms": ["Watery stools >3 times/day", "Abdominal cramps", "Nausea", "Dehydration", "Fever"],
            "prevention": [
                "Distribute ORS packets and chlorine tablets in all flood relief camps",
                "Set up temporary water purification units in 15 worst-affected districts",
                "No open defecation — use portable toilets provided at relief camps",
                "Handwashing stations every 50 metres in relief camps",
                "Monitor all children <5 for dehydration — refer immediately if sunken eyes or skin tenting",
            ],
            "last_updated": "2026-04-14",
        },
    ],
    "vaccination_status": [
        {"program": "COVID-19 (Booster)", "target_group": "18+ years", "coverage_percent": 72, "target": 90, "doses_administered": 2180000000, "status": "Ongoing"},
        {"program": "JE Vaccination", "target_group": "1-15 years (Endemic)", "coverage_percent": 62, "target": 90, "doses_administered": 48000000, "status": "Below Target"},
        {"program": "Pulse Polio (OPV)", "target_group": "0-5 years", "coverage_percent": 97, "target": 100, "doses_administered": 121000000, "status": "On Track"},
        {"program": "Measles-Rubella (MR)", "target_group": "9 months - 15 years", "coverage_percent": 88, "target": 95, "doses_administered": 345000000, "status": "Ongoing"},
        {"program": "BCG (Tuberculosis)", "target_group": "Newborns", "coverage_percent": 93, "target": 100, "doses_administered": 25000000, "status": "On Track"},
        {"program": "Hepatitis B (Birth Dose)", "target_group": "Newborns (0 dose)", "coverage_percent": 85, "target": 95, "doses_administered": 23000000, "status": "Ongoing"},
        {"program": "Pentavalent (DPT+HepB+Hib)", "target_group": "6-14 weeks", "coverage_percent": 91, "target": 95, "doses_administered": 78000000, "status": "On Track"},
        {"program": "Rotavirus Vaccine", "target_group": "6-14 weeks", "coverage_percent": 68, "target": 90, "doses_administered": 42000000, "status": "Scale-up Phase"},
    ],
    "water_sanitation": [
        {"region": "Bihar — Muzaffarpur", "water_quality": "Unsafe", "contamination_source": "E.coli in 35% tube wells (post-flood)", "odf_status": "Non-ODF", "sanitation_score": 32},
        {"region": "Jharkhand — Tribal Belt", "water_quality": "Unsafe", "contamination_source": "Open defecation near water sources", "odf_status": "Non-ODF", "sanitation_score": 38},
        {"region": "Rajasthan — Barmer", "water_quality": "Moderate", "contamination_source": "Fluoride >1.5ppm in groundwater", "odf_status": "ODF", "sanitation_score": 55},
        {"region": "Assam — Flood Areas", "water_quality": "Unsafe", "contamination_source": "Flood debris & sewage mixing", "odf_status": "Non-ODF", "sanitation_score": 25},
        {"region": "MP — Bundelkhand", "water_quality": "Moderate", "contamination_source": "Shared contaminated sources (scarcity)", "odf_status": "ODF", "sanitation_score": 52},
        {"region": "Tamil Nadu — Chennai", "water_quality": "Safe", "contamination_source": "None — chlorinated municipal supply", "odf_status": "ODF+", "sanitation_score": 82},
        {"region": "Kerala — Ernakulam", "water_quality": "Safe", "contamination_source": "None", "odf_status": "ODF+", "sanitation_score": 91},
    ],
    "hospital_capacity": [
        {"region": "Maharashtra", "total_beds": 185000, "available_beds": 46250, "icu_beds": 8500, "icu_available": 4200, "ventilators": 4200, "ventilators_available": 2100, "status": "Moderate Load"},
        {"region": "Bihar", "total_beds": 42000, "available_beds": 5040, "icu_beds": 1200, "icu_available": 580, "ventilators": 480, "ventilators_available": 210, "status": "High Load"},
        {"region": "Uttar Pradesh", "total_beds": 165000, "available_beds": 49500, "icu_beds": 7600, "icu_available": 3800, "ventilators": 3300, "ventilators_available": 1650, "status": "Normal"},
        {"region": "Rajasthan", "total_beds": 78000, "available_beds": 14040, "icu_beds": 3000, "icu_available": 1500, "ventilators": 1360, "ventilators_available": 680, "status": "Elevated"},
        {"region": "Kerala", "total_beds": 95000, "available_beds": 42750, "icu_beds": 6400, "icu_available": 3200, "ventilators": 3600, "ventilators_available": 1800, "status": "Normal"},
        {"region": "Odisha", "total_beds": 48000, "available_beds": 16800, "icu_beds": 1960, "icu_available": 980, "ventilators": 840, "ventilators_available": 420, "status": "Normal"},
    ],
    "public_safety_alerts": [
        {
            "alert_type": "Food Adulteration",
            "region": "Delhi NCR",
            "severity": "high",
            "date_issued": "2026-04-12",
            "description": "FSSAI raids reveal 22% milk samples adulterated with detergent/urea. 150 FIRs filed. Consumer advisory: buy only from verified brands/cooperatives.",
            "action_required": [
                "Avoid purchasing loose/unpackaged milk from unverified vendors",
                "Report suspected adulteration to FSSAI helpline 1800-112-100",
                "Check FSSAI license number on packaged dairy products",
            ],
        },
        {
            "alert_type": "Air Quality Emergency",
            "region": "Delhi — NCR",
            "severity": "critical",
            "date_issued": "2026-04-14",
            "description": "AQI 380+ (Severe). PM2.5 at 6x safe limit. Schools closed for 3 days. Outdoor activities banned. N95 mask advisory. Construction halted.",
            "action_required": [
                "Stay indoors — close windows and use air purifiers if available",
                "Wear N95 mask if outdoor exposure unavoidable",
                "Avoid morning walks and outdoor exercise until AQI drops below 200",
                "Persons with asthma/COPD should keep emergency inhalers accessible",
            ],
        },
        {
            "alert_type": "Drug Recall — Paracetamol",
            "region": "Pan-India",
            "severity": "moderate",
            "date_issued": "2026-04-11",
            "description": "CDSCO recalls batch of paracetamol 500mg (Batch MF-2026-034) — microbial contamination detected. Return to pharmacist for replacement.",
            "action_required": [
                "Check batch number MF-2026-034 on paracetamol 500mg strips",
                "Return matching strips to nearest pharmacy for free replacement",
                "Contact CDSCO helpline 1800-11-1454 for queries",
            ],
        },
        {
            "alert_type": "Water Supply Warning",
            "region": "Chennai",
            "severity": "high",
            "date_issued": "2026-04-13",
            "description": "Reservoir levels at 28% of capacity. Water rationing initiated — alternate day supply in zones 5-12. Tanker requests via helpline 1916.",
            "action_required": [
                "Store water during supply hours — alternate day schedule in zones 5-12",
                "Request water tanker via helpline 1916 or Chennai Metro Water app",
                "Report water theft or pipeline leaks to local ward office",
                "Avoid using potable water for car washing or garden irrigation",
            ],
        },
        {
            "alert_type": "Radiation Containment",
            "region": "Mumbai — Thane",
            "severity": "low",
            "date_issued": "2026-04-09",
            "description": "Routine AERB inspection found expired radioactive source in scrapyard. Contained. No public exposure detected. Area cordoned for 48 hours.",
            "action_required": [
                "No immediate action required for general public",
                "Avoid the cordoned area in Thane industrial zone for 48 hours",
                "Scrap dealers must report any suspicious metal objects to AERB hotline",
            ],
        },
    ],
}


@app.get("/api/health/dashboard")
async def health_dashboard():
    """Get full public health & disease dashboard data"""
    return _health_data


@app.get("/api/health/outbreaks")
async def health_outbreaks():
    """Get active disease outbreaks"""
    return {"disease_outbreaks": _health_data["disease_outbreaks"]}


@app.get("/api/health/vaccination")
async def health_vaccination():
    """Get vaccination program status"""
    return {"vaccination_status": _health_data["vaccination_status"]}


@app.get("/api/health/sanitation")
async def health_sanitation():
    """Get water & sanitation reports"""
    return {"water_sanitation": _health_data["water_sanitation"]}


@app.get("/api/health/hospitals")
async def health_hospitals():
    """Get hospital capacity data"""
    return {"hospital_capacity": _health_data["hospital_capacity"]}


@app.get("/api/health/safety")
async def health_safety():
    """Get public safety alerts"""
    return {"public_safety_alerts": _health_data["public_safety_alerts"]}


# ===================== WEATHER FORECASTING DATA =====================
_weather_data = {
    "current_conditions": [
        {"city": "Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090, "temp_c": 42, "feels_like": 46, "humidity": 18, "wind_kph": 22, "wind_dir": "W", "condition": "Extreme Heat", "icon": "☀️", "aqi": 185, "uv_index": 11, "pressure_hpa": 1004, "visibility_km": 4},
        {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "temp_c": 34, "feels_like": 40, "humidity": 72, "wind_kph": 14, "wind_dir": "SW", "condition": "Humid & Hazy", "icon": "🌤️", "aqi": 120, "uv_index": 9, "pressure_hpa": 1008, "visibility_km": 6},
        {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "temp_c": 37, "feels_like": 42, "humidity": 65, "wind_kph": 18, "wind_dir": "SE", "condition": "Hot & Humid", "icon": "🌤️", "aqi": 95, "uv_index": 10, "pressure_hpa": 1006, "visibility_km": 8},
        {"city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "temp_c": 36, "feels_like": 43, "humidity": 78, "wind_kph": 12, "wind_dir": "S", "condition": "Thunderstorm Alert", "icon": "⛈️", "aqi": 110, "uv_index": 7, "pressure_hpa": 1002, "visibility_km": 5},
        {"city": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "temp_c": 29, "feels_like": 31, "humidity": 55, "wind_kph": 10, "wind_dir": "E", "condition": "Partly Cloudy", "icon": "⛅", "aqi": 65, "uv_index": 8, "pressure_hpa": 1012, "visibility_km": 12},
        {"city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "temp_c": 44, "feels_like": 48, "humidity": 12, "wind_kph": 28, "wind_dir": "W", "condition": "Heat Wave", "icon": "🔥", "aqi": 160, "uv_index": 12, "pressure_hpa": 1001, "visibility_km": 3},
        {"city": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "temp_c": 30, "feels_like": 35, "humidity": 82, "wind_kph": 8, "wind_dir": "SE", "condition": "Heavy Rain", "icon": "🌧️", "aqi": 55, "uv_index": 4, "pressure_hpa": 1000, "visibility_km": 3},
        {"city": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "temp_c": 41, "feels_like": 44, "humidity": 22, "wind_kph": 20, "wind_dir": "NW", "condition": "Very Hot", "icon": "☀️", "aqi": 175, "uv_index": 11, "pressure_hpa": 1003, "visibility_km": 5},
        {"city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867, "temp_c": 38, "feels_like": 41, "humidity": 35, "wind_kph": 16, "wind_dir": "NW", "condition": "Hot & Dry", "icon": "☀️", "aqi": 78, "uv_index": 10, "pressure_hpa": 1007, "visibility_km": 9},
        {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "temp_c": 43, "feels_like": 47, "humidity": 14, "wind_kph": 25, "wind_dir": "W", "condition": "Heat Wave", "icon": "🔥", "aqi": 145, "uv_index": 12, "pressure_hpa": 1002, "visibility_km": 4},
        {"city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "temp_c": 35, "feels_like": 37, "humidity": 30, "wind_kph": 12, "wind_dir": "W", "condition": "Hot & Clear", "icon": "☀️", "aqi": 72, "uv_index": 10, "pressure_hpa": 1009, "visibility_km": 10},
        {"city": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "temp_c": 38, "feels_like": 40, "humidity": 20, "wind_kph": 18, "wind_dir": "NW", "condition": "Hot & Dry", "icon": "☀️", "aqi": 135, "uv_index": 11, "pressure_hpa": 1005, "visibility_km": 6},
        {"city": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "temp_c": 40, "feels_like": 43, "humidity": 18, "wind_kph": 15, "wind_dir": "W", "condition": "Extreme Heat", "icon": "☀️", "aqi": 130, "uv_index": 11, "pressure_hpa": 1004, "visibility_km": 6},
        {"city": "Patna", "state": "Bihar", "lat": 25.6093, "lon": 85.1376, "temp_c": 38, "feels_like": 44, "humidity": 55, "wind_kph": 10, "wind_dir": "SE", "condition": "Hot & Humid", "icon": "🌤️", "aqi": 155, "uv_index": 10, "pressure_hpa": 1003, "visibility_km": 5},
        {"city": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245, "temp_c": 36, "feels_like": 42, "humidity": 68, "wind_kph": 14, "wind_dir": "S", "condition": "Humid & Warm", "icon": "🌤️", "aqi": 88, "uv_index": 9, "pressure_hpa": 1005, "visibility_km": 7},
        {"city": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366, "temp_c": 32, "feels_like": 38, "humidity": 80, "wind_kph": 10, "wind_dir": "W", "condition": "Pre-Monsoon Showers", "icon": "🌦️", "aqi": 42, "uv_index": 9, "pressure_hpa": 1008, "visibility_km": 8},
        {"city": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "temp_c": 22, "feels_like": 21, "humidity": 45, "wind_kph": 12, "wind_dir": "W", "condition": "Pleasant & Cool", "icon": "⛅", "aqi": 32, "uv_index": 6, "pressure_hpa": 1015, "visibility_km": 15},
        {"city": "Srinagar", "state": "Jammu & Kashmir", "lat": 34.0837, "lon": 74.7973, "temp_c": 18, "feels_like": 16, "humidity": 50, "wind_kph": 8, "wind_dir": "NW", "condition": "Cool & Breezy", "icon": "🌤️", "aqi": 28, "uv_index": 5, "pressure_hpa": 1016, "visibility_km": 18},
        {"city": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096, "temp_c": 35, "feels_like": 39, "humidity": 50, "wind_kph": 12, "wind_dir": "S", "condition": "Thunderstorm Risk", "icon": "⛈️", "aqi": 95, "uv_index": 8, "pressure_hpa": 1004, "visibility_km": 7},
        {"city": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296, "temp_c": 39, "feels_like": 42, "humidity": 25, "wind_kph": 14, "wind_dir": "W", "condition": "Very Hot", "icon": "☀️", "aqi": 110, "uv_index": 11, "pressure_hpa": 1005, "visibility_km": 6},
        {"city": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "temp_c": 32, "feels_like": 34, "humidity": 35, "wind_kph": 10, "wind_dir": "NW", "condition": "Warm & Clear", "icon": "☀️", "aqi": 55, "uv_index": 9, "pressure_hpa": 1010, "visibility_km": 10},
        {"city": "Imphal", "state": "Manipur", "lat": 24.8170, "lon": 93.9368, "temp_c": 27, "feels_like": 30, "humidity": 75, "wind_kph": 6, "wind_dir": "SE", "condition": "Light Rain", "icon": "🌧️", "aqi": 38, "uv_index": 5, "pressure_hpa": 1004, "visibility_km": 6},
        {"city": "Shillong", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "temp_c": 20, "feels_like": 20, "humidity": 85, "wind_kph": 10, "wind_dir": "E", "condition": "Moderate Rain", "icon": "🌧️", "aqi": 30, "uv_index": 4, "pressure_hpa": 1002, "visibility_km": 4},
        {"city": "Agartala", "state": "Tripura", "lat": 23.8315, "lon": 91.2868, "temp_c": 32, "feels_like": 38, "humidity": 78, "wind_kph": 8, "wind_dir": "S", "condition": "Hot & Rainy", "icon": "🌦️", "aqi": 48, "uv_index": 7, "pressure_hpa": 1003, "visibility_km": 5},
        {"city": "Panaji", "state": "Goa", "lat": 15.4909, "lon": 73.8278, "temp_c": 33, "feels_like": 38, "humidity": 70, "wind_kph": 12, "wind_dir": "SW", "condition": "Humid & Warm", "icon": "🌤️", "aqi": 52, "uv_index": 10, "pressure_hpa": 1007, "visibility_km": 8},
        {"city": "Gangtok", "state": "Sikkim", "lat": 27.3389, "lon": 88.6065, "temp_c": 16, "feels_like": 14, "humidity": 70, "wind_kph": 8, "wind_dir": "E", "condition": "Cool & Misty", "icon": "🌫️", "aqi": 25, "uv_index": 4, "pressure_hpa": 1012, "visibility_km": 5},
        {"city": "Itanagar", "state": "Arunachal Pradesh", "lat": 27.0844, "lon": 93.6053, "temp_c": 24, "feels_like": 26, "humidity": 80, "wind_kph": 6, "wind_dir": "SE", "condition": "Light Drizzle", "icon": "🌦️", "aqi": 32, "uv_index": 5, "pressure_hpa": 1004, "visibility_km": 5},
        {"city": "Kohima", "state": "Nagaland", "lat": 25.6751, "lon": 94.1086, "temp_c": 22, "feels_like": 23, "humidity": 72, "wind_kph": 8, "wind_dir": "SE", "condition": "Partly Cloudy", "icon": "⛅", "aqi": 28, "uv_index": 6, "pressure_hpa": 1006, "visibility_km": 8},
        {"city": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176, "temp_c": 25, "feels_like": 27, "humidity": 70, "wind_kph": 10, "wind_dir": "S", "condition": "Cloudy", "icon": "☁️", "aqi": 30, "uv_index": 5, "pressure_hpa": 1005, "visibility_km": 7},
        {"city": "Port Blair", "state": "Andaman & Nicobar", "lat": 11.6234, "lon": 92.7265, "temp_c": 31, "feels_like": 36, "humidity": 82, "wind_kph": 16, "wind_dir": "SW", "condition": "Tropical Showers", "icon": "🌧️", "aqi": 35, "uv_index": 9, "pressure_hpa": 1006, "visibility_km": 6},
        {"city": "Leh", "state": "Ladakh", "lat": 34.1526, "lon": 77.5771, "temp_c": 8, "feels_like": 3, "humidity": 20, "wind_kph": 18, "wind_dir": "N", "condition": "Cold & Clear", "icon": "❄️", "aqi": 15, "uv_index": 8, "pressure_hpa": 1020, "visibility_km": 25},
        {"city": "Daman", "state": "Dadra & Nagar Haveli", "lat": 20.3974, "lon": 72.8328, "temp_c": 34, "feels_like": 39, "humidity": 65, "wind_kph": 14, "wind_dir": "SW", "condition": "Warm & Humid", "icon": "🌤️", "aqi": 58, "uv_index": 10, "pressure_hpa": 1007, "visibility_km": 8},
        {"city": "Kavaratti", "state": "Lakshadweep", "lat": 10.5626, "lon": 72.6369, "temp_c": 30, "feels_like": 35, "humidity": 80, "wind_kph": 18, "wind_dir": "W", "condition": "Tropical Rain", "icon": "🌧️", "aqi": 25, "uv_index": 10, "pressure_hpa": 1008, "visibility_km": 7},
    ],
    "weekly_forecast": [
        {"date": "2026-04-15", "day": "Wed", "temp_max": 43, "temp_min": 28, "condition": "Heat Wave", "icon": "🔥", "rain_chance": 0, "wind_kph": 25},
        {"date": "2026-04-16", "day": "Thu", "temp_max": 44, "temp_min": 29, "condition": "Extreme Heat", "icon": "☀️", "rain_chance": 0, "wind_kph": 22},
        {"date": "2026-04-17", "day": "Fri", "temp_max": 42, "temp_min": 28, "condition": "Very Hot", "icon": "☀️", "rain_chance": 5, "wind_kph": 18},
        {"date": "2026-04-18", "day": "Sat", "temp_max": 39, "temp_min": 27, "condition": "Dust Storm Possible", "icon": "🌪️", "rain_chance": 15, "wind_kph": 45},
        {"date": "2026-04-19", "day": "Sun", "temp_max": 36, "temp_min": 25, "condition": "Partly Cloudy", "icon": "⛅", "rain_chance": 30, "wind_kph": 20},
        {"date": "2026-04-20", "day": "Mon", "temp_max": 34, "temp_min": 24, "condition": "Pre-Monsoon Showers", "icon": "🌦️", "rain_chance": 55, "wind_kph": 15},
        {"date": "2026-04-21", "day": "Tue", "temp_max": 33, "temp_min": 23, "condition": "Scattered Rain", "icon": "🌧️", "rain_chance": 65, "wind_kph": 12},
    ],
    "historical_trends": {
        "labels": ["Jan", "Feb", "Mar", "Apr (so far)", "May*", "Jun*", "Jul*", "Aug*", "Sep*", "Oct*", "Nov*", "Dec*"],
        "avg_temp": [14, 18, 26, 38, 42, 38, 33, 32, 33, 30, 22, 16],
        "avg_rainfall_mm": [18, 15, 12, 8, 22, 180, 320, 290, 210, 45, 8, 5],
        "avg_humidity": [55, 42, 30, 20, 25, 65, 82, 85, 78, 50, 40, 52],
        "note": "* May onwards: predicted based on IMD seasonal model & historical 30-year average"
    },
    "severe_weather_alerts": [
        {
            "type": "Heat Wave",
            "severity": "critical",
            "region": "Rajasthan, Gujarat, Vidarbha",
            "valid_from": "2026-04-14",
            "valid_until": "2026-04-18",
            "description": "IMD Red Alert — Max temps 46-48°C expected. Heat stroke risk extreme for outdoor workers, elderly, and children.",
            "advisory": [
                "Avoid sun exposure 11 AM – 4 PM",
                "Drink water every 20 minutes — minimum 4-6 litres/day",
                "Public cooling shelters open at 480 locations across 3 states",
                "NDRF teams pre-positioned in 12 districts",
            ],
        },
        {
            "type": "Thunderstorm & Squall",
            "severity": "high",
            "region": "West Bengal, Jharkhand, Odisha",
            "valid_from": "2026-04-15",
            "valid_until": "2026-04-16",
            "description": "Nor'wester thunderstorms with wind gusts up to 80 kmph. Hail possible in sub-Himalayan West Bengal.",
            "advisory": [
                "Secure loose outdoor objects — signboards, tin roofs",
                "Avoid sheltering under trees during lightning",
                "Fishermen advised not to venture into Bay of Bengal",
                "Power outages expected — charge essential devices",
            ],
        },
        {
            "type": "Heavy Rainfall",
            "severity": "high",
            "region": "Assam, Meghalaya, Arunachal Pradesh",
            "valid_from": "2026-04-15",
            "valid_until": "2026-04-19",
            "description": "IMD Orange Alert — 120-180mm rain expected over 4 days. Flash flood risk in Brahmaputra tributaries.",
            "advisory": [
                "Residents near riverbanks should relocate to higher ground",
                "SDRF on standby in 8 districts of Assam",
                "Avoid crossing flooded roads/bridges",
                "Emergency helpline: 1070 (NDRF) / 108 (Ambulance)",
            ],
        },
        {
            "type": "Dust Storm",
            "severity": "moderate",
            "region": "Rajasthan, Haryana, Western UP",
            "valid_from": "2026-04-17",
            "valid_until": "2026-04-18",
            "description": "Strong westerly winds 50-70 kmph carrying dust from Thar Desert. Visibility likely to drop below 500m.",
            "advisory": [
                "Close windows and doors — use wet cloth as filter",
                "Avoid driving during peak dust storm hours (afternoon)",
                "Wear N95 masks if outdoor travel is essential",
                "Airport operations may face delays — check airline updates",
            ],
        },
    ],
    "geography_zones": [
        {"zone": "North India Plains", "lat": 28.5, "lon": 77.5, "climate": "Semi-Arid / Hot", "current_status": "Heat Wave Active", "monsoon_onset": "Late June", "key_risk": "Heat stroke, dust storms, water scarcity"},
        {"zone": "Western Coast", "lat": 19.0, "lon": 73.0, "climate": "Tropical Coastal", "current_status": "Pre-Monsoon Humidity", "monsoon_onset": "Early June (Kerala: Jun 1 ±5 days)", "key_risk": "Cyclones, flooding, landslides"},
        {"zone": "Eastern Coast", "lat": 13.0, "lon": 80.5, "climate": "Tropical Wet-Dry", "current_status": "Hot & Humid", "monsoon_onset": "NE Monsoon (Oct-Dec)", "key_risk": "Cyclones (Bay of Bengal), storm surge"},
        {"zone": "Northeast", "lat": 26.0, "lon": 91.5, "climate": "Subtropical Humid", "current_status": "Heavy Rain Active", "monsoon_onset": "Early June", "key_risk": "Flash floods, landslides, river erosion"},
        {"zone": "Central India", "lat": 23.0, "lon": 80.0, "climate": "Tropical Wet-Dry", "current_status": "Extreme Heat", "monsoon_onset": "Mid June", "key_risk": "Heat waves, drought (Bundelkhand), unseasonal hail"},
        {"zone": "Western Desert", "lat": 26.5, "lon": 71.0, "climate": "Arid / Desert", "current_status": "Heat Wave — Red Alert", "monsoon_onset": "Early July", "key_risk": "Heat stroke, sandstorms, water crisis"},
        {"zone": "Himalayan Region", "lat": 32.0, "lon": 77.0, "climate": "Alpine / Cold", "current_status": "Snowmelt + Warming", "monsoon_onset": "Late June", "key_risk": "Glacial lake outbursts, landslides, avalanches"},
    ],
    "monsoon_prediction": {
        "overall_forecast": "Normal to Above-Normal (106% of LPA)",
        "lpa_mm": 868,
        "predicted_mm": 920,
        "confidence": "78%",
        "onset_kerala": "June 1 ± 5 days",
        "onset_delhi": "June 28 ± 7 days",
        "withdrawal_start": "September 17",
        "regional_forecast": [
            {"region": "Northwest India", "forecast": "Below Normal (92% LPA)", "risk": "Possible drought in Haryana, West Rajasthan"},
            {"region": "Central India", "forecast": "Above Normal (112% LPA)", "risk": "Flood risk in Vidarbha, Madhya Pradesh"},
            {"region": "South Peninsula", "forecast": "Normal (98% LPA)", "risk": "Moderate — watch for cyclonic activity Oct-Nov"},
            {"region": "Northeast India", "forecast": "Above Normal (115% LPA)", "risk": "Major flood risk — Brahmaputra basin"},
        ],
        "el_nino_status": "Neutral (transitioning to weak La Niña by Jul-Aug)",
        "iod_status": "Positive IOD developing — supports good monsoon for peninsular India",
    },
}


@app.get("/api/weather/dashboard")
async def weather_dashboard():
    """Get full weather forecasting dashboard data"""
    return _weather_data


@app.get("/api/weather/current")
async def weather_current():
    """Get current conditions for all cities"""
    return {"current_conditions": _weather_data["current_conditions"]}


@app.get("/api/weather/forecast")
async def weather_forecast():
    """Get 7-day forecast"""
    return {"weekly_forecast": _weather_data["weekly_forecast"]}


@app.get("/api/weather/historical")
async def weather_historical():
    """Get historical trends data"""
    return {"historical_trends": _weather_data["historical_trends"]}


@app.get("/api/weather/alerts")
async def weather_alerts():
    """Get severe weather alerts"""
    return {"severe_weather_alerts": _weather_data["severe_weather_alerts"]}


@app.get("/api/weather/monsoon")
async def weather_monsoon():
    """Get monsoon prediction data"""
    return {"monsoon_prediction": _weather_data["monsoon_prediction"]}


# ===================== WEATHER FORECASTING RECOMMENDATIONS =====================
_weather_reco_data = {
    "states": [
        {"state": "Andhra Pradesh", "capital": "Amaravati", "temp_range": "34–42°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "HIGH",
         "forecast_7d": "Heatwave in Rayalaseema. Coastal areas expect pre-monsoon showers by week end.",
         "recommendations": ["Avoid outdoor work 11 AM – 4 PM", "Fishermen should not venture beyond 40 km from coast", "Prepare irrigation reserves for Kharif sowing"],
         "sectors": {"agriculture": "Delay paddy nursery by 5 days — soil moisture deficit", "health": "Heat stroke advisory — 200+ cases in Anantapur district", "infrastructure": "Power demand at 98% capacity — load shedding possible", "transport": "Vizag port operations affected by SW swell"}},
        {"state": "Arunachal Pradesh", "capital": "Itanagar", "temp_range": "18–26°C", "condition": "Moderate Rain", "icon": "🌧️", "risk_level": "MODERATE",
         "forecast_7d": "Continuous moderate rainfall expected. Landslide risk in Tawang and West Kameng districts.",
         "recommendations": ["Landslide prone zones — avoid travel on NH-13", "Pre-position disaster relief in Tawang", "Monitor river water levels hourly"],
         "sectors": {"agriculture": "Orange orchards — apply fungicide for root rot prevention", "health": "Malaria prevention spraying recommended in Lower Subansiri", "infrastructure": "Road connectivity may be disrupted to Tawang for 2–3 days", "transport": "Helicopter services operational with delays"}},
        {"state": "Assam", "capital": "Guwahati", "temp_range": "26–32°C", "condition": "Heavy Rain", "icon": "🌧️", "risk_level": "CRITICAL",
         "forecast_7d": "Red alert for Brahmaputra basin. Water level 1.2m above danger mark at Dhubri. Flood situation worsening.",
         "recommendations": ["Evacuate low-lying areas along Brahmaputra", "NDRF teams deployed — 12 teams in Dhubri, Barpeta", "Activate all flood shelters in Barpeta district"],
         "sectors": {"agriculture": "Complete crop loss expected in 3 districts — insurance claims to be fast-tracked", "health": "Water-borne disease risk HIGH — deploy mobile health units", "infrastructure": "NH-27 submerged at 4 points — use alternate routes", "transport": "Guwahati airport operating with restrictions — flight delays expected"}},
        {"state": "Bihar", "capital": "Patna", "temp_range": "35–42°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "HIGH",
         "forecast_7d": "Severe heat in northern plains. Thunderstorm activity expected from Day 4 with gusty winds.",
         "recommendations": ["Heat advisory for outdoor laborers — ORS distribution recommended", "Lightning alert from Thursday — farmers should stay indoors", "Water table dropping — restrict tube well usage"],
         "sectors": {"agriculture": "Mango crop at risk from heat stress — spray kaolin", "health": "12 heat-related deaths this week — activate heat action plan", "infrastructure": "Power grid under stress — 5-hour load shedding in rural areas", "transport": "Ganga water level low — ferry services reduced at Digha Ghat"}},
        {"state": "Chhattisgarh", "capital": "Raipur", "temp_range": "37–44°C", "condition": "Extreme Heat", "icon": "☀️", "risk_level": "HIGH",
         "forecast_7d": "Persistent heatwave across Chhattisgarh plains. Forest fire alerts active in Achanakmar and Barnawapara.",
         "recommendations": ["Forest fire watch — deploy fire lines in Achanakmar", "Water tanker deployment for 15 tribal villages", "Schools closed until temperature drops below 42°C"],
         "sectors": {"agriculture": "Irrigation reservoirs at 22% — restrict non-essential usage", "health": "Sunstroke cases rising — set up heat relief camps", "infrastructure": "Forest fire risk to power transmission lines in Korba", "transport": "All clear — no weather disruption"}},
        {"state": "Goa", "capital": "Panaji", "temp_range": "30–35°C", "condition": "Humid & Warm", "icon": "🌤️", "risk_level": "LOW",
         "forecast_7d": "Pre-monsoon conditions building. Expect isolated thundershowers from Day 5. Sea becoming rough.",
         "recommendations": ["Beach safety patrols to be increased from Friday", "Fishermen advisory — rough seas expected by weekend", "Tourism operators prepare monsoon contingency plans"],
         "sectors": {"agriculture": "Cashew harvest — dry conditions favorable this week", "health": "Dengue surveillance needed — stagnant water checks", "infrastructure": "All systems normal — monsoon infrastructure audit recommended", "transport": "Mormugao port operational — swell building from Friday"}},
        {"state": "Gujarat", "capital": "Ahmedabad", "temp_range": "40–47°C", "condition": "Heat Wave", "icon": "🔥", "risk_level": "CRITICAL",
         "forecast_7d": "Severe heatwave — Ahmedabad, Rajkot, Surat to cross 46°C. Kutch facing extreme drought conditions.",
         "recommendations": ["Red alert for Ahmedabad — all construction work suspended 12–5 PM", "Deploy water trains to Kutch region", "Narmada canal water allocation to be increased"],
         "sectors": {"agriculture": "Groundnut sowing postponed — await monsoon", "health": "Heat action plan activated — 500 cooling centres open", "infrastructure": "Water crisis in Kutch — desalination plants at full capacity", "transport": "Kandla port normal — vehicular traffic restricted on NH-8A during peak heat"}},
        {"state": "Haryana", "capital": "Chandigarh", "temp_range": "38–45°C", "condition": "Hot & Dry", "icon": "☀️", "risk_level": "HIGH",
         "forecast_7d": "Intense heat continuing. Dust storm possible from western Rajasthan on Day 3. Crop residue burning advisories.",
         "recommendations": ["Dust storm alert for southern Haryana — secure loose structures", "Wheat stubble management advisory — avoid burning", "Water conservation measures in Gurugram mandatory"],
         "sectors": {"agriculture": "Wheat harvest complete — prepare fields for monsoon paddy without burning", "health": "AQI deteriorating — masks advisory for Gurugram, Faridabad", "infrastructure": "Power demand peak expected — grid synchronization stable", "transport": "NH-48 visibility may drop during dust storm — use fog lights"}},
        {"state": "Himachal Pradesh", "capital": "Shimla", "temp_range": "18–28°C", "condition": "Pleasant", "icon": "⛅", "risk_level": "LOW",
         "forecast_7d": "Pleasant weather in hills. Isolated thunderstorms in lower hills. Tourist season at peak.",
         "recommendations": ["Tourist safety advisory for Rohtang Pass — afternoon clouds", "Apple orchards — good growth conditions continue", "Monitor Sutlej river levels after upstream snowmelt"],
         "sectors": {"agriculture": "Apple orchards thriving — continue pest monitoring", "health": "UV index high at altitude — sunscreen advisory for tourists", "infrastructure": "All roads operational — Manali-Leh highway open", "transport": "Shimla airport operational — afternoon turbulence possible"}},
        {"state": "Jharkhand", "capital": "Ranchi", "temp_range": "32–39°C", "condition": "Thunderstorm Risk", "icon": "⛈️", "risk_level": "MODERATE",
         "forecast_7d": "Hot days with afternoon thunderstorm development. Lightning risk across Chota Nagpur plateau.",
         "recommendations": ["Lightning safety awareness in mining areas", "Farmers — harvest standing paddy before Thursday storms", "Municipal drains to be cleared pre-monsoon"],
         "sectors": {"agriculture": "Lac cultivation — favorable conditions", "health": "Vector control spraying needed in Jamshedpur", "infrastructure": "Mining operations — lightning detection systems mandatory", "transport": "Ranchi airport — expect afternoon delays due to convective weather"}},
        {"state": "Karnataka", "capital": "Bengaluru", "temp_range": "24–34°C", "condition": "Pre-Monsoon Showers", "icon": "🌦️", "risk_level": "MODERATE",
         "forecast_7d": "Pre-monsoon activity intensifying. Bengaluru may see evening thunderstorms. Coastal Karnataka — heavy rain alert.",
         "recommendations": ["Bengaluru — urban flood preparedness for low-lying areas", "Coastal Karnataka fishermen to return to shore", "Coffee plantations — ideal conditions for blossom showers"],
         "sectors": {"agriculture": "Coffee blossom showers — excellent for Arabica yield", "health": "Dengue prevention drive in Bengaluru urban", "infrastructure": "Bengaluru stormwater drains at 60% capacity — clear debris", "transport": "Mangalore airport — crosswind advisory from Thursday"}},
        {"state": "Kerala", "capital": "Thiruvananthapuram", "temp_range": "28–35°C", "condition": "Pre-Monsoon Showers", "icon": "🌦️", "risk_level": "MODERATE",
         "forecast_7d": "Monsoon onset likely by June 1. Pre-monsoon showers intensifying. Idukki dam at 42% capacity.",
         "recommendations": ["Fishermen — return to shore before monsoon onset", "Idukki dam — monitor inflow closely", "Rubber tapping to be paused during heavy rain spells"],
         "sectors": {"agriculture": "Paddy nursery preparation — optimal timing now", "health": "Leptospirosis advisory — avoid wading in flood water", "infrastructure": "Kerala canal system inspection before monsoon", "transport": "Kochi port — monsoon preparedness drill completed"}},
        {"state": "Madhya Pradesh", "capital": "Bhopal", "temp_range": "38–46°C", "condition": "Extreme Heat", "icon": "☀️", "risk_level": "HIGH",
         "forecast_7d": "Prolonged heatwave in western MP. Chambal region crossing 46°C. Forest fires in Panna Tiger Reserve.",
         "recommendations": ["Forest fire response teams on standby in Panna", "Water rationing in Bundelkhand — 4-hour supply", "MGNREGA work timings changed to early morning"],
         "sectors": {"agriculture": "Soybean regions — pre-monsoon field preparation optimal", "health": "Heat mortality — awareness campaigns in rural areas", "infrastructure": "Dam levels at 18% — water allocation prioritized for drinking", "transport": "NH-46 clear — watch for heat-related tire bursts"}},
        {"state": "Maharashtra", "capital": "Mumbai", "temp_range": "30–38°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "MODERATE",
         "forecast_7d": "Mumbai — humidity rising, pre-monsoon clouds building. Vidarbha — severe heat persists. Konkan coast — sea state deteriorating.",
         "recommendations": ["Mumbai — clean storm drains before monsoon arrival", "Vidarbha farmers — drought relief scheme applications open", "Konkan — fishermen advisory for rough seas"],
         "sectors": {"agriculture": "Sugarcane — adequate irrigation recommended in Marathwada", "health": "Dengue cases rising in Mumbai — fogging recommended", "infrastructure": "Mumbai local — monsoon timetable preparation in progress", "transport": "Mumbai CSMT — waterlogging preparedness at critical stations"}},
        {"state": "Manipur", "capital": "Imphal", "temp_range": "18–28°C", "condition": "Light Rain", "icon": "🌧️", "risk_level": "LOW",
         "forecast_7d": "Light to moderate rainfall continues. Valley areas pleasant. Hill districts — foggy mornings.",
         "recommendations": ["Hill road travel — reduce speed in fog", "Rice transplanting — optimal timing next week", "Monitor Barak river tributaries"],
         "sectors": {"agriculture": "Wet rice cultivation — field preparation ongoing", "health": "Malaria prevention in hill districts", "infrastructure": "Imphal-Moreh highway — minor landslips possible", "transport": "Imphal airport operational — visibility sometimes drops to 2 km"}},
        {"state": "Meghalaya", "capital": "Shillong", "temp_range": "15–23°C", "condition": "Heavy Rain", "icon": "🌧️", "risk_level": "HIGH",
         "forecast_7d": "Cherrapunji/Mawsynram receiving 200+ mm daily. Flash flood risk in south Garo hills. Shillong pleasant.",
         "recommendations": ["Flash flood alert for Garo Hills — evacuate riverside settlements", "Tourist advisory — avoid waterfalls and rivers", "Pre-position relief material in East Khasi Hills"],
         "sectors": {"agriculture": "Strawberry harvest — protect from excess rain", "health": "Waterborne disease alert — boil water advisory", "infrastructure": "Multiple road breaches on NH-6 — repairs underway", "transport": "Shillong Umroi airport — flights operational with visibility delays"}},
        {"state": "Mizoram", "capital": "Aizawl", "temp_range": "20–28°C", "condition": "Moderate Rain", "icon": "🌧️", "risk_level": "MODERATE",
         "forecast_7d": "Steady rainfall with embedded heavy spells. Landslide-prone areas on alert.",
         "recommendations": ["Landslide watch in Lunglei and Champhai", "Bamboo flowering areas — rat flood preparedness", "Community weather stations — increase reporting frequency"],
         "sectors": {"agriculture": "Jhum cultivation areas — soil erosion monitoring", "health": "Storm water management in Aizawl city", "infrastructure": "Kaladan project road — weather delays expected", "transport": "Lengpui airport — crosswind alerts active"}},
        {"state": "Nagaland", "capital": "Kohima", "temp_range": "18–26°C", "condition": "Cloudy with Rain", "icon": "☁️", "risk_level": "MODERATE",
         "forecast_7d": "Overcast skies with intermittent rain. Mon district — heavy rain expected Day 3–5.",
         "recommendations": ["Mon district — landslide preparedness", "Terrace farming areas — drainage channel clearing", "Community alert systems — test before heavy rain"],
         "sectors": {"agriculture": "Terrace rice fields — transplanting window next week", "health": "Japanese encephalitis vaccination drive in Dimapur", "infrastructure": "NH-29 — monitor for landslides after heavy rain", "transport": "Dimapur railway — minor delays due to track waterlogging"}},
        {"state": "Odisha", "capital": "Bhubaneswar", "temp_range": "34–42°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "HIGH",
         "forecast_7d": "Western Odisha heatwave continues. Coastal areas — depression forming in Bay of Bengal being monitored.",
         "recommendations": ["Cyclone preparedness — monitor Bay of Bengal depression", "Sundargarh-Bolangir heat red alert", "Fishing ban advisory if depression intensifies"],
         "sectors": {"agriculture": "Paddy — prepare for Kharif sowing post-monsoon onset", "health": "Heat treatment camps in mining districts", "infrastructure": "Paradip port — cyclone preparedness protocol initiated", "transport": "Bhubaneswar airport normal — watch cyclone development"}},
        {"state": "Punjab", "capital": "Chandigarh", "temp_range": "36–44°C", "condition": "Hot & Dusty", "icon": "☀️", "risk_level": "HIGH",
         "forecast_7d": "Severe heat with dust haze. Wheat stubble burning season — air quality concerns. Thundershower possible Day 6–7.",
         "recommendations": ["Stubble burning ban enforcement — satellite monitoring active", "Conserve canal water for paddy transplantation", "Heat advisory for outdoor workers — ORS distribution"],
         "sectors": {"agriculture": "Wheat harvest complete — DO NOT burn stubble — ₹2500/acre incentive for mulching", "health": "Respiratory issues rising from stubble smoke — AQI 280+", "infrastructure": "Power demand surge — canal water allocation dispute", "transport": "Amritsar-Delhi corridor — visibility 3 km due to haze"}},
        {"state": "Rajasthan", "capital": "Jaipur", "temp_range": "40–49°C", "condition": "Severe Heat Wave", "icon": "🔥", "risk_level": "CRITICAL",
         "forecast_7d": "Barmer, Churu, Ganganagar — 49°C expected. Thar Desert sandstorm forming. Night temperatures above 32°C.",
         "recommendations": ["Stay indoors 10 AM – 6 PM in western Rajasthan", "Military — heat acclimatization for desert exercises", "Water supply emergency — deploy tankers to 50 villages in Barmer"],
         "sectors": {"agriculture": "No cultivation possible — focus on livestock survival", "health": "60+ heat deaths this month — emergency medical camps", "infrastructure": "Solar power generation exceeding 12 GW — grid export active", "transport": "NH-15 — sandstorm visibility near zero — highway closed temporarily"}},
        {"state": "Sikkim", "capital": "Gangtok", "temp_range": "12–20°C", "condition": "Cool & Misty", "icon": "🌫️", "risk_level": "LOW",
         "forecast_7d": "Pleasant weather with afternoon mist. Glacial lake monitoring — Teesta basin stable.",
         "recommendations": ["Tourism at peak — ensure tourist safety at monasteries and viewpoints", "Cardamom plantations — ideal growing conditions", "Monitor GLOF indicators in North Sikkim"],
         "sectors": {"agriculture": "Cardamom — excellent conditions, continue organic practices", "health": "Altitude sickness advisory for high-pass travelers", "infrastructure": "Teesta Stage-V dam — normal operations", "transport": "NH-10 open — Nathula Pass open for tourists weekdays"}},
        {"state": "Tamil Nadu", "capital": "Chennai", "temp_range": "33–40°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "HIGH",
         "forecast_7d": "Chennai — heat index above 48°C with humidity. Delta districts — water stress. Nilgiris — pleasant.",
         "recommendations": ["Chennai — schools timings advanced to 7 AM", "Cauvery delta — restrict borewell pumping", "Nilgiris — tourist season optimal"],
         "sectors": {"agriculture": "Cauvery delta — water shortage for Kuruvai paddy — delay sowing", "health": "Heat index dangerous — Chennai cooling shelters activated", "infrastructure": "Metro water supply — alternate day schedule until June", "transport": "Chennai airport operational — haze reducing visibility to 4 km"}},
        {"state": "Telangana", "capital": "Hyderabad", "temp_range": "36–43°C", "condition": "Hot & Dry", "icon": "☀️", "risk_level": "HIGH",
         "forecast_7d": "Persistent heat across Telangana. Thunderstorm development expected Day 5 onwards with dust squalls.",
         "recommendations": ["Mission Bhagiratha water supply — increase tanker deployment", "Construction workers — mandatory rest 12–3 PM", "Cotton sowing — await monsoon establishment"],
         "sectors": {"agriculture": "Cotton and chili — pre-monsoon field preparation", "health": "Kidney disease surge from heat — hydration campaigns", "infrastructure": "Kaleswaram project — reservoir at 31% capacity", "transport": "Rajiv Gandhi International Airport — normal operations"}},
        {"state": "Tripura", "capital": "Agartala", "temp_range": "28–35°C", "condition": "Hot & Rainy", "icon": "🌦️", "risk_level": "MODERATE",
         "forecast_7d": "Intermittent heavy showers. Flooding in low-lying areas of Agartala. Gomati river rising.",
         "recommendations": ["Gomati river bank settlements — flood alert", "Pre-monsoon drainage clearing in Agartala city", "Rubber plantations — tapping pause advisory"],
         "sectors": {"agriculture": "Rubber tapping paused — protect latex from rain contamination", "health": "Dengue vector surveillance — clear stagnant water", "infrastructure": "Agartala-Sabroom railway — waterlogging checks", "transport": "Agartala MBB airport — intermittent closures during heavy downpours"}},
        {"state": "Uttar Pradesh", "capital": "Lucknow", "temp_range": "38–46°C", "condition": "Extreme Heat", "icon": "☀️", "risk_level": "CRITICAL",
         "forecast_7d": "Severe heatwave across UP plains. Bundelkhand drought conditions. Thunderstorm activity from Day 5 in eastern UP.",
         "recommendations": ["Red alert for 15 districts — outdoor work banned 12–4 PM", "Bundelkhand drought — water train deployment approved", "Schools and Anganwadis closed until further notice in worst-hit districts"],
         "sectors": {"agriculture": "Sugarcane — irrigation critical, canal water allocation increased", "health": "300+ heat casualties this month — activate all PHCs for heat emergencies", "infrastructure": "Power deficit — 4-hour load shedding in tier-2 cities", "transport": "Lucknow metro — normal. Highways — watch for tire bursts in extreme heat"}},
        {"state": "Uttarakhand", "capital": "Dehradun", "temp_range": "28–38°C", "condition": "Warm & Clear", "icon": "☀️", "risk_level": "MODERATE",
         "forecast_7d": "Plains hot, hills pleasant. Forest fire risk HIGH in Kumaon region. Char Dham yatra weather favorable.",
         "recommendations": ["Forest fire alert — Kumaon and Garhwal ranges", "Char Dham yatra — safe passage conditions for next 5 days", "Rishikesh — river rafting conditions optimal"],
         "sectors": {"agriculture": "Basmati nursery — begin preparation in Terai region", "health": "Forest fire smoke — AQI advisory for Nainital, Almora", "infrastructure": "Badrinath highway — clear for heavy vehicles", "transport": "Jolly Grant airport — normal operations, turbulence after 2 PM"}},
        {"state": "West Bengal", "capital": "Kolkata", "temp_range": "32–40°C", "condition": "Thunderstorm", "icon": "⛈️", "risk_level": "HIGH",
         "forecast_7d": "Nor'westers active — severe thunderstorms with hail possible. Kolkata to experience gusty winds 60–80 kmph.",
         "recommendations": ["Nor'wester alert — secure outdoor hoardings and scaffolding", "Fishermen — do not venture into Bay of Bengal", "Crop protection — cover nurseries and protect mango orchards"],
         "sectors": {"agriculture": "Mango-litchi orchards — hail protection nets recommended", "health": "Lightning safety — 15 deaths this week from thunderstorms", "infrastructure": "Kolkata trees at high risk of uprooting — pruning drive needed", "transport": "Kolkata airport — afternoon closures possible due to thunderstorms"}},
        {"state": "Delhi NCT", "capital": "New Delhi", "temp_range": "40–47°C", "condition": "Severe Heat", "icon": "🔥", "risk_level": "CRITICAL",
         "forecast_7d": "Extreme heatwave — all-time records possible. Yamuna at lowest level in decade. AQI 200+ from dust storms.",
         "recommendations": ["Outdoor work banned 11 AM – 5 PM", "DJB water supply increased — tanker helpline active", "Homeless shelters — cooling stations in every ward"],
         "sectors": {"agriculture": "Urban farming — shade nets mandatory", "health": "Emergency wards on high alert — heat stroke surge expected", "infrastructure": "Power demand at 8.3 GW — new record, grid stable", "transport": "IGI Airport normal — visibility advisory during dust events"}},
        {"state": "Jammu & Kashmir", "capital": "Srinagar", "temp_range": "14–28°C", "condition": "Pleasant", "icon": "🌤️", "risk_level": "LOW",
         "forecast_7d": "Valley — ideal weather for tourism. Jammu division — hot. Snowmelt feeding rivers adequately.",
         "recommendations": ["Tourist season peak — ensure crowd management at Dal Lake", "Amarnath Yatra preparation — route assessment ongoing", "Apple farmers — thinning and pest spray schedule on track"],
         "sectors": {"agriculture": "Apple — thinning phase, saffron fields — normal maintenance", "health": "Tourist influx — medical camps at major destinations", "infrastructure": "Jhelum river — controlled flow, no flood risk currently", "transport": "Srinagar airport — clear operations, Jammu highway open"}},
        {"state": "Ladakh", "capital": "Leh", "temp_range": "2–18°C", "condition": "Cold & Clear", "icon": "❄️", "risk_level": "LOW",
         "forecast_7d": "Cold desert — clear skies. Night frost in Changthang. Tourist season starting.",
         "recommendations": ["Tourist advisory — acclimatization mandatory before high passes", "Changthang pastoralists — cold protection for livestock", "Solar power — excellent generation conditions"],
         "sectors": {"agriculture": "Apricot cultivation — flowering phase, no frost damage expected", "health": "Altitude sickness — military medical teams deployed at Khardung La", "infrastructure": "Zoji La tunnel — operational, all highways open", "transport": "Leh airport — operational, weight restrictions due to altitude"}},
        {"state": "Puducherry", "capital": "Puducherry", "temp_range": "32–38°C", "condition": "Hot & Humid", "icon": "🌤️", "risk_level": "MODERATE",
         "forecast_7d": "Coastal heat with high humidity. Beach erosion monitoring active. Pre-monsoon clouds building.",
         "recommendations": ["Sea erosion — vulnerable coastal areas identified", "Fishing community — rough sea advisory from Day 5", "Water conservation — reservoir levels at 40%"],
         "sectors": {"agriculture": "Salt pans — harvest conditions good", "health": "Heat + humidity — heat index above 45°C", "infrastructure": "Beach erosion countermeasures deployed", "transport": "Puducherry port — minor disruptions expected by weekend"}},
        {"state": "Chandigarh", "capital": "Chandigarh", "temp_range": "36–43°C", "condition": "Hot", "icon": "☀️", "risk_level": "MODERATE",
         "forecast_7d": "Urban heat island effect — nighttime temperatures not dropping below 30°C. Sukhna Lake receding.",
         "recommendations": ["Water conservation strict — lawn watering banned", "Sukhna Lake — water level monitoring for ecological balance", "Public parks — evening hours extended for heat relief"],
         "sectors": {"agriculture": "N/A — urban territory", "health": "Heat fatigue in outdoor workers — cooling stations at sector markets", "infrastructure": "Power supply stable — solar rooftop surge helping grid", "transport": "All transport normal — AC bus frequency increased"}},
    ],
    "national_summary": {
        "overall_risk": "HIGH",
        "critical_states": 5,
        "high_risk_states": 11,
        "active_alerts": 28,
        "monsoon_countdown_days": 18,
        "headline": "Severe heatwave grips North & Central India. Flood situation worsening in Assam. Bay of Bengal depression forming — cyclone watch initiated.",
        "updated_at": datetime.now().isoformat() if 'datetime' in dir() else "2026-04-15T10:00:00",
    },
    "sector_matrix": [
        {"sector": "Agriculture", "icon": "🌾", "national_risk": "HIGH", "summary": "Kharif sowing delayed across 12 states due to heat. Crop insurance claims rising in drought-affected Bundelkhand and Vidarbha. Coffee blossom showers in Karnataka beneficial.", "affected_states": 18, "advisory": "Delay sowing until monsoon onset confirmed. Use mulching to conserve soil moisture."},
        {"sector": "Health", "icon": "🏥", "national_risk": "CRITICAL", "summary": "Heat-related mortality at 450+ across India this month. Dengue vector surveillance needed in 8 states. Water-borne disease risk escalating in flood-affected NE states.", "affected_states": 22, "advisory": "Activate heat action plans. Deploy ORS and cooling stations in all vulnerable districts."},
        {"sector": "Infrastructure", "icon": "🏗️", "national_risk": "HIGH", "summary": "Power grid at 92% capacity nationally. Water reservoirs at 24% average. Road disruptions in 6 NE states due to landslides. Dam safety monitoring intensified.", "affected_states": 15, "advisory": "Load management critical. Prioritize drinking water over irrigation."},
        {"sector": "Transport", "icon": "🚂", "national_risk": "MODERATE", "summary": "Airport disruptions at 4 locations due to weather. Highway closures in Rajasthan (sandstorm), Meghalaya (landslides). Port operations affected on east coast.", "affected_states": 8, "advisory": "Real-time weather integration for transport advisories."},
        {"sector": "Disaster Preparedness", "icon": "🛡️", "national_risk": "HIGH", "summary": "NDRF deployed in 8 states. Cyclone watch in Bay of Bengal. Flood rescue operations active in Assam. Forest fire alerts in 3 states.", "affected_states": 12, "advisory": "Pre-position rescue teams. Ensure early warning systems are operational in all districts."},
    ],
}

@app.get("/api/weather/recommendations")
async def weather_recommendations():
    """Get state-wise weather forecasting recommendations"""
    return _weather_reco_data


# ===================== INCIDENT REPORTING =====================
import uuid
from datetime import datetime

# ===================== LIVE EVENTS INTELLIGENCE =====================
_live_events = [
    {
        "id": "EVT-2026-001",
        "type": "protest",
        "title": "Farmers Protest — Delhi-Haryana Border",
        "summary": "Large-scale farmer protest demanding guaranteed MSP legislation. ~25,000 farmers from Punjab and Haryana assembled at Singhu and Tikri border points. NH-44 highway blockade active.",
        "status": "active",
        "escalation": "escalating",
        "severity": "HIGH",
        "region": "Delhi - Haryana Border",
        "state": "Haryana",
        "affected_areas": ["Singhu Border", "Tikri Border", "NH-44 Corridor", "Kundli Industrial Area"],
        "started_at": "2026-03-28T06:00:00",
        "last_updated": "2026-04-15T08:30:00",
        "source": "Delhi Police Intelligence / IB",
        "key_facts": [
            "25,000+ farmers assembled from Punjab & Haryana",
            "NH-44 blocked — traffic diverted via Rajasthan corridor",
            "5,000 police personnel deployed with water cannons",
            "48-hour Punjab bandh called by protest leaders",
            "Talks between farm union leaders and govt scheduled April 17",
            "Essential supply routes being rerouted"
        ],
        "impact": {
            "people_affected": "~2 lakh (direct), 50 lakh (supply chain disruption)",
            "economic_loss": "Estimated ₹150 crore/day",
            "sectors_impacted": ["Transport", "Agriculture Supply Chain", "Trade"]
        },
        "timeline": [
            {"date": "2026-03-28", "event": "Farmers begin march from Punjab, reach Shambhu border"},
            {"date": "2026-04-01", "event": "Crowd swells to 15,000; first NH-44 blockade"},
            {"date": "2026-04-07", "event": "Punjab bandh observed; police use tear gas at Shambhu"},
            {"date": "2026-04-12", "event": "Crowd grows to 25,000; Tikri border also blocked"},
            {"date": "2026-04-15", "event": "Government agrees to talks on April 17; situation tense but stable"}
        ],
        "govt_response": "MHA monitoring. Haryana Police deployed. Central negotiation team formed. Essential supplies corridor established.",
        "tags": ["farmers", "MSP", "protest", "bandh", "Punjab", "Haryana", "NH-44"]
    },
    {
        "id": "EVT-2026-002",
        "type": "civil_unrest",
        "title": "Manipur Ethnic Violence — Churachandpur & Bishnupur",
        "summary": "Fresh ethnic clashes in Manipur hill districts. 15 houses burned, 3 casualties. Army deployed along valley-hill buffer zone. 2,500 displaced to relief camps.",
        "status": "active",
        "escalation": "escalating",
        "severity": "CRITICAL",
        "region": "Manipur",
        "state": "Manipur",
        "affected_areas": ["Churachandpur", "Bishnupur", "Imphal East", "NH-2 Imphal-Moreh Road"],
        "started_at": "2026-04-08T14:00:00",
        "last_updated": "2026-04-15T06:00:00",
        "source": "MHA Situation Report",
        "key_facts": [
            "15 houses burned in Churachandpur & Bishnupur",
            "3 casualties confirmed, 18 injured",
            "2,500 people displaced to relief camps in Imphal East",
            "Army column deployed along valley-hill buffer zone",
            "Internet blackout in 5 districts",
            "NH-2 Imphal-Moreh partially blocked",
            "Central government advisors dispatched"
        ],
        "impact": {
            "people_affected": "~50,000 (displacement + curfew zones)",
            "economic_loss": "Trade with Myanmar halted via Moreh",
            "sectors_impacted": ["Security", "Trade", "Humanitarian"]
        },
        "timeline": [
            {"date": "2026-04-08", "event": "Clashes erupt in Churachandpur after market dispute"},
            {"date": "2026-04-10", "event": "Violence spreads to Bishnupur; army columns deployed"},
            {"date": "2026-04-12", "event": "Internet suspended in 5 districts; curfew imposed"},
            {"date": "2026-04-14", "event": "Relief camps set up; 2,500 displaced"},
            {"date": "2026-04-15", "event": "Central advisors arrive; peace talks proposed"}
        ],
        "govt_response": "Army and Assam Rifles deployed. Section 144 in 3 districts. MHA central team on ground. Internet blackout to prevent rumor spread.",
        "tags": ["ethnic violence", "Manipur", "curfew", "army", "displacement", "civil unrest"]
    },
    {
        "id": "EVT-2026-003",
        "type": "pandemic",
        "title": "Nipah Virus Alert — Kerala Kozhikode",
        "summary": "Level-2 pandemic alert in Kozhikode after fruit bat surveillance shows 8% Nipah antibody prevalence. One suspected case (negative). 500-bed isolation facility activated. Contact tracing active.",
        "status": "active",
        "escalation": "monitoring",
        "severity": "HIGH",
        "region": "Kerala - Kozhikode",
        "state": "Kerala",
        "affected_areas": ["Kozhikode City", "Malappuram Border", "Wayanad Buffer Zone"],
        "started_at": "2026-03-15T10:00:00",
        "last_updated": "2026-04-14T18:00:00",
        "source": "Kerala Health Department / ICMR",
        "key_facts": [
            "Fruit bat surveillance: 8% Nipah antibody prevalence in Kozhikode",
            "One suspected case tested negative on April 5",
            "500-bed isolation facility activated at 3 hospitals",
            "PPE stocks available for 30 days",
            "Contact tracing protocol operational — 450 contacts monitored",
            "Travel advisory issued for Kozhikode district"
        ],
        "impact": {
            "people_affected": "~8 lakh (health alert zone)",
            "economic_loss": "Tourism down 40% in Kozhikode; trade fairs canceled",
            "sectors_impacted": ["Health", "Tourism", "Economy"]
        },
        "timeline": [
            {"date": "2026-03-15", "event": "ICMR bat surveillance report flags 8% antibody prevalence"},
            {"date": "2026-03-20", "event": "Level-2 health alert declared by Kerala Health Dept"},
            {"date": "2026-04-05", "event": "Suspected case admitted; tested negative for Nipah"},
            {"date": "2026-04-10", "event": "Contact tracing expanded to 450 persons"},
            {"date": "2026-04-14", "event": "No new cases; alert maintained as precaution"}
        ],
        "govt_response": "ICMR lead agency. Isolation wards ready. State health minister monitoring daily. WHO advisory team consulted.",
        "tags": ["Nipah", "pandemic", "virus", "Kerala", "Kozhikode", "health alert", "ICMR"]
    },
    {
        "id": "EVT-2026-004",
        "type": "strike",
        "title": "Nationwide Transport Strike — Fuel Price Protest",
        "summary": "All India Motor Transport Congress indefinite strike from April 18 over fuel prices and toll charges. 95 lakh trucks and 50 lakh buses expected to halt. Essential supply chain at severe risk.",
        "status": "active",
        "escalation": "escalating",
        "severity": "CRITICAL",
        "region": "Pan-India",
        "state": "All States",
        "affected_areas": ["All National Highways", "Major Cities", "Industrial Corridors", "Port Areas"],
        "started_at": "2026-04-12T00:00:00",
        "last_updated": "2026-04-15T10:00:00",
        "source": "Ministry of Road Transport / IB Assessment",
        "key_facts": [
            "Strike announced from April 18 — indefinite",
            "95 lakh trucks + 50 lakh buses will halt",
            "Petroleum, food grains, vegetables supply at risk",
            "Govt invoked Essential Services Maintenance Act in 6 states",
            "Emergency fuel reserves activated for 7 days",
            "Railways asked to increase freight capacity",
            "140 potential flashpoints identified by state police"
        ],
        "impact": {
            "people_affected": "~140 crore (nationwide supply disruption)",
            "economic_loss": "Estimated ₹3,500 crore/day to economy",
            "sectors_impacted": ["Transport", "Fuel", "Food Supply", "Manufacturing", "Trade"]
        },
        "timeline": [
            {"date": "2026-04-05", "event": "Transport Congress announces strike call over fuel prices"},
            {"date": "2026-04-10", "event": "Government negotiations fail; strike confirmed April 18"},
            {"date": "2026-04-12", "event": "Essential Services Act invoked in 6 states"},
            {"date": "2026-04-14", "event": "Fuel reserves activated; Railways prep for extra freight"},
            {"date": "2026-04-15", "event": "Last-minute talks scheduled; unions firm on demands"}
        ],
        "govt_response": "Essential Services Act invoked. Emergency fuel reserves. Railways on standby. Final negotiation round scheduled April 16.",
        "tags": ["transport strike", "fuel", "trucks", "supply chain", "bandh", "nationwide"]
    },
    {
        "id": "EVT-2026-005",
        "type": "war",
        "title": "LoC Tensions — Poonch & Rajouri Sector",
        "summary": "Pakistan ceasefire violations escalating in Poonch-Rajouri. 15 incidents in March 2026. Indian Army neutralized 2 launch pads. 8,000 civilians evacuated from 5km buffer zone.",
        "status": "active",
        "escalation": "escalating",
        "severity": "CRITICAL",
        "region": "Jammu & Kashmir - Poonch / Rajouri",
        "state": "Jammu & Kashmir",
        "affected_areas": ["Poonch Sector", "Rajouri Sector", "Mendhar Tehsil", "LoC Buffer Zone"],
        "started_at": "2026-03-01T00:00:00",
        "last_updated": "2026-04-15T05:00:00",
        "source": "Indian Army Northern Command / BSF",
        "key_facts": [
            "15 ceasefire violations in March 2026",
            "Indian Army retaliatory fire neutralized 2 launch pads",
            "8,000 civilians evacuated from 5km buffer zone in Mendhar",
            "BSF reinforced forward posts with additional battalions",
            "Night surveillance drones deployed along LoC",
            "3 soldiers martyred, 7 injured in March",
            "Diplomatic protests lodged via DGMO hotline"
        ],
        "impact": {
            "people_affected": "~8,000 (evacuated), 1.5 lakh (alert zone)",
            "economic_loss": "Apple trade from Poonch disrupted",
            "sectors_impacted": ["Security", "Border Trade", "Civilian Safety"]
        },
        "timeline": [
            {"date": "2026-03-05", "event": "First ceasefire violation in Poonch sector after 6 months"},
            {"date": "2026-03-12", "event": "Multiple violations; 2 soldiers martyred in Rajouri"},
            {"date": "2026-03-20", "event": "Army neutralizes 2 launch pads across LoC"},
            {"date": "2026-03-28", "event": "Civilian evacuation ordered in Mendhar buffer zone"},
            {"date": "2026-04-10", "event": "BSF reinforcements arrive; drone surveillance begins"},
            {"date": "2026-04-15", "event": "Situation tense; DGMO talks proposed"}
        ],
        "govt_response": "Army on high alert. BSF reinforced. Civilian evacuation complete. Diplomatic channels active. DGMO hotline engaged.",
        "tags": ["LoC", "ceasefire", "Pakistan", "border", "war", "Poonch", "Rajouri", "army"]
    },
    {
        "id": "EVT-2026-006",
        "type": "disaster",
        "title": "Brahmaputra Flood Warning — Assam",
        "summary": "Brahmaputra river at Guwahati approaching danger mark (49.2m vs 49.68m danger). Rising 0.15m/day. NDRF on standby. 2022-level flooding could displace 45 lakh people.",
        "status": "active",
        "escalation": "monitoring",
        "severity": "HIGH",
        "region": "Assam - Guwahati",
        "state": "Assam",
        "affected_areas": ["Kamrup Metropolitan", "Barpeta", "Nalbari", "Morigaon", "Dhubri"],
        "started_at": "2026-04-01T00:00:00",
        "last_updated": "2026-04-15T07:00:00",
        "source": "CWC Flood Bulletin / Assam SDMA",
        "key_facts": [
            "Water level: 49.2m (danger mark: 49.68m)",
            "Rising at 0.15m per day",
            "Upstream dam releases from Bhutan increased",
            "NDRF teams on standby in Kamrup Metropolitan",
            "2022 floods at similar levels displaced 45 lakh people",
            "Pre-positioned 200 boats and relief supplies"
        ],
        "impact": {
            "people_affected": "~45 lakh (if breaches danger mark)",
            "economic_loss": "Potential ₹8,000 crore crop + infrastructure damage",
            "sectors_impacted": ["Disaster", "Agriculture", "Health", "Infrastructure"]
        },
        "timeline": [
            {"date": "2026-04-01", "event": "Brahmaputra rises above warning level at Guwahati"},
            {"date": "2026-04-05", "event": "Bhutan increases dam releases upstream"},
            {"date": "2026-04-10", "event": "NDRF pre-positioned; boats deployed"},
            {"date": "2026-04-15", "event": "Water level 49.2m and rising; close to danger mark"}
        ],
        "govt_response": "NDRF standby. SDMA activated. Flood control rooms operational 24/7. Pre-positioned relief supplies.",
        "tags": ["flood", "Brahmaputra", "Assam", "Guwahati", "NDRF", "disaster"]
    },
    {
        "id": "EVT-2026-007",
        "type": "naxal",
        "title": "Naxal Activity Surge — Chhattisgarh Bastar",
        "summary": "40-50 armed Naxal cadres active in Bijapur-Sukma-Dantewada triangle. IED recoveries, CRPF ambush with 2 jawans injured. Area domination operations intensified.",
        "status": "active",
        "escalation": "stable",
        "severity": "HIGH",
        "region": "Chhattisgarh - Bastar",
        "state": "Chhattisgarh",
        "affected_areas": ["Bijapur", "Sukma", "Dantewada", "Basaguda-Bijapur Road", "Tarrem"],
        "started_at": "2026-03-10T00:00:00",
        "last_updated": "2026-04-14T16:00:00",
        "source": "CRPF Intelligence Wing",
        "key_facts": [
            "40-50 armed cadres active in Bijapur-Sukma-Dantewada triangle",
            "IED recovered on Basaguda-Bijapur road",
            "2 CRPF jawans injured in ambush near Tarrem",
            "Helicopter surveillance activated",
            "Local markets shut in Konta and Dornapal for 3 days",
            "12 tribal villages on high alert"
        ],
        "impact": {
            "people_affected": "~75,000 (tribal population in alert zone)",
            "economic_loss": "Market closures affecting local livelihoods",
            "sectors_impacted": ["Security", "Tribal Welfare", "Infrastructure"]
        },
        "timeline": [
            {"date": "2026-03-10", "event": "Intelligence reports movement of 40-50 cadres"},
            {"date": "2026-03-18", "event": "IED found on Basaguda-Bijapur road"},
            {"date": "2026-03-25", "event": "CRPF ambush near Tarrem — 2 jawans injured"},
            {"date": "2026-04-05", "event": "Helicopter surveillance and area domination intensified"},
            {"date": "2026-04-14", "event": "Markets shut in Konta/Dornapal; combing ops continue"}
        ],
        "govt_response": "CRPF area domination ops. Helicopter surveillance. IED sweeps on key roads. District admin on alert.",
        "tags": ["Naxal", "Maoist", "Chhattisgarh", "Bastar", "CRPF", "IED", "security"]
    },
    {
        "id": "EVT-2026-008",
        "type": "protest",
        "title": "Anti-Reservation Bharat Bandh — Rajasthan & Gujarat",
        "summary": "Student unions call Bharat Bandh on April 20 against reservation policy. Coordinated mobilization in Jaipur, Ahmedabad, Udaipur, Surat. 140 flashpoints identified by police.",
        "status": "active",
        "escalation": "escalating",
        "severity": "HIGH",
        "region": "Rajasthan - Gujarat",
        "state": "Rajasthan / Gujarat",
        "affected_areas": ["Jaipur", "Ahmedabad", "Udaipur", "Surat", "All major highways"],
        "started_at": "2026-04-10T00:00:00",
        "last_updated": "2026-04-15T09:00:00",
        "source": "IB Assessment",
        "key_facts": [
            "Bharat Bandh call for April 20",
            "Student unions leading; social media mobilization underway",
            "140 potential flashpoints identified by state police",
            "Previous similar bandh in 2025 caused ₹2,500 crore losses",
            "Railways advised to increase station security",
            "Section 144 likely in major cities"
        ],
        "impact": {
            "people_affected": "~15 crore (Rajasthan + Gujarat combined)",
            "economic_loss": "Estimated ₹2,500 crore (based on 2025 precedent)",
            "sectors_impacted": ["Economy", "Transport", "Education", "Trade"]
        },
        "timeline": [
            {"date": "2026-04-10", "event": "Bharat Bandh call circulated on social media"},
            {"date": "2026-04-12", "event": "Student unions coordinate across states"},
            {"date": "2026-04-14", "event": "Police identify 140 flashpoints; prep begins"},
            {"date": "2026-04-15", "event": "IB assessment flags high risk; Section 144 recommended"}
        ],
        "govt_response": "State police on high alert. 140 flashpoints under surveillance. Section 144 to be imposed. Railways security enhanced.",
        "tags": ["reservation", "protest", "bandh", "students", "Rajasthan", "Gujarat"]
    }
]


_incidents = [
    {
        "id": "INC-2026-0001",
        "title": "Pothole on NH-48 causing accidents",
        "category": "Infrastructure",
        "severity": "high",
        "description": "Large pothole (~3ft wide) on NH-48 near Manesar toll plaza, lane 2. Two bike accidents reported in last 24 hours. Needs immediate repair.",
        "location": "NH-48, Manesar Toll Plaza, Gurugram, Haryana",
        "lat": 28.3594,
        "lon": 76.9380,
        "reported_by": "Citizen — Rajesh Kumar",
        "contact": "+91-98XXX-XXXXX",
        "department": "NHAI / PWD Haryana",
        "status": "assigned",
        "priority": "urgent",
        "created_at": "2026-04-13T09:30:00",
        "updated_at": "2026-04-14T11:00:00",
        "updates": [
            {"timestamp": "2026-04-13T10:15:00", "note": "Received and forwarded to NHAI regional office.", "by": "System"},
            {"timestamp": "2026-04-14T11:00:00", "note": "Assigned to PWD maintenance crew. Repair scheduled for Apr 15.", "by": "NHAI Gurugram"},
        ],
    },
    {
        "id": "INC-2026-0002",
        "title": "Contaminated water supply in Ward 12",
        "category": "Health & Sanitation",
        "severity": "critical",
        "description": "Brownish water with foul smell from municipal taps in Ward 12 since April 10. Multiple families reporting stomach illness. Children worst affected.",
        "location": "Ward 12, Muzaffarpur, Bihar",
        "lat": 26.1209,
        "lon": 85.3647,
        "reported_by": "Ward Councillor — Priya Devi",
        "contact": "+91-97XXX-XXXXX",
        "department": "PHE Dept / Municipal Corp Muzaffarpur",
        "status": "in-progress",
        "priority": "urgent",
        "created_at": "2026-04-11T14:20:00",
        "updated_at": "2026-04-14T16:00:00",
        "updates": [
            {"timestamp": "2026-04-11T15:00:00", "note": "Water sample collected for lab testing.", "by": "PHE Inspector"},
            {"timestamp": "2026-04-12T10:30:00", "note": "E.coli detected. Chlorination team dispatched.", "by": "PHE Lab"},
            {"timestamp": "2026-04-14T16:00:00", "note": "Emergency chlorination done. Tanker supply arranged for 72 hours.", "by": "Municipal Corp"},
        ],
    },
    {
        "id": "INC-2026-0003",
        "title": "Illegal tree felling in Aarey Colony",
        "category": "Environment",
        "severity": "high",
        "description": "Approximately 50 trees felled overnight in Aarey Colony buffer zone. No permission boards visible. Locals suspect land encroachment.",
        "location": "Aarey Colony, Goregaon East, Mumbai",
        "lat": 19.1550,
        "lon": 72.8674,
        "reported_by": "Citizen — Meera Patel",
        "contact": "+91-90XXX-XXXXX",
        "department": "Forest Dept Maharashtra / BMC",
        "status": "under-review",
        "priority": "high",
        "created_at": "2026-04-14T06:45:00",
        "updated_at": "2026-04-14T12:00:00",
        "updates": [
            {"timestamp": "2026-04-14T08:00:00", "note": "FIR registered. Forest ranger dispatched for site inspection.", "by": "Forest Dept"},
        ],
    },
    {
        "id": "INC-2026-0004",
        "title": "Street lights non-functional for 2 weeks",
        "category": "Infrastructure",
        "severity": "moderate",
        "description": "All 12 street lights on MG Road (between crossing 4 and 7) non-functional since April 1. Area is unsafe for women after dark. Multiple complaints ignored.",
        "location": "MG Road, Sector 14, Gurugram, Haryana",
        "lat": 28.4595,
        "lon": 77.0266,
        "reported_by": "RWA President — Sunil Sharma",
        "contact": "+91-88XXX-XXXXX",
        "department": "MCG Electrical Division",
        "status": "submitted",
        "priority": "normal",
        "created_at": "2026-04-14T18:00:00",
        "updated_at": "2026-04-14T18:00:00",
        "updates": [],
    },
    {
        "id": "INC-2026-0005",
        "title": "Crop damage due to unseasonal hailstorm",
        "category": "Agriculture",
        "severity": "high",
        "description": "Hailstorm on April 12 destroyed standing wheat crop across 200+ hectares in Bundi district. 450 farmers affected. Need crop insurance assessment and immediate relief.",
        "location": "Bundi District, Rajasthan",
        "lat": 25.4305,
        "lon": 75.6376,
        "reported_by": "Block Development Officer — Ramesh Meena",
        "contact": "+91-94XXX-XXXXX",
        "department": "Agriculture Dept Rajasthan / PMFBY Cell",
        "status": "in-progress",
        "priority": "urgent",
        "created_at": "2026-04-12T16:00:00",
        "updated_at": "2026-04-15T09:00:00",
        "updates": [
            {"timestamp": "2026-04-12T18:00:00", "note": "Preliminary report filed with District Collector.", "by": "BDO Bundi"},
            {"timestamp": "2026-04-13T11:00:00", "note": "Satellite imagery requested for crop loss assessment.", "by": "Agriculture Dept"},
            {"timestamp": "2026-04-15T09:00:00", "note": "PMFBY insurance team arriving April 16 for ground survey.", "by": "PMFBY Cell"},
        ],
    },
]

_incident_counter = 5


# ===================== LIVE EVENTS API =====================
@app.get("/api/live-events")
async def get_live_events(
    event_type: str = None, state: str = None,
    severity: str = None, status: str = None
):
    """Get all live events with optional filters"""
    filtered = _live_events
    if event_type:
        filtered = [e for e in filtered if e["type"] == event_type]
    if state:
        filtered = [e for e in filtered if state.lower() in e.get("state", "").lower()]
    if severity:
        filtered = [e for e in filtered if e["severity"] == severity.upper()]
    if status:
        filtered = [e for e in filtered if e["status"] == status]

    severity_order = {"CRITICAL": 3, "HIGH": 2, "MODERATE": 1, "LOW": 0}
    filtered.sort(key=lambda e: severity_order.get(e.get("severity", "LOW"), 0), reverse=True)

    stats = {
        "total": len(_live_events),
        "active": sum(1 for e in _live_events if e["status"] == "active"),
        "escalating": sum(1 for e in _live_events if e["escalation"] == "escalating"),
        "critical": sum(1 for e in _live_events if e["severity"] == "CRITICAL"),
        "by_type": {}
    }
    for e in _live_events:
        t = e["type"]
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1

    return {"events": filtered, "stats": stats}


@app.get("/api/live-events/{event_id}")
async def get_live_event(event_id: str):
    """Get a single live event by ID"""
    for e in _live_events:
        if e["id"] == event_id:
            return e
    raise HTTPException(status_code=404, detail="Event not found")


@app.post("/api/live-events")
async def create_live_event(request: dict):
    """Add a new live event to the tracker"""
    event_num = len(_live_events) + 1
    event = {
        "id": f"EVT-2026-{str(event_num).zfill(3)}",
        "type": request.get("type", "other"),
        "title": request.get("title", "Untitled Event"),
        "summary": request.get("summary", ""),
        "status": "active",
        "escalation": request.get("escalation", "monitoring"),
        "severity": request.get("severity", "MODERATE"),
        "region": request.get("region", "Unknown"),
        "state": request.get("state", "Unknown"),
        "affected_areas": request.get("affected_areas", []),
        "started_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "source": request.get("source", "Field Report"),
        "key_facts": request.get("key_facts", []),
        "impact": request.get("impact", {}),
        "timeline": [{"date": datetime.now().strftime("%Y-%m-%d"), "event": "Event reported and tracking initiated"}],
        "govt_response": request.get("govt_response", "Under assessment"),
        "tags": request.get("tags", [])
    }
    _live_events.append(event)
    # Ingest into RAG so AI can answer questions about it
    _ingest_live_events_to_rag()
    return {"id": event["id"], "message": "Live event added to tracker and knowledge base"}


@app.patch("/api/live-events/{event_id}")
async def update_live_event(event_id: str, request: dict):
    """Update a live event — add timeline entry, change status/escalation"""
    for e in _live_events:
        if e["id"] == event_id:
            if "status" in request:
                e["status"] = request["status"]
            if "escalation" in request:
                e["escalation"] = request["escalation"]
            if "severity" in request:
                e["severity"] = request["severity"]
            if "update_note" in request:
                e["timeline"].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "event": request["update_note"]
                })
            if "key_fact" in request:
                e["key_facts"].append(request["key_fact"])
            e["last_updated"] = datetime.now().isoformat()
            _ingest_live_events_to_rag()
            return {"message": "Event updated", "event": e}
    raise HTTPException(status_code=404, detail="Event not found")


# ─── Analytics Intelligence Endpoint ─────────────────────────────────
@app.get("/api/analytics")
async def get_analytics():
    """Comprehensive analytics: disasters, geography, trends, outbreaks, crop failures, floods"""
    return {
        "summary": {
            "total_incidents": 4827,
            "active_alerts": 38,
            "risk_zones": 142,
            "data_sources": 67,
            "confidence_index": 94.2,
            "last_updated": "2026-04-15T09:30:00Z"
        },
        "disaster_management": {
            "total_events_ytd": 312,
            "lives_saved": 18420,
            "evacuations": 94,
            "response_time_avg_min": 22,
            "by_type": [
                {"type": "Floods", "count": 98, "deaths": 247, "affected": 1840000, "economic_loss_cr": 12400, "trend": "rising"},
                {"type": "Cyclones", "count": 12, "deaths": 86, "affected": 920000, "economic_loss_cr": 8900, "trend": "stable"},
                {"type": "Earthquakes", "count": 34, "deaths": 12, "affected": 180000, "economic_loss_cr": 3200, "trend": "stable"},
                {"type": "Landslides", "count": 67, "deaths": 134, "affected": 95000, "economic_loss_cr": 2100, "trend": "rising"},
                {"type": "Droughts", "count": 28, "deaths": 0, "affected": 4200000, "economic_loss_cr": 18700, "trend": "rising"},
                {"type": "Heatwaves", "count": 41, "deaths": 312, "affected": 7600000, "economic_loss_cr": 5400, "trend": "rising"},
                {"type": "Cold Waves", "count": 18, "deaths": 89, "affected": 1200000, "economic_loss_cr": 1800, "trend": "declining"},
                {"type": "Industrial", "count": 14, "deaths": 23, "affected": 45000, "economic_loss_cr": 4300, "trend": "stable"}
            ],
            "monthly_trend": [
                {"month": "Jan", "events": 18, "critical": 3},
                {"month": "Feb", "events": 14, "critical": 1},
                {"month": "Mar", "events": 22, "critical": 4},
                {"month": "Apr", "events": 31, "critical": 7},
                {"month": "May", "events": 45, "critical": 12},
                {"month": "Jun", "events": 58, "critical": 18},
                {"month": "Jul", "events": 62, "critical": 22},
                {"month": "Aug", "events": 54, "critical": 16},
                {"month": "Sep", "events": 38, "critical": 9},
                {"month": "Oct", "events": 28, "critical": 5},
                {"month": "Nov", "events": 16, "critical": 2},
                {"month": "Dec", "events": 12, "critical": 1}
            ]
        },
        "geographic_risk": {
            "high_risk_zones": [
                {"state": "Assam", "risk_score": 92, "primary_threat": "Floods", "districts_affected": 22, "population_at_risk": 8400000},
                {"state": "Bihar", "risk_score": 88, "primary_threat": "Floods", "districts_affected": 18, "population_at_risk": 12600000},
                {"state": "Uttarakhand", "risk_score": 85, "primary_threat": "Landslides", "districts_affected": 8, "population_at_risk": 1200000},
                {"state": "Odisha", "risk_score": 82, "primary_threat": "Cyclones", "districts_affected": 14, "population_at_risk": 6800000},
                {"state": "Maharashtra", "risk_score": 78, "primary_threat": "Droughts", "districts_affected": 12, "population_at_risk": 9400000},
                {"state": "Rajasthan", "risk_score": 76, "primary_threat": "Heatwaves", "districts_affected": 16, "population_at_risk": 11200000},
                {"state": "Kerala", "risk_score": 74, "primary_threat": "Floods", "districts_affected": 6, "population_at_risk": 2100000},
                {"state": "Tamil Nadu", "risk_score": 72, "primary_threat": "Cyclones", "districts_affected": 10, "population_at_risk": 5400000},
                {"state": "West Bengal", "risk_score": 70, "primary_threat": "Cyclones", "districts_affected": 8, "population_at_risk": 4200000},
                {"state": "Gujarat", "risk_score": 68, "primary_threat": "Droughts", "districts_affected": 11, "population_at_risk": 7800000}
            ],
            "region_distribution": {
                "North": {"states": 7, "risk_avg": 65, "top_threat": "Heatwaves"},
                "South": {"states": 5, "risk_avg": 62, "top_threat": "Cyclones"},
                "East": {"states": 5, "risk_avg": 78, "top_threat": "Floods"},
                "West": {"states": 4, "risk_avg": 58, "top_threat": "Droughts"},
                "Central": {"states": 4, "risk_avg": 55, "top_threat": "Heatwaves"},
                "Northeast": {"states": 8, "risk_avg": 82, "top_threat": "Floods"}
            }
        },
        "historical_trends": {
            "yearly_comparison": [
                {"year": 2020, "disasters": 198, "deaths": 1124, "affected_millions": 18.4, "loss_cr": 32000},
                {"year": 2021, "disasters": 224, "deaths": 987, "affected_millions": 22.1, "loss_cr": 38000},
                {"year": 2022, "disasters": 267, "deaths": 1342, "affected_millions": 28.6, "loss_cr": 45000},
                {"year": 2023, "disasters": 289, "deaths": 1089, "affected_millions": 31.2, "loss_cr": 52000},
                {"year": 2024, "disasters": 305, "deaths": 956, "affected_millions": 26.8, "loss_cr": 48000},
                {"year": 2025, "disasters": 312, "deaths": 903, "affected_millions": 24.4, "loss_cr": 56800}
            ],
            "insights": [
                "Disaster frequency increased 57% since 2020, driven by climate change",
                "Death toll declining 20% due to improved early warning systems",
                "Economic losses rising 77% — infrastructure vulnerability remains high",
                "Flood events up 34% correlated with erratic monsoon patterns",
                "Heatwave duration increased avg 8 days per year since 2020"
            ]
        },
        "disease_outbreaks": {
            "active_outbreaks": [
                {"disease": "Dengue", "state": "Kerala", "cases": 4820, "deaths": 12, "status": "spreading", "since": "2026-02-14"},
                {"disease": "Malaria", "state": "Odisha", "cases": 8940, "deaths": 34, "status": "contained", "since": "2025-11-02"},
                {"disease": "Cholera", "state": "Bihar", "cases": 1240, "deaths": 8, "status": "post-flood", "since": "2026-03-20"},
                {"disease": "Leptospirosis", "state": "Maharashtra", "cases": 620, "deaths": 4, "status": "monsoon-linked", "since": "2026-03-08"},
                {"disease": "Japanese Encephalitis", "state": "Assam", "cases": 342, "deaths": 28, "status": "seasonal", "since": "2026-01-15"},
                {"disease": "Chikungunya", "state": "Tamil Nadu", "cases": 2180, "deaths": 2, "status": "spreading", "since": "2026-02-28"}
            ],
            "monthly_cases": [
                {"month": "Jan", "dengue": 420, "malaria": 1200, "cholera": 80, "others": 340},
                {"month": "Feb", "dengue": 680, "malaria": 980, "cholera": 120, "others": 290},
                {"month": "Mar", "dengue": 1240, "malaria": 1400, "cholera": 460, "others": 480},
                {"month": "Apr", "dengue": 1890, "malaria": 2100, "cholera": 580, "others": 620}
            ],
            "correlation_note": "Post-flood disease surge: 78% of cholera cases occur within 3 weeks of major flooding events"
        },
        "crop_failure": {
            "total_area_affected_hectares": 4200000,
            "estimated_loss_cr": 28400,
            "farmers_affected": 3400000,
            "compensation_disbursed_cr": 8200,
            "by_crop": [
                {"crop": "Rice (Kharif)", "area_affected_ha": 1240000, "loss_percent": 32, "states": ["Bihar", "Assam", "West Bengal"], "cause": "Floods"},
                {"crop": "Wheat (Rabi)", "area_affected_ha": 890000, "loss_percent": 18, "states": ["Punjab", "Haryana", "Madhya Pradesh"], "cause": "Heatwaves"},
                {"crop": "Cotton", "area_affected_ha": 720000, "loss_percent": 28, "states": ["Maharashtra", "Gujarat", "Telangana"], "cause": "Pest Attack + Drought"},
                {"crop": "Sugarcane", "area_affected_ha": 540000, "loss_percent": 15, "states": ["Uttar Pradesh", "Maharashtra", "Karnataka"], "cause": "Water Scarcity"},
                {"crop": "Pulses", "area_affected_ha": 480000, "loss_percent": 24, "states": ["Rajasthan", "Madhya Pradesh", "Maharashtra"], "cause": "Drought"},
                {"crop": "Oilseeds", "area_affected_ha": 330000, "loss_percent": 21, "states": ["Rajasthan", "Gujarat", "Madhya Pradesh"], "cause": "Erratic Rainfall"}
            ],
            "seasonal_impact": {
                "kharif_2025": {"total_loss_percent": 22, "primary_cause": "Late monsoon + Floods"},
                "rabi_2025_26": {"total_loss_percent": 14, "primary_cause": "Heatwave in Feb-Mar"}
            }
        },
        "flood_analysis": {
            "total_events_2025_26": 98,
            "total_area_inundated_sqkm": 124000,
            "total_deaths": 247,
            "total_displaced": 1840000,
            "river_systems_at_risk": [
                {"river": "Brahmaputra", "risk": "extreme", "states": ["Assam", "Arunachal Pradesh"], "flood_events": 28, "peak_discharge_cumecs": 72400},
                {"river": "Ganga", "risk": "very high", "states": ["Bihar", "Uttar Pradesh", "West Bengal"], "flood_events": 22, "peak_discharge_cumecs": 65200},
                {"river": "Godavari", "risk": "high", "states": ["Maharashtra", "Telangana", "Andhra Pradesh"], "flood_events": 14, "peak_discharge_cumecs": 42800},
                {"river": "Mahanadi", "risk": "high", "states": ["Chhattisgarh", "Odisha"], "flood_events": 12, "peak_discharge_cumecs": 38600},
                {"river": "Krishna", "risk": "moderate", "states": ["Maharashtra", "Karnataka", "Andhra Pradesh"], "flood_events": 8, "peak_discharge_cumecs": 28400},
                {"river": "Kosi", "risk": "extreme", "states": ["Bihar", "Nepal border"], "flood_events": 18, "peak_discharge_cumecs": 24800}
            ],
            "monthly_inundation_sqkm": [
                {"month": "Jun", "area": 8200},
                {"month": "Jul", "area": 34600},
                {"month": "Aug", "area": 42800},
                {"month": "Sep", "area": 28400},
                {"month": "Oct", "area": 8600},
                {"month": "Nov", "area": 1400}
            ],
            "dam_levels": [
                {"dam": "Hirakud", "state": "Odisha", "capacity_percent": 89, "status": "warning"},
                {"dam": "Sardar Sarovar", "state": "Gujarat", "capacity_percent": 76, "status": "normal"},
                {"dam": "Bhakra Nangal", "state": "Himachal Pradesh", "capacity_percent": 82, "status": "watch"},
                {"dam": "Nagarjuna Sagar", "state": "Telangana", "capacity_percent": 71, "status": "normal"},
                {"dam": "Tehri", "state": "Uttarakhand", "capacity_percent": 94, "status": "critical"},
                {"dam": "Mettur", "state": "Tamil Nadu", "capacity_percent": 62, "status": "normal"}
            ]
        },
        "predictive_alerts": [
            {"type": "Flood", "region": "Assam - Brahmaputra Basin", "probability": 87, "timeframe": "Next 72 hours", "severity": "critical"},
            {"type": "Heatwave", "region": "Rajasthan - Western Districts", "probability": 92, "timeframe": "Next 48 hours", "severity": "high"},
            {"type": "Cyclone", "region": "Bay of Bengal - Odisha Coast", "probability": 45, "timeframe": "Next 5-7 days", "severity": "moderate"},
            {"type": "Crop Failure", "region": "Maharashtra - Vidarbha", "probability": 78, "timeframe": "Current Season", "severity": "high"},
            {"type": "Disease Outbreak", "region": "Bihar - Flood Zones", "probability": 82, "timeframe": "Post-Monsoon", "severity": "high"},
            {"type": "Landslide", "region": "Uttarakhand - Joshimath", "probability": 68, "timeframe": "Next 2 weeks", "severity": "moderate"}
        ]
    }


@app.get("/api/incidents")
async def get_incidents(status: str = None, category: str = None, severity: str = None):
    """Get all incidents with optional filters"""
    filtered = _incidents
    if status:
        filtered = [i for i in filtered if i["status"] == status]
    if category:
        filtered = [i for i in filtered if i["category"] == category]
    if severity:
        filtered = [i for i in filtered if i["severity"] == severity]
    return {
        "incidents": sorted(filtered, key=lambda x: x["created_at"], reverse=True),
        "total": len(_incidents),
        "stats": {
            "submitted": sum(1 for i in _incidents if i["status"] == "submitted"),
            "under_review": sum(1 for i in _incidents if i["status"] == "under-review"),
            "assigned": sum(1 for i in _incidents if i["status"] == "assigned"),
            "in_progress": sum(1 for i in _incidents if i["status"] == "in-progress"),
            "resolved": sum(1 for i in _incidents if i["status"] == "resolved"),
        },
    }


@app.post("/api/incidents")
async def create_incident(req: dict):
    """Raise a new incident"""
    global _incident_counter
    _incident_counter += 1
    inc_id = f"INC-2026-{_incident_counter:04d}"
    now = datetime.now().isoformat(timespec="seconds")

    incident = {
        "id": inc_id,
        "title": req.get("title", "Untitled Incident"),
        "category": req.get("category", "Other"),
        "severity": req.get("severity", "moderate"),
        "description": req.get("description", ""),
        "location": req.get("location", ""),
        "lat": req.get("lat"),
        "lon": req.get("lon"),
        "reported_by": req.get("reported_by", "Anonymous"),
        "contact": req.get("contact", ""),
        "department": _auto_assign_dept(req.get("category", "Other")),
        "status": "submitted",
        "priority": "urgent" if req.get("severity") == "critical" else "normal",
        "created_at": now,
        "updated_at": now,
        "updates": [],
    }
    _incidents.append(incident)
    return {"success": True, "incident": incident}


@app.patch("/api/incidents/{incident_id}")
async def update_incident(incident_id: str, req: dict):
    """Update incident status or add a note"""
    for inc in _incidents:
        if inc["id"] == incident_id:
            if "status" in req:
                inc["status"] = req["status"]
            if "note" in req:
                inc["updates"].append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "note": req["note"],
                    "by": req.get("by", "System"),
                })
            inc["updated_at"] = datetime.now().isoformat(timespec="seconds")
            return {"success": True, "incident": inc}
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get single incident details"""
    for inc in _incidents:
        if inc["id"] == incident_id:
            return inc
    raise HTTPException(status_code=404, detail="Incident not found")


def _auto_assign_dept(category: str) -> str:
    dept_map = {
        "Infrastructure": "Public Works Department (PWD)",
        "Health & Sanitation": "Public Health Engineering / Municipal Corp",
        "Environment": "State Forest Dept / Pollution Control Board",
        "Agriculture": "Agriculture Dept / PMFBY Cell",
        "Law & Order": "District Police / Home Dept",
        "Disaster": "NDMA / State Disaster Management Authority",
        "Education": "Education Dept / District Education Officer",
        "Corruption": "Anti-Corruption Bureau / Lokayukta",
        "Women Safety": "Women & Child Development Dept / Police",
        "Other": "District Collector Office",
    }
    return dept_map.get(category, "District Collector Office")


# ===================== LIVE EVENTS ENDPOINTS =====================

from app.rag_engine import ingest_documents as rag_ingest

def _ingest_live_events_to_rag():
    """Ingest all live events into RAG for AI-powered Q&A."""
    docs = []
    for ev in _live_events:
        facts = "; ".join(ev.get("key_facts", []))
        timeline_str = " | ".join(
            [f"{t['date']}: {t['event']}" for t in ev.get("timeline", [])]
        )
        text = (
            f"LIVE EVENT [{ev['type'].upper()}] — {ev['title']}. "
            f"Status: {ev['status']}, Escalation: {ev['escalation']}, Severity: {ev['severity']}. "
            f"Region: {ev['region']}, State: {ev['state']}. "
            f"{ev['summary']} "
            f"Key facts: {facts}. "
            f"Government response: {ev.get('govt_response', 'N/A')}. "
            f"Timeline: {timeline_str}. "
            f"Impact: {ev.get('impact', {}).get('people_affected', 'N/A')} people affected. "
            f"Economic loss: {ev.get('impact', {}).get('economic_loss', 'N/A')}."
        )
        sector = {
            "protest": "security", "civil_unrest": "security", "war": "security",
            "naxal": "security", "strike": "security", "pandemic": "health",
            "disaster": "disaster",
        }.get(ev["type"], "security")
        docs.append({
            "id": f"live_{ev['id']}",
            "text": text,
            "metadata": {
                "sector": sector,
                "region": ev["region"],
                "date": ev["last_updated"][:10],
                "source": ev["source"],
                "event_type": ev["type"],
                "live_event": "true"
            }
        })
    if docs:
        rag_ingest(docs)


# --- MOVED HERE: app must be defined before any @app routes ---


# =================== Models ===================

class TextQueryRequest(BaseModel):
    text: str
    language_code: str = "en-IN"


class TranslateRequest(BaseModel):
    text: str
    source_language: str = "en-IN"
    target_language: str = "hi-IN"


class TTSRequest(BaseModel):
    text: str
    language_code: str = "hi-IN"


class IngestRequest(BaseModel):
    documents: list[dict]


class AcknowledgeRequest(BaseModel):
    alert_id: str


class NotifyRequest(BaseModel):
    channel: str  # sms, whatsapp, call, all
    message: str
    regions: list[str] = []
    alert_id: str | None = None


class SOSRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str | None = None


class LiveLocationUpdate(BaseModel):
    sos_id: str
    latitude: float
    longitude: float
    timestamp: str | None = None


# =================== Routes ===================

@app.get("/")
async def landing():
    return FileResponse("frontend/index.html")

@app.get("/landing")
async def landing_page():
    return FileResponse("frontend/landing.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("frontend/index.html")


# ---------- Voice Q&A ----------

@app.post("/api/voice-query")
async def voice_query(audio: UploadFile = File(...), language_code: str = Form("auto")):
    """
    Full voice pipeline: audio in → STT → RAG → LLM → TTS → audio + text out
    
    Returns:
    - user_text: What the user said (in their language)
    - user_text_english: What they said in English
    - detected_language: Language code of input audio
    - response_english: AI response in English
    - response_translated: AI response in user's language
    - response_audio_base64: Audio response (base64 encoded)
    - sector: Detected intelligence sector
    - emergency_detected: Whether emergency keywords detected
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file. Please record voice and try again.")
        
        print(f"🎤 Voice query received: {len(audio_bytes)} bytes, language: {language_code}", file=__import__('sys').stderr)
        
        # Process voice query through full pipeline
        result = process_voice_query(audio_bytes, preferred_language=language_code)
        
        print(f"✅ Voice query processed successfully", file=__import__('sys').stderr)
        
        # Ensure audio response exists
        audio_b64 = ""
        if result.get("response_audio"):
            try:
                audio_b64 = base64.b64encode(result["response_audio"]).decode("utf-8")
                print(f"🔊 TTS audio generated: {len(result['response_audio'])} bytes", file=__import__('sys').stderr)
            except Exception as tts_err:
                print(f"⚠️  TTS encoding error: {tts_err}", file=__import__('sys').stderr)
        else:
            print(f"⚠️  No audio response generated from TTS", file=__import__('sys').stderr)

        return {
            "user_text": result.get("user_text", ""),
            "user_text_english": result.get("user_text_english", ""),
            "detected_language": result.get("detected_language", "en-IN"),
            "response_english": result.get("response_english", "No response generated"),
            "response_translated": result.get("response_translated", ""),
            "response_audio_base64": audio_b64,
            "sector": result.get("sector", "general"),
            "emergency_detected": result.get("emergency_detected", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Voice query failed: {str(e)[:200]}"
        print(f"❌ {error_msg}", file=__import__('sys').stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


# ---------- Text Q&A ----------

@app.post("/api/text-query")
async def text_query(req: TextQueryRequest):
    """Text-based query pipeline"""
    result = process_text_query(req.text, language_code=req.language_code)
    return result


# ---------- Translation ----------

@app.post("/api/translate")
async def translate(req: TranslateRequest):
    """Translate text between languages"""
    translated = translate_text(
        req.text,
        source_language=req.source_language,
        target_language=req.target_language,
    )
    return {"translated_text": translated}


# ---------- Text to Speech ----------

@app.post("/api/tts")
async def tts(req: TTSRequest):
    """Convert text to speech"""
    audio_bytes = text_to_speech(req.text, language_code=req.language_code)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_base64": audio_b64}


# ---------- Alerts ----------

@app.get("/api/alerts")
async def alerts(severity: str = None):
    """Get active alerts"""
    return {"alerts": get_active_alerts(severity)}


@app.get("/api/alerts/all")
async def all_alerts():
    """Get all alerts including acknowledged"""
    return {"alerts": get_all_alerts()}


@app.post("/api/alerts/check")
async def trigger_alert_check():
    """Manually trigger an alert analysis"""
    new_alerts = run_alert_check()
    return {"new_alerts": new_alerts, "count": len(new_alerts)}


@app.post("/api/alerts/acknowledge")
async def ack_alert(req: AcknowledgeRequest):
    """Acknowledge an alert"""
    success = acknowledge_alert(req.alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged"}


@app.post("/api/alerts/translate")
async def translate_alert_endpoint(alert_id: str = Form(...), target_language: str = Form(...)):
    """Translate an alert to a target language"""
    all_a = get_all_alerts()
    alert = next((a for a in all_a if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    translated = translate_alert(alert, target_language)
    return translated


# ---------- RAG / Data ----------

@app.post("/api/ingest")
async def ingest(req: IngestRequest):
    """Ingest documents into the knowledge base"""
    count = ingest_documents(req.documents)
    return {"ingested": count}


@app.get("/api/rag/stats")
async def rag_stats():
    """Get RAG knowledge base statistics"""
    return get_stats()


@app.get("/api/rag/search")
async def rag_search(q: str, sector: str = None):
    """Search the knowledge base"""
    results = rag_query(q, sector=sector)
    return {"results": results}


# ---------- Notifications ----------

_notification_log: list[dict] = []
_sos_requests: list[dict] = []


@app.post("/api/notify")
async def send_notification(req: NotifyRequest):
    """Send emergency notification via SMS, WhatsApp, or Call"""
    import time
    from datetime import datetime

    entry = {
        "id": f"notif_{int(time.time())}_{len(_notification_log)}",
        "channel": req.channel,
        "message": req.message,
        "regions": req.regions,
        "alert_id": req.alert_id,
        "timestamp": datetime.now().isoformat(),
        "status": "sent",
    }
    _notification_log.append(entry)

    # In production: integrate Twilio (SMS/Call), WhatsApp Business API, etc.
    return {
        "status": "sent",
        "channel": req.channel,
        "regions": req.regions,
        "notification_id": entry["id"],
    }


@app.get("/api/notifications")
async def get_notifications():
    """Get notification history"""
    return {"notifications": sorted(_notification_log, key=lambda n: n["timestamp"], reverse=True)}


# ---------- SOS / Emergency ----------

@app.post("/api/sos")
async def sos_alert(req: SOSRequest):
    """Receive SOS alert with live location"""
    import time
    from datetime import datetime

    sos = {
        "id": f"sos_{int(time.time())}_{len(_sos_requests)}",
        "latitude": req.latitude,
        "longitude": req.longitude,
        "timestamp": req.timestamp or datetime.now().isoformat(),
        "status": "active",
        "tracking": True,
        "location_trail": [
            {
                "latitude": req.latitude,
                "longitude": req.longitude,
                "timestamp": req.timestamp or datetime.now().isoformat(),
            }
        ],
    }
    _sos_requests.append(sos)

    # In production: dispatch to nearest police (100) and ambulance (108)
    return {"status": "received", "sos_id": sos["id"], "message": "SOS received. Live tracking started. Emergency services notified."}


@app.post("/api/sos/location")
async def update_live_location(req: LiveLocationUpdate):
    """Receive periodic live location update for an active SOS"""
    from datetime import datetime

    sos = next((s for s in _sos_requests if s["id"] == req.sos_id), None)
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found")
    if not sos.get("tracking"):
        return {"status": "stopped", "message": "Tracking already stopped for this SOS."}

    point = {
        "latitude": req.latitude,
        "longitude": req.longitude,
        "timestamp": req.timestamp or datetime.now().isoformat(),
    }
    sos["latitude"] = req.latitude
    sos["longitude"] = req.longitude
    sos["location_trail"].append(point)

    return {"status": "updated", "points": len(sos["location_trail"])}


@app.get("/api/sos/{sos_id}/trail")
async def get_location_trail(sos_id: str):
    """Get the full location trail for an SOS request"""
    sos = next((s for s in _sos_requests if s["id"] == sos_id), None)
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found")
    return {
        "sos_id": sos_id,
        "tracking": sos.get("tracking", False),
        "trail": sos.get("location_trail", []),
    }


@app.post("/api/sos/{sos_id}/stop")
async def stop_tracking(sos_id: str):
    """Stop live location tracking for an SOS"""
    sos = next((s for s in _sos_requests if s["id"] == sos_id), None)
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found")
    sos["tracking"] = False
    return {"status": "stopped", "sos_id": sos_id}


@app.get("/api/sos")
async def get_sos_requests():
    """Get active SOS requests with tracking status"""
    active = [s for s in _sos_requests if s["status"] == "active"]
    return {"sos_requests": active}


# ---------- Health ----------

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Sanket.AI"}

"""
Sample data to seed the RAG knowledge base for demonstration.
Covers: agriculture, disaster management, public health, civil unrest & security across Indian regions.
"""
from app.rag_engine import ingest_documents, get_stats


def seed_sample_data():
    """Seed the knowledge base with sample intelligence data."""
    stats = get_stats()
    if stats["total_documents"] > 0:
        return  # Already seeded

    documents = [
        # =================== AGRICULTURE ===================
        {
            "id": "agri_001",
            "text": "Kharif season 2025-26: Maharashtra's Vidarbha region reports 30% below-normal rainfall in June-July. Soybean sowing delayed by 3 weeks. Soil moisture levels at 45% compared to normal 70%. Farmers in Yavatmal, Akola, and Amravati districts are most affected. Historical data shows similar conditions in 2015 led to 40% crop yield reduction.",
            "metadata": {"sector": "agriculture", "region": "Maharashtra - Vidarbha", "date": "2025-07", "source": "IMD Rainfall Report"},
        },
        {
            "id": "agri_002",
            "text": "Punjab wheat procurement 2025-26: Record 132 lakh metric tonnes procured at MSP of Rs 2,375/quintal. However, late-season heat wave in March caused shriveled grains in 15% of produce in Bathinda and Mansa districts. Quality downgrade affects farmer income by estimated Rs 200-300 per quintal.",
            "metadata": {"sector": "agriculture", "region": "Punjab", "date": "2025-04", "source": "FCI Procurement Report"},
        },
        {
            "id": "agri_003",
            "text": "Kerala's Wayanad district: Coffee plantation yield dropped 25% due to unseasonal rainfall in December 2025. Black pepper production also affected. 12,000 smallholder farmers reported losses. Spices Board recommends crop insurance claims filing before March 2026.",
            "metadata": {"sector": "agriculture", "region": "Kerala - Wayanad", "date": "2025-12", "source": "Spices Board India"},
        },
        {
            "id": "agri_004",
            "text": "Andhra Pradesh Rabi season forecast: Groundnut and sunflower cultivation in Anantapur and Kurnool expected to benefit from above-normal northeast monsoon. Reservoir storage at 85% capacity. Agricultural extension services recommend early sowing by October 15 for optimal results.",
            "metadata": {"sector": "agriculture", "region": "Andhra Pradesh", "date": "2025-09", "source": "AP State Agriculture Dept"},
        },
        {
            "id": "agri_005",
            "text": "Assam tea production Q1 2026: First flush quality rated above average in Upper Assam (Dibrugarh, Tinsukia). However, labor shortage affecting 35% of estates. Organic tea exports to EU increased 22%. Average auction price at Guwahati Tea Auction Centre: Rs 285/kg, up 12% year-on-year.",
            "metadata": {"sector": "agriculture", "region": "Assam", "date": "2026-03", "source": "Tea Board of India"},
        },
        {
            "id": "agri_006",
            "text": "Tamil Nadu paddy cultivation: Cauvery delta districts (Thanjavur, Tiruvarur, Nagapattinam) report water release from Mettur Dam adequate for Samba season. Expected cultivation area: 15.2 lakh hectares. Fertilizer availability stable. Pest surveillance reports moderate risk of brown planthopper in coastal areas.",
            "metadata": {"sector": "agriculture", "region": "Tamil Nadu - Cauvery Delta", "date": "2025-08", "source": "TN Agriculture Dept"},
        },

        # =================== DISASTER MANAGEMENT ===================
        {
            "id": "disaster_001",
            "text": "Brahmaputra river water level at Guwahati: 49.2m against danger mark of 49.68m as of July 15, 2025. Rising trend of 0.15m per day observed. Upstream dam releases from Bhutan increased. NDRF teams on standby in Kamrup Metropolitan. Historical data: 2022 floods at similar levels displaced 45 lakh people in Assam.",
            "metadata": {"sector": "disaster", "region": "Assam - Guwahati", "date": "2025-07", "source": "CWC Flood Bulletin"},
        },
        {
            "id": "disaster_002",
            "text": "Cyclone season forecast Bay of Bengal 2025-26: IMD predicts 4-5 cyclonic storms, 2 likely to be severe. October-December window highest risk for Odisha, Andhra Pradesh, Tamil Nadu coastlines. Pre-positioned relief: 150 NDRF teams, 500 boats, 5000 MT food stocks across east coast states.",
            "metadata": {"sector": "disaster", "region": "East Coast India", "date": "2025-06", "source": "IMD Cyclone Warning"},
        },
        {
            "id": "disaster_003",
            "text": "Uttarakhand landslide risk assessment 2025: 17 new vulnerable zones identified along Char Dham highway construction route. Joshimath subsidence continues — 3mm/month displacement. Chamoli and Rudraprayag districts rated HIGH risk during monsoon. Geological Survey recommends evacuation planning for 23 villages.",
            "metadata": {"sector": "disaster", "region": "Uttarakhand", "date": "2025-05", "source": "GSI Risk Assessment"},
        },
        {
            "id": "disaster_004",
            "text": "Chennai flood model projection: Urban drainage capacity handles up to 150mm/day rainfall. November 2025 forecast shows 3 episodes of 200mm+ rainfall likely. 47 low-lying areas in South Chennai identified as flood-prone. Adyar and Cooum rivers need desilting — currently at 60% capacity. Storm water drain project 78% complete.",
            "metadata": {"sector": "disaster", "region": "Tamil Nadu - Chennai", "date": "2025-10", "source": "Chennai Corp Flood Preparedness"},
        },
        {
            "id": "disaster_005",
            "text": "Gujarat earthquake preparedness: Kutch region seismic monitoring shows minor tremor activity (2.1-3.4 magnitude) in Bhuj-Anjar belt, January 2026. No immediate threat. Building vulnerability assessment: 40% structures in Bhuj not retrofitted since 2001 earthquake. Emergency response drill conducted for 12,000 residents.",
            "metadata": {"sector": "disaster", "region": "Gujarat - Kutch", "date": "2026-01", "source": "Gujarat SDMA"},
        },
        {
            "id": "disaster_006",
            "text": "Madhya Pradesh dam safety audit 2025: Bargi Dam (Jabalpur) spillway gates require maintenance — 2 of 21 gates showing stress fractures. Tawa Dam reservoir at 92% capacity, excess release may affect downstream villages in Hoshangabad. 14 small dams in Bundelkhand classified as structurally deficient.",
            "metadata": {"sector": "disaster", "region": "Madhya Pradesh", "date": "2025-08", "source": "CWC Dam Safety Report"},
        },

        # =================== PUBLIC HEALTH ===================
        {
            "id": "health_001",
            "text": "Dengue outbreak tracking October 2025: Maharashtra reports 8,500 confirmed cases, 40% increase from September. Hotspots: Pune (2,100 cases), Mumbai (1,800), Nagpur (1,200). Aedes mosquito breeding index elevated in urban areas post-monsoon. Hospital bed occupancy at 75% in Pune. Fogging operations intensified in 15 municipal corporations.",
            "metadata": {"sector": "health", "region": "Maharashtra", "date": "2025-10", "source": "IDSP Disease Surveillance"},
        },
        {
            "id": "health_002",
            "text": "Cholera alert Bihar 2025: 340 confirmed cases in Muzaffarpur and East Champaran districts linked to contaminated tube well water after monsoon flooding. 12 deaths reported. ORS distribution to 50,000 households. Water testing reveals E.coli contamination in 35% of sampled tube wells. UNICEF deploying water purification units.",
            "metadata": {"sector": "health", "region": "Bihar", "date": "2025-08", "source": "Bihar Health Dept"},
        },
        {
            "id": "health_003",
            "text": "Japanese Encephalitis surveillance Uttar Pradesh 2025: Gorakhpur division reports 180 suspected cases, 45 confirmed, 8 deaths. Vaccination coverage in affected blocks only 62% (target 90%). BRD Medical College ICU capacity stretched. NVBDCP recommends emergency vector control and vaccination catch-up campaign.",
            "metadata": {"sector": "health", "region": "Uttar Pradesh - Gorakhpur", "date": "2025-09", "source": "NVBDCP Report"},
        },
        {
            "id": "health_004",
            "text": "Kerala Nipah virus preparedness 2026: Kozhikode district health system maintains Level 2 alert following fruit bat surveillance showing 8% Nipah virus antibody prevalence. Contact tracing protocol activated after one suspected case (later negative). 500-bed isolation facility ready. PPE stocks for 30 days maintained at 3 hospitals.",
            "metadata": {"sector": "health", "region": "Kerala - Kozhikode", "date": "2026-02", "source": "Kerala Health Dept"},
        },
        {
            "id": "health_005",
            "text": "Malaria elimination progress Odisha 2025: API (Annual Parasite Index) reduced from 5.8 to 2.3 in tribal districts (Koraput, Malkangiri, Rayagada). LLIN distribution coverage 95%. However, P.falciparum drug resistance detected in 3% of samples from Malkangiri. WHO team recommends ACT efficacy monitoring.",
            "metadata": {"sector": "health", "region": "Odisha - Tribal Districts", "date": "2025-12", "source": "NVBDCP Malaria Report"},
        },
        {
            "id": "health_006",
            "text": "Heat-related illness tracking Rajasthan summer 2025: 1,200 heat stroke cases reported across Jodhpur, Barmer, and Jaisalmer districts during May-June heatwave (48°C peak). 34 deaths confirmed. Public cooling centers operational at 250 locations. ASHA workers distributing ORS to 80,000 vulnerable households. Health advisory issued for outdoor workers.",
            "metadata": {"sector": "health", "region": "Rajasthan - Western", "date": "2025-06", "source": "Rajasthan Health Dept"},
        },

        # =================== CROSS-SECTOR ===================
        {
            "id": "cross_001",
            "text": "Post-flood health-agriculture impact assessment Bihar 2025: Monsoon floods in 14 districts destroyed 3.2 lakh hectares of paddy crop. Standing water created mosquito breeding grounds — malaria cases up 60% in flood-affected areas. Contaminated water supply linked to 2,100 diarrheal disease cases. Recovery timeline: 6-8 months for full agricultural restoration.",
            "metadata": {"sector": "health", "region": "Bihar", "date": "2025-09", "source": "Bihar SDMA Impact Report"},
        },
        {
            "id": "cross_002",
            "text": "Climate-agriculture nexus Western Ghats 2025: Shifting rainfall patterns affecting cardamom, coffee, and tea plantations in Karnataka and Kerala. 15% reduction in Western Ghats rainfall over 5 years. Landslide risk increasing in deforested slopes. Water table drop of 2-3 meters in Kodagu district affecting irrigation. Recommend watershed management and drought-resistant crop varieties.",
            "metadata": {"sector": "agriculture", "region": "Western Ghats - Karnataka/Kerala", "date": "2025-11", "source": "ICAR Climate Report"},
        },

        # =================== CIVIL UNREST & PROTESTS ===================
        {
            "id": "unrest_001",
            "text": "Large-scale farmer protest at Delhi-Haryana border: Approximately 25,000 farmers from Punjab and Haryana have assembled at Singhu and Tikri border points demanding guaranteed MSP legislation. Highway blockade affecting NH-44 traffic. Police deployed 5,000 personnel with water cannons. Protest leaders have called for a 48-hour bandh across Punjab. Essential supply routes being rerouted through Rajasthan corridor.",
            "metadata": {"sector": "security", "region": "Delhi - Haryana Border", "date": "2026-03", "source": "Delhi Police Intelligence"},
        },
        {
            "id": "unrest_002",
            "text": "Communal tension reported in Meerut and Muzaffarnagar districts following a local dispute. Curfew imposed in 4 wards of Meerut city. Section 144 enforced. 200 arrests made in preventive action. Social media monitoring reveals inflammatory posts being circulated. Internet services suspended in affected areas for 48 hours. Rapid Action Force and PAC deployed. District Magistrate has convened peace committee meeting.",
            "metadata": {"sector": "security", "region": "Uttar Pradesh - Meerut", "date": "2026-02", "source": "UP Police Situation Report"},
        },
        {
            "id": "unrest_003",
            "text": "Manipur ethnic violence update April 2026: Fresh clashes reported in Churachandpur and Bishnupur hill districts. 15 houses burned, 3 casualties confirmed. Army column deployed along the valley-hill buffer zone. 2,500 people displaced to relief camps in Imphal East. Internet blackout in 5 districts. Central government advisors en route. National Highway 2 (Imphal-Moreh) partially blocked.",
            "metadata": {"sector": "security", "region": "Manipur", "date": "2026-04", "source": "MHA Situation Report"},
        },
        {
            "id": "unrest_004",
            "text": "Anti-reservation protest movement gaining momentum across Rajasthan and Gujarat. Student unions have called Bharat Bandh on April 20. Social media analysis indicates coordinated mobilization in Jaipur, Ahmedabad, Udaipur, and Surat. State police have identified 140 potential flashpoints. Previous similar bandh in 2025 resulted in Rs 2,500 crore economic losses. Railways has been advised to increase security at stations.",
            "metadata": {"sector": "security", "region": "Rajasthan - Gujarat", "date": "2026-04", "source": "IB Assessment"},
        },

        # =================== SECURITY THREATS ===================
        {
            "id": "security_001",
            "text": "Naxal activity alert Chhattisgarh: Intelligence reports indicate movement of 40-50 armed cadres in Bijapur-Sukma-Dantewada triangle. IED recovery on Basaguda-Bijapur road. 2 CRPF jawans injured in ambush near Tarrem. Area domination operations intensified. Helicopter surveillance activated. Local markets in Konta and Dornapal shut for 3 days. Tribal population in 12 villages advised to stay alert.",
            "metadata": {"sector": "security", "region": "Chhattisgarh - Bastar", "date": "2026-03", "source": "CRPF Intelligence Wing"},
        },
        {
            "id": "security_002",
            "text": "J&K border security update: Pakistan ceasefire violations reported in Poonch and Rajouri sectors — 15 incidents in March 2026. Indian Army retaliatory fire neutralized 2 launch pads. Civilian evacuation from 5km buffer zone affecting 8,000 residents in Mendhar tehsil. BSF has reinforced forward posts with additional battalions. Night surveillance drones deployed along LoC.",
            "metadata": {"sector": "security", "region": "Jammu and Kashmir - Poonch", "date": "2026-03", "source": "Indian Army Northern Command"},
        },
        {
            "id": "security_003",
            "text": "Countrywide strike by transport unions: All India Motor Transport Congress has announced indefinite strike from April 18 over fuel price hike and toll charges. Expected to affect 95 lakh trucks and 50 lakh buses nationwide. Essential commodity supply chain at risk — petroleum, food grains, vegetables. Government has invoked essential services maintenance act in 6 states. Emergency fuel reserves activated for 7 days.",
            "metadata": {"sector": "security", "region": "Pan-India", "date": "2026-04", "source": "Ministry of Road Transport"},
        },
        {
            "id": "security_004",
            "text": "Cyber threat advisory: CERT-In reports a coordinated phishing campaign targeting state government email systems across Maharashtra, Tamil Nadu, and Karnataka. 450 government accounts potentially compromised. Malware strain linked to state-sponsored actor. All departments advised to reset passwords and enable 2FA immediately. NIC conducting emergency audit of all state data centers.",
            "metadata": {"sector": "security", "region": "Maharashtra - Tamil Nadu - Karnataka", "date": "2026-04", "source": "CERT-In Advisory"},
        },
    ]

    count = ingest_documents(documents)
    print(f"Seeded {count} documents into knowledge base")

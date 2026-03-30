"""
TerraGuard SOS NLP Triage Engine - Accurate agency routing
Categorizes SOS messages into Fire, Police, Medical, NDRF.
"""
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "3_backend_services", "sos_nlp_model.pkl")
DISASTER_CSV = os.path.join(PROJECT_ROOT, "disasterIND.csv")

# Extensive training data - diverse phrasings for accurate agency routing
data = [
    # === MEDICAL (Ambulance / Hospital) ===
    ("I think I broke my leg, need an ambulance", "Medical_Response", 6),
    ("Someone is having a heart attack, please hurry!", "Medical_Response", 10),
    ("Deep cut on arm, bleeding heavily after a fall", "Medical_Response", 8),
    ("Man collapsed on the street, not breathing", "Medical_Response", 10),
    ("Child fell from stairs, head injury", "Medical_Response", 8),
    ("Elderly person unconscious, need medical help", "Medical_Response", 9),
    ("Severe allergic reaction, swelling", "Medical_Response", 8),
    ("Stroke suspected, one side paralysis", "Medical_Response", 10),
    ("Overdose, person not responsive", "Medical_Response", 9),
    ("Labor pains, baby coming", "Medical_Response", 9),
    ("Severe asthma attack, inhaler not working", "Medical_Response", 8),
    ("Burned hand on stove, bad blister", "Medical_Response", 6),
    ("Dog bite, bleeding wound", "Medical_Response", 6),
    ("Chest pain, might be heart", "Medical_Response", 9),
    ("Accident on road, people injured", "Medical_Response", 9),
    ("Seizure, person convulsing", "Medical_Response", 9),
    ("Suicide attempt, need ambulance", "Medical_Response", 10),
    ("Heat stroke, person passed out", "Medical_Response", 8),
    ("Choking, cannot breathe", "Medical_Response", 10),
    ("Diabetic emergency, sugar very low", "Medical_Response", 8),

    # === FIRE (Fire Department) ===
    ("There is a huge fire in the apartment building", "Fire_Department", 10),
    ("Kitchen caught on fire, we are outside", "Fire_Department", 7),
    ("Smell thick smoke coming from the garage", "Fire_Department", 5),
    ("Building on fire, people trapped inside", "Fire_Department", 10),
    ("Gas cylinder leaking, smell of gas", "Fire_Department", 9),
    ("Forest fire spreading towards village", "Fire_Department", 9),
    ("Electrical short circuit, sparks and smoke", "Fire_Department", 8),
    ("Petrol pump fire, explosion risk", "Fire_Department", 10),
    ("Factory blaze, workers evacuated", "Fire_Department", 9),
    ("Car on fire on the highway", "Fire_Department", 7),
    ("Wires burning, black smoke", "Fire_Department", 8),
    ("Wildfire near residential area", "Fire_Department", 9),
    ("Oil spill caught fire", "Fire_Department", 8),
    ("Flames visible from next building", "Fire_Department", 8),
    ("Short circuit in meter box", "Fire_Department", 6),
    ("Burning smell from basement", "Fire_Department", 6),
    ("LPG leak, do not light match", "Fire_Department", 10),
    ("Warehouse fire, toxic smoke", "Fire_Department", 9),

    # === POLICE (Crime / Security) ===
    ("Someone is breaking into my house", "Police_Dispatch", 9),
    ("There is a massive fight outside the bar", "Police_Dispatch", 7),
    ("Suspicious person looking into parked cars", "Police_Dispatch", 4),
    ("Robbery in progress at shop", "Police_Dispatch", 9),
    ("Armed men threatening us", "Police_Dispatch", 10),
    ("Domestic violence, woman screaming", "Police_Dispatch", 9),
    ("Burglary, house ransacked", "Police_Dispatch", 7),
    ("Gang fight with weapons", "Police_Dispatch", 9),
    ("Child missing, abducted", "Police_Dispatch", 10),
    ("Car stolen from parking", "Police_Dispatch", 5),
    ("Chain snatching on the road", "Police_Dispatch", 6),
    ("Harassment, man following me", "Police_Dispatch", 6),
    ("Riot, mob destroying property", "Police_Dispatch", 9),
    ("Murder, dead body found", "Police_Dispatch", 10),
    ("Road rage, driver threatening", "Police_Dispatch", 6),
    ("Fraud, fake police demanding money", "Police_Dispatch", 7),
    ("My cat is stuck in a tall tree", "Police_Dispatch", 2),
    ("Noise complaint, loud party", "Police_Dispatch", 3),
    ("Stabbing outside the mall", "Police_Dispatch", 10),
    ("Kidnapping attempt, child safe now", "Police_Dispatch", 9),

    # === NDRF (Natural Disasters / Rescue) ===
    ("Mudslide just blocked the main highway, cars trapped", "NDRF_Rescue", 9),
    ("House collapsed from the earthquake, people trapped", "NDRF_Rescue", 10),
    ("Water is flooding into our basement rapidly", "NDRF_Rescue", 7),
    ("Landslide blocked the road, vehicles stuck", "NDRF_Rescue", 8),
    ("River overflowing, village submerged", "NDRF_Rescue", 9),
    ("Cyclone damage, roofs blown off", "NDRF_Rescue", 9),
    ("Earthquake, building cracks, people scared", "NDRF_Rescue", 9),
    ("Flash flood, people on rooftops", "NDRF_Rescue", 10),
    ("Hill slope collapsing, houses at risk", "NDRF_Rescue", 9),
    ("Heavy rain, waterlogging, cars floating", "NDRF_Rescue", 7),
    ("Dam breach, water rushing in", "NDRF_Rescue", 10),
    ("Cloudburst, sudden flood", "NDRF_Rescue", 9),
    ("Building collapsed due to rain", "NDRF_Rescue", 9),
    ("Storm uprooted trees, roads blocked", "NDRF_Rescue", 7),
    ("People trapped in flood, need rescue boat", "NDRF_Rescue", 10),
    ("Avalanche, tourists trapped", "NDRF_Rescue", 9),
    ("Drought, no water, cattle dying", "NDRF_Rescue", 6),
    ("Heat wave, people fainting", "NDRF_Rescue", 7),
    ("Tsunami warning, evacuate beach", "NDRF_Rescue", 10),
    ("Sinkhole, road caved in", "NDRF_Rescue", 8),

    # === Civilian (Low priority / General) ===
    ("Power went out in our neighborhood", "Civilian", 3),
    ("Water supply problem", "Civilian", 2),
    ("Streetlight not working", "Civilian", 1),
]

DISASTER_TO_CATEGORY = {
    "Flood": "NDRF_Rescue", "Storm": "NDRF_Rescue", "Earthquake": "NDRF_Rescue",
    "Mass movement (wet)": "NDRF_Rescue", "Mass movement (dry)": "NDRF_Rescue",
    "Drought": "NDRF_Rescue", "Extreme temperature": "NDRF_Rescue",
    "Wildfire": "Fire_Department", "Epidemic": "Medical_Response",
    "Glacial lake outburst flood": "NDRF_Rescue", "Infestation": "NDRF_Rescue",
}

def severity_from_impact(deaths, affected):
    if pd.isna(deaths): deaths = 0
    if pd.isna(affected): affected = 0
    return min(10, max(1, int((deaths / 1000 + affected / 100000) * 3 + 3)))

print("Initializing TerraGuard NLP Triage Engine...")

# Add disasterIND examples - limit to avoid overwhelming Fire/Police/Medical
if os.path.exists(DISASTER_CSV):
    df_dis = pd.read_csv(DISASTER_CSV)
    disaster_samples = []
    for _, row in df_dis.iterrows():
        dtype = row.get("Disaster Type", "")
        loc = str(row.get("Location", "")) if pd.notna(row.get("Location")) else ""
        cat = DISASTER_TO_CATEGORY.get(dtype, "NDRF_Rescue")
        sev = severity_from_impact(row.get("Total Deaths", 0) or 0, row.get("Total Affected", 0) or 0)
        if loc and loc != "nan":
            msg = f"{dtype} in {loc}, people affected"
        else:
            msg = f"{dtype} disaster, emergency rescue needed"
        if msg and len(msg) > 5:
            disaster_samples.append((msg, cat, sev))
    # Sample max 80 NDRF from disasterIND to balance with manual data
    import random
    random.seed(42)
    ndrf_dis = [x for x in disaster_samples if x[1] == "NDRF_Rescue"]
    other_dis = [x for x in disaster_samples if x[1] != "NDRF_Rescue"]
    sampled = other_dis + (random.sample(ndrf_dis, min(80, len(ndrf_dis))) if ndrf_dis else [])
    data.extend(sampled)
    print(f"  Added {len(sampled)} balanced examples from disasterIND.csv")

df = pd.DataFrame(data, columns=['message', 'category', 'severity'])

# Use class_weight to handle any remaining imbalance
print("Training NLP Category Classifier (ngram + 200 trees, balanced)...")
category_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)),
    ('clf', RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced'))
])
category_pipeline.fit(df['message'], df['category'])

print("Training NLP Severity Predictor...")
severity_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)),
    ('clf', RandomForestClassifier(n_estimators=200, random_state=42))
])
severity_pipeline.fit(df['message'], df['severity'])

nlp_models = {'category_model': category_pipeline, 'severity_model': severity_pipeline}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
joblib.dump(nlp_models, OUTPUT_PATH)

print(f"\nSaved to {OUTPUT_PATH}")

# Test diverse inputs
tests = [
    "Someone is having a heart attack, please hurry!",
    "Huge fire in the building, people trapped",
    "Flood in Assam, hundreds trapped",
    "Robbery at the bank, armed men",
    "Gas leak, smell everywhere",
]
print("\nLive tests:")
for t in tests:
    c, s = category_pipeline.predict([t])[0], severity_pipeline.predict([t])[0]
    print(f"  '{t[:45]}...' -> {c} (sev:{s})")

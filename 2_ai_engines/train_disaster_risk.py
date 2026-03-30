"""
TerraGuard Disaster Risk Model - Trained on disasterIND.csv
Predicts disaster risk by location using historical India disaster data.
"""
import os
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
CSV_PATH = os.path.join(PROJECT_ROOT, "disasterIND.csv")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "3_backend_services", "disaster_risk_model.pkl")

# Map EM-DAT disaster types to TerraGuard categories
DISASTER_TO_CATEGORY = {
    "Flood": "NDRF_Rescue",
    "Storm": "NDRF_Rescue",
    "Earthquake": "NDRF_Rescue",
    "Mass movement (wet)": "NDRF_Rescue",  # Landslides
    "Mass movement (dry)": "NDRF_Rescue",
    "Drought": "NDRF_Rescue",
    "Extreme temperature": "NDRF_Rescue",
    "Wildfire": "Fire_Department",
    "Epidemic": "Medical_Response",
    "Glacial lake outburst flood": "NDRF_Rescue",
    "Infestation": "NDRF_Rescue",
}

def haversine_km(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    R = 6371  # Earth radius km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

print("Loading disasterIND.csv...")
df = pd.read_csv(CSV_PATH)

# Filter rows with valid coordinates
df_geo = df[df["Latitude"].notna() & df["Longitude"].notna()].copy()
df_geo = df_geo[df_geo["Latitude"] != ""]
df_geo["Latitude"] = pd.to_numeric(df_geo["Latitude"], errors="coerce")
df_geo["Longitude"] = pd.to_numeric(df_geo["Longitude"], errors="coerce")
df_geo = df_geo.dropna(subset=["Latitude", "Longitude"])

# Map disaster type and compute severity (1-10) from deaths/affected
df_geo["disaster_type"] = df_geo["Disaster Type"].fillna("Unknown")
df_geo["category"] = df_geo["disaster_type"].map(
    lambda x: DISASTER_TO_CATEGORY.get(x, "NDRF_Rescue")
)
deaths = df_geo["Total Deaths"].fillna(0)
affected = df_geo["Total Affected"].fillna(0)
# Severity: log-scale of impact
severity = np.clip(
    np.log1p(deaths + affected / 1000) * 1.5,
    1, 10
).astype(int)
df_geo["severity"] = severity

# Convert to radians for BallTree (haversine)
lat_rad = np.radians(df_geo["Latitude"].values)
lon_rad = np.radians(df_geo["Longitude"].values)
coords = np.column_stack([lat_rad, lon_rad])

tree = BallTree(coords, metric="haversine")
earth_radius_km = 6371

model_package = {
    "tree": tree,
    "df": df_geo[["Latitude", "Longitude", "disaster_type", "category", "severity", "Location", "Start Year"]],
    "earth_radius_km": earth_radius_km,
    "disaster_to_category": DISASTER_TO_CATEGORY,
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
joblib.dump(model_package, OUTPUT_PATH)

print(f"Saved to {OUTPUT_PATH}")
print(f"Trained on {len(df_geo)} geo-tagged disasters")
print("Disaster types:", df_geo["disaster_type"].value_counts().head(8).to_dict())

"""
TerraGuard Landslide Prediction Model - Trained on synthetic + disasterIND.csv
Predicts landslide risk from rainfall, soil moisture, and slope.
"""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "3_backend_services", "landslide_model.pkl")
DISASTER_CSV = os.path.join(PROJECT_ROOT, "disasterIND.csv")

print("Initializing TerraGuard Landslide AI Engine...")

# Base synthetic data
np.random.seed(42)
data_size = 1000
rainfall = np.random.uniform(0, 200, data_size)
soil_moisture = np.random.uniform(10, 100, data_size)
slope_angle = np.random.uniform(20, 60, data_size)
risk_factor = (rainfall * 0.5) + (soil_moisture * 0.3) + (slope_angle * 0.2)
landslide_occurred = np.where(risk_factor > 110, 1, 0)

df = pd.DataFrame({
    'rainfall_mm': rainfall,
    'soil_moisture_percent': soil_moisture,
    'slope_angle': slope_angle,
    'landslide_occurred': landslide_occurred
})

# Add real landslide events from disasterIND (Mass movement wet = landslides)
if os.path.exists(DISASTER_CSV):
    dis = pd.read_csv(DISASTER_CSV)
    landslides = dis[dis["Disaster Type"] == "Mass movement (wet)"]
    n = len(landslides)
    if n > 0:
        # Synthesize plausible conditions: high rain, high soil moisture, steep slope
        extra_rain = np.random.uniform(80, 180, n)
        extra_soil = np.random.uniform(60, 95, n)
        extra_slope = np.random.uniform(40, 58, n)
        extra_df = pd.DataFrame({
            'rainfall_mm': extra_rain,
            'soil_moisture_percent': extra_soil,
            'slope_angle': extra_slope,
            'landslide_occurred': np.ones(n, dtype=int)
        })
        df = pd.concat([df, extra_df], ignore_index=True)
        print(f"  Added {n} landslide events from disasterIND")

X = df[['rainfall_mm', 'soil_moisture_percent', 'slope_angle']]
y = df['landslide_occurred']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

accuracy = model.score(X, y) * 100
print(f"Model Training Complete! Accuracy: {accuracy:.2f}%")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
joblib.dump(model, OUTPUT_PATH)
print(f"Saved to {OUTPUT_PATH}")

import numpy as np
import pandas as pd
import joblib
import json

# --- Cargar modelo y scaler ---
MODEL_PATH = "model/exoplanet_model.pkl"
SCALER_PATH = "model/scaler.pkl"
FEATURES_PATH = "model/feature_config.json"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
with open(FEATURES_PATH, 'r') as f:
    feature_columns = json.load(f)

# --- Datos de ejemplo: exoplaneta confirmado ---
# Reemplaza estos valores con los de tu KOI confirmado
exo_data = {
    "koi_period": 9.488035570,
    "koi_time0bk": 170.53875,
    "koi_duration": 2.95750,
    "koi_depth": 6.1580e+02,
    "koi_prad": 2.26,
    "koi_teq": 793.0,
    "koi_insol": 93.59,
    "koi_model_snr": 24.81,
    "koi_steff": 5455.0,
    "koi_slogg": 4.467,
    "koi_srad": 0.9270,
    "koi_score": 1.0
}

# --- Preprocesamiento ---
df_input = pd.DataFrame([exo_data])
X = df_input[feature_columns].copy()
X = X.fillna(X.median())
X_scaled = scaler.transform(X)

# --- Inferencia ---
pred_class = model.predict(X_scaled)[0]
pred_proba = model.predict_proba(X_scaled)[0]

class_map = {0: 'False Positive', 1: 'Candidate', 2: 'Confirmed Exoplanet'}

print("Predicción:", class_map[pred_class])
print("Probabilidades:")
print(f"  False Positive: {pred_proba[0]:.4f}")
print(f"  Candidate: {pred_proba[1]:.4f}")
print(f"  Confirmed Exoplanet: {pred_proba[2]:.4f}")

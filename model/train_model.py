import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import os


def load_nasa_data():
    """
    Load NASA KOI dataset (koi_table.csv) and preprocess
    """
    file_path = "/home/andy/exoclassify-nasa/model/koi_table.csv"
    
    # Cargar CSV ignorando las líneas de comentario que empiezan con '#'
    df = pd.read_csv(file_path, comment='#')
    
    # Seleccionamos las columnas que vas a usar en el modelo
    selected_columns = [
        'koi_period', 'koi_time0bk', 'koi_impact', 'koi_duration',
        'koi_depth', 'koi_prad', 'koi_teq', 'koi_insol', 'koi_model_snr',
        'koi_steff', 'koi_slogg', 'koi_srad', 'koi_score',
        'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec',
        'koi_disposition'
    ]
    
    df = df[selected_columns].copy()
    
    # Features adicionales
    df['transit_shape'] = df['koi_depth'] / df['koi_duration']
    df['density_ratio'] = df['koi_prad'] ** 3 / (df['koi_period'] ** 2)
    df['habitability_index'] = np.exp(-(df['koi_teq'] - 288) ** 2 / (2 * 100 ** 2))
    
    # Target real (clases de NASA)
    target_map = {
        'CONFIRMED': 2,
        'CANDIDATE': 1,
        'FALSE POSITIVE': 0
    }
    df['target'] = df['koi_disposition'].map(target_map)
    
    # Eliminar filas sin target (ej. valores nulos)
    df = df.dropna(subset=['target'])
    
    return df


def preprocess_features(df):
    """Preprocess features for machine learning"""
    # Select features for model
    feature_columns = [
        "koi_period",      # Periodo orbital
        "koi_time0bk",     # Tiempo de tránsito
        "koi_duration",    # Duración del tránsito
        "koi_depth",       # Profundidad del tránsito
        "koi_prad",        # Radio planetario
        "koi_teq",         # Temperatura de equilibrio del planeta
        "koi_insol",       # Insolación recibida
        "koi_steff",       # Temperatura estelar
        "koi_slogg",       # Gravedad superficial de la estrella
        "koi_srad",        # Radio de la estrella
        "koi_model_snr",   # Relación señal/ruido del modelo
        "koi_score"        # Probabilidad asignada por Kepler
    ]
    
    X = df[feature_columns]
    y = df['target']
    
    # Handle missing values
    X = X.fillna(X.median())
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, feature_columns, scaler


def train_model():
    """Train Random Forest classifier"""
    print("Loading NASA exoplanet data...")
    df = load_nasa_data()
    
    print("Preprocessing features...")
    X, y, feature_columns, scaler = preprocess_features(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Training Random Forest classifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                              target_names=['False Positive', 'Candidate', 'Confirmed Exoplanet']))
    
    # Save model and preprocessing objects
    os.makedirs('model', exist_ok=True)
    joblib.dump(model, 'model/exoplanet_model.pkl')
    joblib.dump(scaler, 'model/scaler.pkl')
    
    with open('model/feature_config.json', 'w') as f:
        json.dump(feature_columns, f)
    
    print("Model training completed and saved!")
    
    # Generate sample exoplanet data for frontend
    generate_sample_data(df)
    
    return model, scaler, feature_columns


def generate_sample_data(df):
    """Generate sample exoplanet data for the frontend visualization"""
    sample_size = min(200, len(df))
    sample_df = df.sample(sample_size, random_state=42)
    
    exoplanets = []
    for _, row in sample_df.iterrows():
        # Convert to celestial coordinates (simplified)
        ra = np.random.uniform(0, 360)  # Right Ascension
        dec = np.random.uniform(-90, 90)  # Declination

        exoplanet = {
            'id': f"KOI-{np.random.randint(1000, 9999)}",
            'name': f"KOI-{np.random.randint(1000, 9999)}",
            'ra': ra,
            'dec': dec,
            'classification': ['False Positive', 'Candidate', 'Confirmed Exoplanet'][int(row['target'])],
            'period': float(row['koi_period']),
            'radius': float(row['koi_prad']),
            'temperature': float(row['koi_teq']),
            'depth': float(row['koi_depth']),
            'snr': float(row['koi_model_snr']),
            'magnitude': np.random.uniform(8, 15)  # Apparent magnitude
        }
        exoplanets.append(exoplanet)
    
    with open('/home/andy/exoclassify-nasa/static/data/exoplanets.json', 'w') as f:
        json.dump(exoplanets, f, indent=2)


if __name__ == '__main__':
    train_model()

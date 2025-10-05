from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.preprocessing import StandardScaler
import json
from datetime import datetime
import math

app = Flask(__name__)

# Cargar modelo y objetos de preprocesamiento (con manejo de errores)
try:
    model = joblib.load('/home/andy/exoclassify-nasa/model/model/exoplanet_model.pkl')
    scaler = joblib.load('/home/andy/exoclassify-nasa/model/model/scaler.pkl')
    feature_names = json.load(open('/home/andy/exoclassify-nasa/model/model/feature_config.json', 'r'))
    model_loaded = True
except FileNotFoundError:
    print("⚠️  Model files not found. Please run train_model.py first.")
    model_loaded = False

@app.route('/')
def index():
    """Main dashboard with interactive star map"""
    return render_template('index.html')

@app.route('/classify')
def classify_page():
    """Página de clasificación ML"""
    return render_template('classify.html')

@app.route('/validate')
def validate_page():
    """Página de validación NEOSSat"""
    return render_template('validate.html')

@app.route('/characterize')
def characterize_page():
    """Página de caracterización JWST"""
    return render_template('characterize.html')

def preprocess_features(data):
    """
    Convierte los datos del formulario en el formato esperado por el modelo ML.
    Realiza casting y ordena según feature_names.
    Aplica límites razonables para evitar valores extremos que generen predicciones erróneas.
    """
    # Define límites para cada feature si es necesario (ajusta según tu modelo)
    feature_limits = {
        # 'feature_name': (min, max)
        'koi_period': (0.1, 1000),         # días
        'koi_time0bk': (0, 10000),         # días
        'koi_impact': (0, 1),              # sin unidad
        'koi_duration': (0.1, 100),        # horas
        'koi_depth': (0, 100000),          # ppm
        'koi_prad': (0.1, 30),             # radios terrestres
        'koi_srad': (0.1, 10),             # radios solares
        'koi_smass': (0.1, 5),             # masas solares
        'koi_steff': (2000, 10000),        # K
        'koi_insol': (0, 100),             # S/S_earth
        'koi_model_snr': (0, 1000),        # SNR
        'koi_fpflag_nt': (0, 1),           # flag
        'koi_fpflag_ss': (0, 1),           # flag
        'koi_fpflag_co': (0, 1),           # flag
        'koi_fpflag_ec': (0, 1),           # flag
        # Agrega más si tu modelo lo requiere
    }
    features = []
    for name in feature_names:
        value = data.get(name, 0)
        try:
            value = float(value)
        except Exception:
            value = 0.0
        # Aplica límites si existen para el feature
        if name in feature_limits:
            min_val, max_val = feature_limits[name]
            value = max(min_val, min(max_val, value))
        features.append(value)
    # Escalar si el scaler está disponible
    if scaler:
        features = scaler.transform([features])
    else:
        features = [features]
    return features

# Traducción de clase numérica a etiqueta
CLASS_LABELS = {
    "0": "Confirmed Exoplanet",
    "1": "Candidate",
    "2": "False Positive"
}

# Reporte de entrenamiento del modelo (puedes ponerlo en un archivo aparte si prefieres)
MODEL_REPORT = """
Classification Report:
                     precision    recall  f1-score   support

     False Positive       0.92      0.86      0.89       968
          Candidate       0.61      0.72      0.66       396
Confirmed Exoplanet       0.89      0.87      0.88       549

           accuracy                           0.83      1913
          macro avg       0.80      0.82      0.81      1913
       weighted avg       0.85      0.83      0.84      1913
"""

@app.route('/api/classify', methods=['POST'])
def classify():
    if not model_loaded:
        return jsonify({'error': 'Modelo ML no disponible.'}), 503
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        X = preprocess_features(data)
        pred = model.predict(X)[0]
        proba = model.predict_proba(X)[0]
        pred_label = CLASS_LABELS.get(str(pred), str(pred))
        main_confidence = max(proba)
        result = {
            'prediction': pred_label,
            'confidence': round(main_confidence * 100, 1),
            'probabilities': {CLASS_LABELS.get(str(i), str(i)): round(float(p)*100, 1) for i, p in enumerate(proba)},
            'model_report': MODEL_REPORT
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error en clasificación: {str(e)}'}), 400

@app.route('/api/validate', methods=['POST'])
def validate():
    """NEOSSat contamination validation - análisis básico"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        required_fields = ['ra', 'dec', 'observation_date', 'fov', 'mag_threshold']
        for field in required_fields:
            if field not in data or str(data[field]).strip() == '':
                return jsonify({'error': f'Campo requerido: {field}'}), 400

        try:
            ra = float(data['ra'])
            dec = float(data['dec'])
            fov = float(data['fov'])
            mag_threshold = float(data['mag_threshold'])
            obs_date = str(data['observation_date'])
            datetime.strptime(obs_date, '%Y-%m-%d')
        except Exception:
            return jsonify({'error': 'Datos numéricos o fecha inválidos'}), 400

        # Cálculo de distancia angular a la Luna (posición aproximada)
        moon_ra = 134.68  # grados, ejemplo
        moon_dec = 13.77  # grados, ejemplo

        def angular_distance(ra1, dec1, ra2, dec2):
            ra1_rad = math.radians(ra1)
            dec1_rad = math.radians(dec1)
            ra2_rad = math.radians(ra2)
            dec2_rad = math.radians(dec2)
            cos_d = (math.sin(dec1_rad)*math.sin(dec2_rad) +
                     math.cos(dec1_rad)*math.cos(dec2_rad)*math.cos(ra1_rad-ra2_rad))
            return math.degrees(math.acos(min(1, max(-1, cos_d))))

        dist_moon = angular_distance(ra, dec, moon_ra, moon_dec)

        # Estimación de estrellas brillantes en el campo de visión
        if mag_threshold >= 15:
            density = 50
        elif mag_threshold >= 12:
            density = 10
        else:
            density = 2
        area = math.pi * (fov/2)**2
        bright_stars = int(density * area)

        # Simulación básica de cruce de asteroides/satélites (NEOSSat)
        # Probabilidad simple: si FOV > 2 y mag_threshold > 14, riesgo medio-alto
        crossing_risk = 0
        if fov > 2 and mag_threshold > 14:
            crossing_risk = 0.5
        elif fov > 1:
            crossing_risk = 0.2

        contamination_level = 'limpia'
        color = 'success'
        recommendations = []
        note = 'Este análisis es una estimación basada en datos públicos y simplificaciones. NEOSSat detecta posibles contaminantes como asteroides y satélites.'

        if dist_moon < fov:
            contamination_level = 'altamente contaminada'
            color = 'danger'
            recommendations.append('Cambiar fecha de observación para evitar la Luna.')
        elif bright_stars > 30 or crossing_risk > 0.3:
            contamination_level = 'parcialmente contaminada'
            color = 'warning'
            if bright_stars > 30:
                recommendations.append('Reducir el campo de visión (FOV) para evitar estrellas brillantes.')
            if crossing_risk > 0.3:
                recommendations.append('Verifica posibles cruces de asteroides/satélites en el campo usando NEOSSat.')
            recommendations.append('Considera usar filtros ópticos.')
        else:
            recommendations.append('Condiciones óptimas para observación.')

        try:
            date_obj = datetime.strptime(obs_date, '%Y-%m-%d')
            if date_obj.day in range(13, 17):
                recommendations.append('La Luna podría estar brillante, verifica fase lunar.')
        except Exception:
            pass

        result = {
            'contamination_level': contamination_level,
            'color': color,
            'distance_to_moon_deg': round(dist_moon, 2),
            'bright_stars_estimate': bright_stars,
            'recommendations': recommendations,
            'note': note,
            'summary': (
                f"Nivel: {contamination_level.capitalize()}. "
                f"Distancia a la Luna: {round(dist_moon,2)}°. "
                f"Estrellas brillantes: {bright_stars}. "
                f"Riesgo de cruce de asteroides/satélites: "
                f"{int(crossing_risk*100)}%."
            )
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/api/characterize', methods=['POST'])
def characterize():
    """Caracterización física basada en datos del exoplaneta"""
    if request.method == 'POST':
        data = request.get_json()
        physical = characterize_physical(data)
        return jsonify(physical)

def characterize_physical(data):
    """
    Calcula propiedades físicas y habitabilidad usando datos del exoplaneta.
    Espera: stellar_temp, stellar_radius, stellar_mass, period, radius, planet_mass, koi_insol, eccentricity, albedo
    """
    Tstar = float(data.get('stellar_temp', 5772))         # K
    Rstar = float(data.get('stellar_radius', 1.0))        # Rsun
    Mstar = float(data.get('stellar_mass', 1.0))          # Msun
    P_days = float(data.get('period', 365.25))            # días
    rp = float(data.get('radius', 1.0))                   # R_earth
    Mp = float(data.get('planet_mass', 1.0))              # M_earth
    koi_insol = float(data.get('koi_insol', 1.0))         # S/S_earth
    e = float(data.get('eccentricity', 0.0))              # excentricidad
    albedo = float(data.get('albedo', 0.3))               # albedo

    # Calcular semi-eje mayor si no está presente
    sma = (Mstar * (P_days / 365.25)**2)**(1/3)  # AU

    # Temperatura de equilibrio
    Rsun_to_AU = 0.00465047
    Rstar_AU = Rstar * Rsun_to_AU
    teq = Tstar * np.sqrt(Rstar_AU / (2 * sma)) * (1 - albedo)**0.25

    # Clasificación por radio
    if rp < 1.6:
        planet_type = 'rocoso'
    elif rp < 2.5:
        planet_type = 'transición'
    else:
        planet_type = 'gaseoso'

    # Zona habitable
    if 0.32 < koi_insol < 1.10:
        hz_status = 'Conservadora'
    elif 0.2 < koi_insol < 1.7:
        hz_status = 'Optimista'
    else:
        hz_status = 'Fuera'

    # Probabilidad de tránsito
    transit_prob = (Rstar * Rsun_to_AU) / sma
    transit_prob = min(transit_prob, 1.0)

    # Gravedad superficial
    g_earth = 9.80665
    gravity = g_earth * (Mp / rp**2)

    # Velocidad de escape
    v_earth = 11.186
    escape_velocity = v_earth * np.sqrt(Mp / rp)

    # Score de habitabilidad
    score = 0
    if rp < 1.6: score += 0.4
    elif rp < 2.5: score += 0.2
    if 0.32 < koi_insol < 1.10: score += 0.4
    elif 0.2 < koi_insol < 1.7: score += 0.2
    if e < 0.2: score += 0.1
    if 200 <= teq <= 320: score += 0.1
    habitability_score = min(score, 1.0)

    return {
        'teq': teq,
        'planet_type': planet_type,
        'habitable_zone': hz_status,
        'transit_probability': transit_prob,
        'surface_gravity': gravity,
        'escape_velocity': escape_velocity,
        'habitability_score': habitability_score
    }

@app.route('/api/exoplanets')
def api_exoplanets():
    # Carga desde tu CSV o base de datos
    df = pd.read_csv('/home/andy/exoclassify-nasa/model/model/koi_table.csv', on_bad_lines='skip')
    # Ajusta los nombres de columnas según tu archivo
    exoplanets = []
    for _, row in df.iterrows():
        exoplanets.append({
            "name": row.get("kepoi_name", f"KOI-{row.get('kepoi_number', '')}"),
            "ra": float(row.get("ra", 0)),
            "dec": float(row.get("dec", 0)),
            "classification": row.get("classification", "Candidate")
        })
    return jsonify(exoplanets)

if __name__ == '__main__':
    # Check if model is loaded
    if not model_loaded:
        print("❌ Model not found. Please run: python model/train_model.py")
        print("📁 Creating directory structure...")
        os.makedirs('model', exist_ok=True)
        os.makedirs('static/data', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
    
    print("🚀 Starting ExoClassify NASA Application...")
    print("📊 Available endpoints:")
    print("   http://localhost:5000/              - Dashboard")
    print("   http://localhost:5000/classify      - ML Classification")
    print("   http://localhost:5000/validate      - NEOSSat Validation") 
    print("   http://localhost:5000/characterize  - JWST Characterization")
    print("   http://localhost:5000/api/health    - Health Check")
    
    app.run(debug=True, port=5000)

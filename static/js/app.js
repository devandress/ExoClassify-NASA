// ExoClassify - NASA Space Apps Challenge Frontend Application
class ExoClassifyApp {
    constructor() {
        this.currentExoplanet = null;
        this.currentPrediction = null;
        this.init();
    }

    init() {
        this.initializeEventListeners();
        this.loadInitialData();
        this.showFormDataPreview('classify-form', 'classify-preview');
        this.showFormDataPreview('validate-form', 'validate-preview');
        this.showFormDataPreview('characterize-form', 'characterize-preview');
        console.log('ExoClassify NASA App Initialized');
    }

    initializeEventListeners() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.handleNavigation(e));
        });

        const classifyForm = document.getElementById('classify-form');
        if (classifyForm) {
            classifyForm.addEventListener('submit', (e) => this.handleClassification(e));
        }

        const validateForm = document.getElementById('validate-form');
        if (validateForm) {
            validateForm.addEventListener('submit', (e) => this.handleValidation(e));
        }

        const characterizeForm = document.getElementById('characterize-form');
        if (characterizeForm) {
            characterizeForm.addEventListener('submit', (e) => this.handleCharacterization(e));
        }
    }

    async loadInitialData() {
        try {
            await this.loadExoplanetStatistics();
            this.showNotification('Aplicación lista para producción', 'success');
        } catch (error) {
            this.showNotification('Error al cargar datos iniciales', 'error');
        }
    }

    // Clasificación ML
    async handleClassification(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData);

        this.showLoading('classify-result', 'Analizando datos...');

        try {
            const response = await fetch('/api/classify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                this.displayClassificationResult(result, 'classify-result');
            } else {
                throw new Error(result.error || 'Error en clasificación');
            }
        } catch (error) {
            this.displayError('classify-result', error.message);
        }
    }

    // Validación NEOSSat
    async handleValidation(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData);

        this.showLoading('results', 'Analizando riesgo de contaminación...');

        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                this.displayValidationCards(result);
            } else {
                throw new Error(result.error || 'Error en validación');
            }
        } catch (error) {
            this.displayError('results', error.message);
        }
    }

    // Caracterización JWST
    async handleCharacterization(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData);

        this.showLoading('characterize-result', 'Simulando espectro JWST...');

        try {
            const response = await fetch('/api/characterize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                this.displayCharacterizationResult(result);
            } else {
                throw new Error(result.error || 'Error en caracterización');
            }
        } catch (error) {
            this.displayError('characterize-result', error.message);
        }
    }

    // Mostrar resultados
    displayClassificationResult(result, containerId = 'classify-result') {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = `
            <div class="card bg-light text-dark mb-3">
                <div class="card-body">
                    <h5 class="card-title">ML Prediction</h5>
                    <p class="card-text">
                        <strong>Class:</strong> <span class="text-primary">${result.prediction}</span><br>
                        <strong>Confidence:</strong> ${result.confidence}%<br>
                        <strong>Probabilities:</strong> ${Object.entries(result.probabilities).map(([label, p]) => `${label}: ${p}%`).join(' / ')}
                    </p>
                </div>
            </div>
        `;
        // Mostrar el reporte del modelo
        const reportDiv = document.getElementById('model-report');
        if (reportDiv && result.model_report) {
            reportDiv.innerHTML = `
                <div class="card bg-light text-dark">
                    <div class="card-body">
                        <h6 class="card-title">Model Training Report</h6>
                        <pre class="small">${result.model_report}</pre>
                        <small class="text-muted">This report shows the accuracy and reliability of the ML model based on training data.</small>
                    </div>
                </div>
            `;
        }
    }

    displayValidationCards(result) {
        const container = document.getElementById('results');
        if (!container) return;
        const colorMap = {
            'success': 'bg-success text-white',
            'warning': 'bg-warning text-dark',
            'danger': 'bg-danger text-white'
        };
        container.innerHTML = `
            <div class="card mb-3 ${colorMap[result.color] || ''}">
                <div class="card-body">
                    <h5 class="card-title">Nivel de contaminación: <strong>${result.contamination_level.toUpperCase()}</strong></h5>
                    <p class="card-text">${result.summary}</p>
                </div>
            </div>
            <div class="card mb-3">
                <div class="card-body">
                    <h6 class="card-title">Métricas calculadas</h6>
                    <ul>
                        <li><strong>Distancia angular a la Luna:</strong> ${result.distance_to_moon_deg}°</li>
                        <li><strong>Estrellas brillantes estimadas en el campo:</strong> ${result.bright_stars_estimate}</li>
                    </ul>
                </div>
            </div>
            <div class="card mb-3">
                <div class="card-body">
                    <h6 class="card-title">Recomendaciones</h6>
                    <ul>
                        ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                    <small class="text-muted">${result.note}</small>
                </div>
            </div>
        `;
    }

    displayCharacterizationResult(result) {
        const container = document.getElementById('characterize-result');
        container.innerHTML = `
            <div>
                <h4>Exoplanet Physical Characterization</h4>
                <ul class="list-group mb-3">
                    <li class="list-group-item"><strong>Equilibrium Temperature:</strong> ${result.teq.toFixed(1)} K</li>
                    <li class="list-group-item"><strong>Planet Type:</strong> ${result.planet_type}</li>
                    <li class="list-group-item"><strong>Habitable Zone:</strong> ${result.habitable_zone}</li>
                    <li class="list-group-item"><strong>Transit Probability:</strong> ${(result.transit_probability*100).toFixed(2)}%</li>
                    <li class="list-group-item"><strong>Surface Gravity:</strong> ${result.surface_gravity.toFixed(2)} m/s²</li>
                    <li class="list-group-item"><strong>Escape Velocity:</strong> ${result.escape_velocity.toFixed(2)} km/s</li>
                    <li class="list-group-item"><strong>Habitability Score:</strong> ${(result.habitability_score*100).toFixed(1)}%</li>
                </ul>
                <div>
                    <small class="text-muted">These metrics are estimated from the input parameters. The habitability score is a simple indicator and not a guarantee of actual habitability.</small>
                </div>
            </div>
        `;
    }

    async loadExoplanetStatistics() {
        try {
            const response = await fetch('/api/exoplanets');
            const exoplanets = await response.json();
            const stats = {
                total: exoplanets.length,
                confirmed: exoplanets.filter(e => e.classification === 'Confirmed Exoplanet').length,
                candidates: exoplanets.filter(e => e.classification === 'Candidate').length,
                falsePositives: exoplanets.filter(e => e.classification === 'False Positive').length
            };
            this.updateStatisticsDisplay(stats);
        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
        }
    }

    updateStatisticsDisplay(stats) {
        const elements = {
            'total-exoplanets': stats.total,
            'confirmed-exoplanets': stats.confirmed,
            'candidate-exoplanets': stats.candidates,
            'false-positive-exoplanets': stats.falsePositives
        };
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value.toLocaleString();
            }
        });
    }

    showLoading(containerId, message = 'Procesando...') {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-success mb-2" role="status"></div>
                <p>${message}</p>
            </div>
        `;
    }

    displayError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification.parentNode) notification.remove();
        }, 5000);
    }

    showFormDataPreview(formId, previewId) {
        const form = document.getElementById(formId);
        const preview = document.getElementById(previewId);
        if (!form || !preview) return;

        form.addEventListener('input', () => {
            const formData = new FormData(form);
            let html = '<ul>';
            for (const [key, value] of formData.entries()) {
                html += `<li><strong>${key}:</strong> ${value}</li>`;
            }
            html += '</ul>';
            preview.innerHTML = html;
        });
    }
}

async function renderCelestialExoplanets() {
    // Configura el mapa celestial
    Celestial.display({
        width: 900,
        projection: "aitoff",
        datapath: "", // No necesitas rutas extra
        container: "celestial-map",
        stars: false,
        dsos: false,
        constellations: {
            names: true,
            lines: true,
            bounds: false
        },
        planets: { show: false },
        interactive: true
    });

    // Obtén los exoplanetas del backend
    let exoplanets = [];
    try {
        const response = await fetch('/api/exoplanets');
        exoplanets = await response.json();
    } catch (e) {
        console.error("Error loading exoplanets:", e);
        return;
    }

    // Prepara los datos para D3-celestial
    const exoFeatures = {
        type: "FeatureCollection",
        features: exoplanets.map(exo => ({
            type: "Feature",
            id: exo.name,
            properties: {
                name: exo.name,
                classification: exo.classification
            },
            geometry: {
                type: "Point",
                coordinates: [exo.ra, exo.dec]
            }
        }))
    };

    // Añade los exoplanetas como puntos personalizados
    Celestial.add({
        type: "exoplanets",
        callback: function() {
            Celestial.plot({
                type: "point",
                data: exoFeatures,
                style: function(d) {
                    // Color por clasificación
                    if (d.properties.classification === "Confirmed Exoplanet") return "#198754";
                    if (d.properties.classification === "Candidate") return "#0dcaf0";
                    return "#dc3545";
                },
                size: 6,
                tooltip: function(d) {
                    return `<strong>${d.properties.name}</strong><br>${d.properties.classification}`;
                }
            });
        }
    });
}

// Llama a la función al cargar la página principal
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('celestial-map')) {
        renderCelestialExoplanets();
    }
    window.app = new ExoClassifyApp();
    const savedTheme = localStorage.getItem('exoclassify-theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
});

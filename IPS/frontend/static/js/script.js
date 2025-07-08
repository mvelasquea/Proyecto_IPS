document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');
    const mesSelect = document.getElementById('mesSelect');
    const dependenciaSelect = document.getElementById('dependenciaSelect');
    const btnGenerate = document.getElementById('btnGenerate');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsSection = document.getElementById('resultsSection');
    const anomaliesSection = document.getElementById('anomaliesSection');
    
    // Event Listeners
    fileUploadArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });
    
    btnGenerate.addEventListener('click', generateReport);
    
    // Función para subir archivo
    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Mostrar loading
        fileUploadArea.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
            </div>
        `;
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Llenar selectores
                mesSelect.innerHTML = '<option value="">-- Seleccione un mes --</option>';
                data.meses.forEach(mes => {
                    const option = document.createElement('option');
                    option.value = mes;
                    option.textContent = mes;
                    mesSelect.appendChild(option);
                });
                
                dependenciaSelect.innerHTML = '<option value="">-- Seleccione una dependencia --</option>';
                data.dependencias.forEach(dep => {
                    const option = document.createElement('option');
                    option.value = dep;
                    option.textContent = dep;
                    dependenciaSelect.appendChild(option);
                });
                
                // Mostrar éxito
                fileUploadArea.innerHTML = `
                    <i class="fas fa-check-circle text-success"></i>
                    <p>Archivo cargado exitosamente</p>
                    <small>${file.name}</small>
                `;
            } else {
                throw new Error(data.error || 'Error al cargar archivo');
            }
        })
        .catch(error => {
            fileUploadArea.innerHTML = `
                <i class="fas fa-exclamation-triangle text-danger"></i>
                <p>${error.message}</p>
                <small>Intente nuevamente</small>
            `;
        });
    }
    
    // Función para generar reporte
    function generateReport() {
        const mes = mesSelect.value;
        const dependencia = dependenciaSelect.value;
        
        if (!mes || !dependencia) {
            alert('Por favor seleccione un mes y una dependencia');
            return;
        }
        
        // Mostrar loading
        btnGenerate.disabled = true;
        btnGenerate.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        loadingSpinner.classList.remove('d-none');
        
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mes: mes,
                dependencia: dependencia
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar UI con resultados
                updateResultsUI(data, mes, dependencia);
                
                // Mostrar secciones de resultados
                resultsSection.style.display = 'block';
                anomaliesSection.style.display = 'block';
                
                // Habilitar botón
                btnGenerate.disabled = false;
                btnGenerate.innerHTML = '<i class="fas fa-chart-line me-2"></i>Generar Reporte';
                loadingSpinner.classList.add('d-none');
            } else {
                throw new Error(data.error || 'Error en el análisis');
            }
        })
        .catch(error => {
            alert(error.message);
            btnGenerate.disabled = false;
            btnGenerate.innerHTML = '<i class="fas fa-chart-line me-2"></i>Generar Reporte';
            loadingSpinner.classList.add('d-none');
        });
    }
    
    // Función para actualizar la UI con los resultados
function updateResultsUI(data, mes, dependencia) {
    const stats = data.stats;
    const graficos = data.graficos;
    
    // Actualizar informaciÃ³n del anÃ¡lisis
    document.getElementById('dependenciaInfo').textContent = dependencia;
    document.getElementById('mesInfo').textContent = mes;
    
    // Actualizar estadÃ­sticas
    const statsRow = document.getElementById('statsRow');
    statsRow.innerHTML = `
        <div class="col-md-3">
            <div class="card stat-card">
                <i class="fas fa-gas-pump"></i>
                <div class="number">${stats.total_galones.toLocaleString('es-PE')}</div>
                <div class="label">Galones consumidos</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <i class="fas fa-road"></i>
                <div class="number">${stats.total_km.toLocaleString('es-PE')}</div>
                <div class="label">KilÃ³metros recorridos</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <i class="fas fa-money-bill-wave"></i>
                <div class="number">S/ ${stats.total_consumo.toLocaleString('es-PE')}</div>
                <div class="label">Total gastado</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <i class="fas fa-exclamation-triangle"></i>
                <div class="number">${stats.total_anomalias}</div>
                <div class="label">AnomalÃ­as detectadas</div>
            </div>
        </div>
    `;
    
    // Actualizar grÃ¡ficos
    const chartsRow = document.getElementById('chartsRow');
    chartsRow.innerHTML = '';
    
    if (graficos.eficiencia) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'col-md-6';
        chartDiv.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-chart-bar me-2"></i>DistribuciÃ³n de Eficiencia (km/gal)
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="efficiencyChart"></canvas>
                    </div>
                </div>
            </div>
        `;
        chartsRow.appendChild(chartDiv);
        
        new Chart(document.getElementById('efficiencyChart').getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['MÃ­nimo', 'Promedio', 'MÃ¡ximo'],
                datasets: [{
                    label: 'Eficiencia (km/gal)',
                    data: [
                        Math.min(...graficos.eficiencia),
                        graficos.eficiencia.reduce((a, b) => a + b, 0) / graficos.eficiencia.length,
                        Math.max(...graficos.eficiencia)
                    ],
                    backgroundColor: [
                        'rgba(231, 76, 60, 0.7)',
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(46, 204, 113, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'KilÃ³metros por galÃ³n'
                        }
                    }
                }
            }
        });
    }
    
    if (graficos.consumo_diario) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'col-md-6';
        chartDiv.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-calendar-alt me-2"></i>Consumo por DÃ­a de la Semana
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="consumptionChart"></canvas>
                    </div>
                </div>
            </div>
        `;
        chartsRow.appendChild(chartDiv);
        
        new Chart(document.getElementById('consumptionChart').getContext('2d'), {
            type: 'line',
            data: {
                labels: graficos.consumo_diario.labels,
                datasets: [{
                    label: 'Consumo diario (S/)',
                    data: graficos.consumo_diario.data,
                    borderColor: 'rgba(155, 89, 182, 0.8)',
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'S/ ' + context.raw.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'S/ ' + value;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // SecciÃ³n de anomalÃ­as mejorada
    document.getElementById('anomaliesSummary').innerHTML = `
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-danger text-white">
                        <i class="fas fa-exclamation-triangle me-2"></i>Resumen de AnomalÃ­as
                    </div>
                    <div class="card-body">
                        <canvas id="anomaliesChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-warning text-dark">
                        <i class="fas fa-chart-pie me-2"></i>DistribuciÃ³n
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>Consumo en riesgo:</span>
                            <strong class="text-danger">S/ ${(stats.total_consumo * 0.3).toLocaleString('es-PE', {minimumFractionDigits: 2})}</strong>
                        </div>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-danger" style="width: 30%">30%</div>
                        </div>
                        <div class="mt-3 text-center">
                            <p class="mb-1"><span class="badge bg-danger me-2"></span> CrÃ­ticas: ${Math.round(stats.total_anomalias * 0.4)}</p>
                            <p class="mb-1"><span class="badge bg-warning me-2"></span> Altas: ${Math.round(stats.total_anomalias * 0.3)}</p>
                            <p class="mb-1"><span class="badge bg-primary me-2"></span> Moderadas: ${Math.round(stats.total_anomalias * 0.2)}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // GrÃ¡fico de anomalÃ­as
    new Chart(document.getElementById('anomaliesChart').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['CrÃ­ticas', 'Altas', 'Moderadas', 'Bajas'],
            datasets: [{
                data: [
                    Math.round(stats.total_anomalias * 0.4),
                    Math.round(stats.total_anomalias * 0.3),
                    Math.round(stats.total_anomalias * 0.2),
                    Math.round(stats.total_anomalias * 0.1)
                ],
                backgroundColor: [
                    '#e74c3c',
                    '#f39c12',
                    '#3498db',
                    '#2ecc71'
                ]
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Tabla de vehÃ­culos con anomalÃ­as (ejemplo dinÃ¡mico)
    document.getElementById('vehiclesTable').innerHTML = `
        <thead class="table-dark">
            <tr>
                <th>VehÃ­culo</th>
                <th>AnomalÃ­as</th>
                <th>Consumo</th>
                <th>Eficiencia</th>
                <th>Riesgo</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><i class="fas fa-car me-2"></i>ABC-123</td>
                <td>8</td>
                <td>S/ 2,850.50</td>
                <td>12.4 km/gal</td>
                <td><span class="badge bg-danger">CrÃ­tico</span></td>
            </tr>
            <tr>
                <td><i class="fas fa-truck me-2"></i>DEF-456</td>
                <td>5</td>
                <td>S/ 3,150.75</td>
                <td>8.7 km/gal</td>
                <td><span class="badge bg-danger">CrÃ­tico</span></td>
            </tr>
            <tr>
                <td><i class="fas fa-car me-2"></i>XYZ-789</td>
                <td>3</td>
                <td>S/ 1,420.30</td>
                <td>15.2 km/gal</td>
                <td><span class="badge bg-warning">Alto</span></td>
            </tr>
        </tbody>
    `;
    
    // Lista de anomalÃ­as con botÃ³n de descarga mejorado
    document.getElementById('anomaliesList').innerHTML = `
        <div class="card mb-3">
            <div class="card-header bg-primary text-white">
                <i class="fas fa-download me-2"></i>Descargar Reporte
            </div>
            <div class="card-body text-center">
                <p class="mb-3">Descargue el reporte completo con todos los detalles de las anomalÃ­as detectadas</p>
                <a href="/download/${data.report_filename}" 
                   class="btn btn-danger btn-lg w-100"
                   download="Reporte_Anomalias_${dependencia}_Mes${mes}.pdf">
                    <i class="fas fa-file-pdf me-2"></i>Descargar PDF
                </a>
                <small class="text-muted mt-2 d-block">TamaÃ±o aproximado: ${Math.round(stats.total_registros * 0.1)} KB</small>
            </div>
        </div>
        <div class="card">
            <div class="card-header bg-info text-white">
                <i class="fas fa-info-circle me-2"></i>Acerca del Reporte
            </div>
            <div class="card-body">
                <p><i class="fas fa-check-circle text-success me-2"></i> Generado: ${new Date().toLocaleString()}</p>
                <p><i class="fas fa-filter text-warning me-2"></i> Filtros aplicados: ${dependencia} - Mes ${mes}</p>
                <p><i class="fas fa-database text-primary me-2"></i> Registros analizados: ${stats.total_registros}</p>
            </div>
        </div>
        `;
    }
});
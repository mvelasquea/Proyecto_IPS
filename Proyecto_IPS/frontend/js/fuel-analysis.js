/**
 * Sistema Completo de Análisis de Combustible
 * Detección de fraudes y anomalías en consumo de combustible
 */
class FuelAnalysisSystem {
  constructor() {
    this.baseURL = "http://localhost:8000";
    this.currentFile = null;
    this.currentAnalysis = null;
    this.currentUser = null;
    this.monitoringInterval = null;
    this.alertConfigs = [];
    this.init();
  }

  /**
   * Inicializa el sistema
   */
  init() {
    console.log("Iniciando sistema completo de análisis de combustible...");
    this.setupEventListeners();
    this.checkAPIHealth();
    this.loadUserSession();
    this.showSection("dashboard");
  }

  /**
   * Configura los event listeners
   */
  setupEventListeners() {
    // Navegación del menú
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const section = e.target.getAttribute("data-section");
        this.showSection(section);
      });
    });

    // Tabs de autenticación
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.switchAuthTab(e.target.getAttribute("data-tab"));
      });
    });

    // Formularios de autenticación
    document
      .getElementById("loginFormElement")
      .addEventListener("submit", (e) => {
        e.preventDefault();
        this.login();
      });

    document
      .getElementById("registerFormElement")
      .addEventListener("submit", (e) => {
        e.preventDefault();
        this.register();
      });

    // Upload de archivos
    const uploadBtn = document.getElementById("uploadBtn");
    const fileInput = document.getElementById("fileInput");

    if (uploadBtn) {
      uploadBtn.addEventListener("click", () => {
        if (fileInput) fileInput.click();
      });
    }

    if (fileInput) {
      fileInput.addEventListener("change", (e) => this.handleFileUpload(e));
    }

    // Botones de análisis
    const analyzeBtn = document.getElementById("analyzeBtn");
    if (analyzeBtn) {
      analyzeBtn.addEventListener("click", () => this.analyzeData());
    }

    // Botones de predicción
    const predictBtn = document.getElementById("predictBtn");
    if (predictBtn) {
      predictBtn.addEventListener("click", () => this.generatePrediction());
    }

    // Botones de monitoreo
    const startMonitoringBtn = document.getElementById("startMonitoring");
    const stopMonitoringBtn = document.getElementById("stopMonitoring");

    if (startMonitoringBtn) {
      startMonitoringBtn.addEventListener("click", () =>
        this.startMonitoring()
      );
    }

    if (stopMonitoringBtn) {
      stopMonitoringBtn.addEventListener("click", () => this.stopMonitoring());
    }

    // Formulario de alertas
    const alertConfigForm = document.getElementById("alertConfigForm");
    if (alertConfigForm) {
      alertConfigForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.configureAlert();
      });
    }

    // Botones de reportes
    const generateReportBtn = document.getElementById("generateReportBtn");
    const generateChartReportBtn = document.getElementById(
      "generateChartReportBtn"
    );

    if (generateReportBtn) {
      generateReportBtn.addEventListener("click", () => this.generateReport());
    }

    if (generateChartReportBtn) {
      generateChartReportBtn.addEventListener("click", () =>
        this.generateChartReport()
      );
    }
  }

  /**
   * Muestra una sección específica
   */
  showSection(sectionName) {
    console.log(`Mostrando sección: ${sectionName}`);

    // Ocultar todas las secciones
    document.querySelectorAll(".section").forEach((section) => {
      section.style.display = "none";
    });

    // Mostrar sección seleccionada
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
      targetSection.style.display = "block";
    }

    // Actualizar navegación activa
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.remove("active");
    });

    const activeLink = document.querySelector(
      `[data-section="${sectionName}"]`
    );
    if (activeLink) {
      activeLink.classList.add("active");
    }
  }

  switchAuthTab(tab) {
    // Cambiar tabs activos
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add("active");

    // Cambiar formularios activos
    document.querySelectorAll(".auth-form").forEach((form) => {
      form.classList.remove("active");
    });
    document.getElementById(`${tab}Form`).classList.add("active");
  }

  /**
   * Verifica el estado de la API
   */
  async checkAPIHealth() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      const data = await response.json();

      const statusElement = document.getElementById("apiStatus");
      if (statusElement) {
        statusElement.textContent = "Conectado";
        statusElement.className = "status connected";
      }
      console.log("API conectada correctamente");
    } catch (error) {
      console.error("API no disponible:", error);
      const statusElement = document.getElementById("apiStatus");
      if (statusElement) {
        statusElement.textContent = "Desconectado";
        statusElement.className = "status disconnected";
      }
    }
  }

  // ==================== AUTENTICACIÓN ====================
  async login() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    if (!email || !password) {
      this.showMessage("Por favor complete todos los campos", "error");
      return;
    }

    try {
      const response = await fetch(`${this.baseURL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();

      if (response.ok) {
        this.currentUser = result.user;
        localStorage.setItem("userToken", result.token);
        localStorage.setItem("userData", JSON.stringify(result.user));
        this.updateUserInterface();
        this.showMessage("Inicio de sesión exitoso", "success");
        this.showSection("dashboard");
      } else {
        this.showMessage(result.message || "Error al iniciar sesión", "error");
      }
    } catch (error) {
      console.error("Error en login:", error);
      this.showMessage("Error de conexión", "error");
    }
  }

  async register() {
    const name = document.getElementById("registerName").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;
    const role = document.getElementById("registerRole").value;

    if (!name || !email || !password) {
      this.showMessage("Por favor complete todos los campos", "error");
      return;
    }

    try {
      const response = await fetch(`${this.baseURL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, email, password, role }),
      });

      const result = await response.json();

      if (response.ok) {
        this.showMessage(
          "Registro exitoso. Ahora puede iniciar sesión",
          "success"
        );
        this.switchAuthTab("login");
      } else {
        this.showMessage(result.message || "Error al registrarse", "error");
      }
    } catch (error) {
      console.error("Error en registro:", error);
      this.showMessage("Error de conexión", "error");
    }
  }

  loadUserSession() {
    const token = localStorage.getItem("userToken");
    const userData = localStorage.getItem("userData");

    if (token && userData) {
      this.currentUser = JSON.parse(userData);
      this.updateUserInterface();
    }
  }

  updateUserInterface() {
    const userInfo = document.getElementById("userInfo");
    if (userInfo && this.currentUser) {
      userInfo.innerHTML = `
                <div class="user-info">
                    <span>👤 ${this.currentUser.name}</span>
                    <span class="user-role">${this.currentUser.role}</span>
                    <button onclick="window.fuelSystem.logout()" class="btn btn-logout">Cerrar Sesión</button>
                </div>
            `;
    }
  }

  logout() {
    this.currentUser = null;
    localStorage.removeItem("userToken");
    localStorage.removeItem("userData");
    this.updateUserInterface();
    this.showMessage("Sesión cerrada exitosamente", "info");
    this.showSection("auth");
  }

  // ==================== ANÁLISIS DE DATOS ====================
  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    console.log("Archivo seleccionado:", file.name);

    // Validar archivo
    if (
      !file.name.toLowerCase().endsWith(".xlsx") &&
      !file.name.toLowerCase().endsWith(".xls")
    ) {
      this.showMessage(
        "Error: Solo se permiten archivos Excel (.xlsx, .xls)",
        "error"
      );
      return;
    }

    // Validar tamaño
    if (file.size > 10 * 1024 * 1024) {
      // 10MB
      this.showMessage(
        "Error: El archivo excede el tamaño máximo de 10MB",
        "error"
      );
      return;
    }

    // Mostrar información del archivo
    const fileInfo = document.getElementById("fileInfo");
    if (fileInfo) {
      fileInfo.innerHTML = `
                <div class="file-details">
                    <h4>✅ Archivo seleccionado:</h4>
                    <p><strong>Nombre:</strong> ${file.name}</p>
                    <p><strong>Tamaño:</strong> ${(
                      file.size /
                      1024 /
                      1024
                    ).toFixed(2)} MB</p>
                    <p><strong>Tipo:</strong> ${file.type}</p>
                    <p><strong>Última modificación:</strong> ${new Date(
                      file.lastModified
                    ).toLocaleString()}</p>
                </div>
            `;
    }

    // Habilitar botón de análisis
    const analyzeBtn = document.getElementById("analyzeBtn");
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
    }

    this.currentFile = file;
    this.showMessage(
      'Archivo cargado correctamente. Vaya a "Análisis" para procesar.',
      "success"
    );

    // Cambiar automáticamente a la sección de análisis
    setTimeout(() => {
      this.showSection("analysis");
    }, 1000);
  }

  /**
   * Analiza los datos del archivo
   */
  async analyzeData() {
    if (!this.currentFile) {
      this.showMessage("Error: No hay archivo seleccionado", "error");
      return;
    }

    try {
      this.showLoading(true);
      this.showMessage("Analizando datos, por favor espere...", "info");

      const formData = new FormData();
      formData.append("file", this.currentFile);

      // Agregar filtros si están definidos
      const filters = this.getAnalysisFilters();
      formData.append("filters", JSON.stringify(filters));

      const response = await fetch(`${this.baseURL}/analizar/`, {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${localStorage.getItem("userToken")}`,
        },
      });

      const result = await response.json();

      if (!response.ok || result.status === "error") {
        throw new Error(
          result.message || result.detalle || "Error desconocido"
        );
      }

      console.log("Análisis completado:", result);
      this.currentAnalysis = result;
      this.displayResults(result);
      this.saveAnalysisHistory(result);
      this.showMessage("✅ Análisis completado exitosamente", "success");
    } catch (error) {
      console.error("Error en análisis:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    } finally {
      this.showLoading(false);
    }
  }

  getAnalysisFilters() {
    return {
      dateFrom: document.getElementById("dateFrom").value,
      dateTo: document.getElementById("dateTo").value,
      vehicle: document.getElementById("vehicleFilter").value,
      zone: document.getElementById("zoneFilter").value,
    };
  }

  /**
   * Muestra los resultados del análisis
   */
  displayResults(analysis) {
    console.log("Mostrando resultados del análisis");

    // Mostrar estadísticas
    const statsContainer = document.getElementById("statsContainer");
    if (statsContainer && analysis.estadisticas) {
      const stats = analysis.estadisticas;
      statsContainer.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>${stats.total_registros || 0}</h3>
                        <p>Total de Registros</p>
                    </div>
                    <div class="stat-card">
                        <h3>${stats.anomalias_detectadas || 0}</h3>
                        <p>Anomalías Detectadas</p>
                    </div>
                    <div class="stat-card">
                        <h3>${stats.porcentaje_anomalias || 0}%</h3>
                        <p>Porcentaje de Anomalías</p>
                    </div>
                    <div class="stat-card">
                        <h3>${stats.vehiculos_unicos || 0}</h3>
                        <p>Vehículos Únicos</p>
                    </div>
                </div>
            `;
    }

    // Mostrar tabla de resultados
    const resultsTable = document.getElementById("resultsTable");
    if (resultsTable && analysis.resultados) {
      this.createResultsTable(analysis.resultados, resultsTable);
    }

    // Habilitar botones de reporte
    const reportBtn = document.getElementById("generateReportBtn");
    const chartReportBtn = document.getElementById("generateChartReportBtn");
    if (reportBtn) reportBtn.disabled = false;
    if (chartReportBtn) chartReportBtn.disabled = false;

    // Cambiar a la sección de resultados
    this.showSection("results");
  }

  /**
   * Crea la tabla de resultados
   */
  createResultsTable(data, container) {
    if (!data || data.length === 0) {
      container.innerHTML =
        '<div class="no-results">✅ No se encontraron anomalías en los datos analizados.</div>';
      return;
    }

    const table = document.createElement("table");
    table.className = "results-table";

    // Crear encabezados
    const headers = [
      "Fecha",
      "Placa",
      "Galones",
      "Tipo de Anomalía",
      "Score",
      "Riesgo",
    ];
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    headers.forEach((header) => {
      const th = document.createElement("th");
      th.textContent = header;
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Crear filas de datos
    const tbody = document.createElement("tbody");

    data.slice(0, 100).forEach((item) => {
      const row = document.createElement("tr");

      // Fecha
      const fechaCell = document.createElement("td");
      fechaCell.textContent = item.fecha
        ? new Date(item.fecha).toLocaleDateString("es-ES")
        : "N/A";
      row.appendChild(fechaCell);

      // Placa
      const placaCell = document.createElement("td");
      placaCell.textContent = item.placa || "N/A";
      row.appendChild(placaCell);

      // Galones
      const galonesCell = document.createElement("td");
      galonesCell.textContent = item.galones
        ? parseFloat(item.galones).toFixed(2)
        : "N/A";
      row.appendChild(galonesCell);

      // Tipo de anomalía
      const tipoCell = document.createElement("td");
      tipoCell.textContent = item.tipo_anomalia || "Anomalía Detectada";
      tipoCell.className = "anomaly-type";
      row.appendChild(tipoCell);

      // Score
      const scoreCell = document.createElement("td");
      scoreCell.textContent = item.score_anomalia
        ? parseFloat(item.score_anomalia).toFixed(3)
        : "N/A";
      row.appendChild(scoreCell);

      // Riesgo
      const riesgoCell = document.createElement("td");
      const riesgo = this.calculateRiskLevel(item.score_anomalia);
      riesgoCell.innerHTML = `<span class="risk-level risk-${riesgo.level}">${riesgo.text}</span>`;
      row.appendChild(riesgoCell);

      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.innerHTML = "";
    container.appendChild(table);

    // Agregar información adicional
    if (data.length > 100) {
      const info = document.createElement("p");
      info.className = "table-info";
      info.textContent = `Mostrando las primeras 100 anomalías de ${data.length} detectadas.`;
      container.appendChild(info);
    }
  }

  calculateRiskLevel(score) {
    if (!score) return { level: "low", text: "Bajo" };

    const numScore = parseFloat(score);
    if (numScore >= 0.8) return { level: "high", text: "Alto" };
    if (numScore >= 0.6) return { level: "medium", text: "Medio" };
    return { level: "low", text: "Bajo" };
  }

  // ==================== PREDICCIONES IA ====================
  async generatePrediction() {
    if (!this.currentAnalysis) {
      this.showMessage("Error: Primero debe realizar un análisis", "error");
      return;
    }

    try {
      this.showLoading(true);
      this.showMessage("Generando predicción con IA...", "info");

      const period = document.getElementById("predictionPeriod").value;
      const vehicle = document.getElementById("predictionVehicle").value;

      const response = await fetch(`${this.baseURL}/predecir/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("userToken")}`,
        },
        body: JSON.stringify({
          data: this.currentAnalysis,
          period: period,
          vehicle: vehicle,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || "Error al generar predicción");
      }

      this.displayPredictionResults(result);
      this.showMessage("🔮 Predicción generada exitosamente", "success");
    } catch (error) {
      console.error("Error en predicción:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    } finally {
      this.showLoading(false);
    }
  }

  displayPredictionResults(prediction) {
    const resultsContainer = document.getElementById("predictionResults");
    if (resultsContainer) {
      resultsContainer.innerHTML = `
                <div class="prediction-results-content">
                    <h3>📊 Resultados de la Predicción</h3>
                    <div class="prediction-summary">
                        <div class="prediction-item">
                            <strong>Consumo Proyectado:</strong> ${prediction.consumo_proyectado} galones
                        </div>
                        <div class="prediction-item">
                            <strong>Tendencia:</strong> ${prediction.tendencia}
                        </div>
                        <div class="prediction-item">
                            <strong>Confianza:</strong> ${prediction.confianza}%
                        </div>
                    </div>
                    <div class="prediction-chart">
                        <h4>Gráfico de Predicción</h4>
                        <div id="predictionChart">
                            <!-- Aquí se renderizaría el gráfico -->
                            <p>📈 Gráfico de predicción (implementar con Chart.js)</p>
                        </div>
                    </div>
                </div>
            `;
    }
  }

  // ==================== MONITOREO ====================
  startMonitoring() {
    const interval = document.getElementById("monitoringInterval").value;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.monitoringInterval = setInterval(() => {
      this.checkForUpdates();
    }, interval * 60 * 1000); // Convertir a milisegundos

    document.getElementById("startMonitoring").disabled = true;
    document.getElementById("stopMonitoring").disabled = false;

    const statusElement = document.getElementById("monitoringStatus");
    if (statusElement) {
      statusElement.innerHTML = `<p>Estado: <span class="status-active">Activo</span> (cada ${interval} minutos)</p>`;
    }

    this.showMessage("📡 Monitoreo iniciado exitosamente", "success");
  }

  stopMonitoring() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    document.getElementById("startMonitoring").disabled = false;
    document.getElementById("stopMonitoring").disabled = true;

    const statusElement = document.getElementById("monitoringStatus");
    if (statusElement) {
      statusElement.innerHTML = `<p>Estado: <span class="status-inactive">Inactivo</span></p>`;
    }

    this.showMessage("⏹️ Monitoreo detenido", "info");
  }

  async checkForUpdates() {
    try {
      const response = await fetch(`${this.baseURL}/check-updates/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("userToken")}`,
        },
      });

      const result = await response.json();

      if (result.updates_available) {
        this.showMessage(
          "🔄 Nuevos datos disponibles. Actualizando...",
          "info"
        );
        // Aquí se podría re-ejecutar el análisis automáticamente
      }
    } catch (error) {
      console.error("Error en monitoreo:", error);
    }
  }

  // ==================== ALERTAS ====================
  async configureAlert() {
    const type = document.getElementById("alertType").value;
    const threshold = document.getElementById("alertThreshold").value;
    const vehicle = document.getElementById("alertVehicle").value;

    if (!threshold) {
      this.showMessage("Error: Debe especificar un umbral", "error");
      return;
    }

    try {
      const response = await fetch(`${this.baseURL}/configurar-alerta/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("userToken")}`,
        },
        body: JSON.stringify({
          tipo: type,
          threshold: parseFloat(threshold),
          vehiculo: vehicle,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        this.alertConfigs.push(result);
        this.updateAlertsList();
        this.showMessage("🚨 Alerta configurada exitosamente", "success");
        document.getElementById("alertConfigForm").reset();
      } else {
        throw new Error(result.message || "Error al configurar alerta");
      }
    } catch (error) {
      console.error("Error configurando alerta:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    }
  }

  updateAlertsList() {
    const container = document.getElementById("alertsContainer");
    if (!container) return;

    if (this.alertConfigs.length === 0) {
      container.innerHTML = "<p>No hay alertas configuradas</p>";
      return;
    }

    container.innerHTML = this.alertConfigs
      .map(
        (alert) => `
            <div class="alert-item">
                <div class="alert-info">
                    <strong>${alert.tipo}:</strong> ${alert.threshold}
                    ${alert.vehiculo ? `(${alert.vehiculo})` : ""}
                </div>
                <button onclick="window.fuelSystem.removeAlert('${
                  alert.id
                }')" class="btn btn-danger btn-sm">
                    Eliminar
                </button>
            </div>
        `
      )
      .join("");
  }

  async removeAlert(alertId) {
    try {
      const response = await fetch(
        `${this.baseURL}/eliminar-alerta/${alertId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("userToken")}`,
          },
        }
      );

      if (response.ok) {
        this.alertConfigs = this.alertConfigs.filter(
          (alert) => alert.id !== alertId
        );
        this.updateAlertsList();
        this.showMessage("🗑️ Alerta eliminada", "info");
      }
    } catch (error) {
      console.error("Error eliminando alerta:", error);
      this.showMessage("❌ Error al eliminar alerta", "error");
    }
  }

  // ==================== REPORTES ====================
  async generateReport() {
    if (!this.currentAnalysis) {
      this.showMessage("Error: No hay datos para generar reporte", "error");
      return;
    }

    try {
      this.showLoading(true);
      this.showMessage("Generando reporte PDF...", "info");

      const response = await fetch(`${this.baseURL}/generar-reporte/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("userToken")}`,
        },
        body: JSON.stringify(this.currentAnalysis),
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte_combustible_${
        new Date().toISOString().split("T")[0]
      }.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      this.showMessage("📄 Reporte descargado exitosamente", "success");
    } catch (error) {
      console.error("Error generando reporte:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    } finally {
      this.showLoading(false);
    }
  }

  async generateChartReport() {
    if (!this.currentAnalysis) {
      this.showMessage("Error: No hay datos para generar reporte", "error");
      return;
    }

    try {
      this.showLoading(true);
      this.showMessage("Generando reporte con gráficos...", "info");

      const response = await fetch(
        `${this.baseURL}/generar-reporte-graficos/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("userToken")}`,
          },
          body: JSON.stringify(this.currentAnalysis),
        }
      );

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte_graficos_${
        new Date().toISOString().split("T")[0]
      }.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      this.showMessage(
        "📊 Reporte con gráficos descargado exitosamente",
        "success"
      );
    } catch (error) {
      console.error("Error generando reporte:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    } finally {
      this.showLoading(false);
    }
  }

  // ==================== UTILIDADES ====================
  saveAnalysisHistory(analysis) {
    const history = JSON.parse(localStorage.getItem("analysisHistory") || "[]");
    history.push({
      timestamp: new Date().toISOString(),
      user: this.currentUser?.name || "Usuario",
      summary: analysis.estadisticas,
    });

    // Mantener solo los últimos 50 análisis
    if (history.length > 50) {
      history.splice(0, history.length - 50);
    }

    localStorage.setItem("analysisHistory", JSON.stringify(history));
  }

  /**
   * Muestra un mensaje al usuario
   */
  showMessage(message, type = "info") {
    const messageContainer =
      document.getElementById("messageContainer") || document.body;

    const messageElement = document.createElement("div");
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;

    messageContainer.appendChild(messageElement);

    // Remover mensaje después de 5 segundos
    setTimeout(() => {
      if (messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
      }
    }, 5000);
  }

  /**
   * Muestra/oculta el indicador de carga
   */
  showLoading(show) {
    const loadingElement = document.getElementById("loadingIndicator");
    if (loadingElement) {
      loadingElement.style.display = show ? "block" : "none";

      if (show) {
        // Animar la barra de progreso
        const progressFill = loadingElement.querySelector(".progress-fill");
        if (progressFill) {
          progressFill.style.width = "0%";
          setTimeout(() => {
            progressFill.style.width = "100%";
          }, 100);
        }
      }
    }
  }
}

// Función para inicializar el sistema
function initFuelSystem() {
  console.log("Documento cargado, iniciando sistema completo...");
  window.fuelSystem = new FuelAnalysisSystem();
}

// Inicializar cuando el DOM esté listo
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initFuelSystem);
} else {
  initFuelSystem();
}

// Exportar para uso global
window.FuelAnalysisSystem = FuelAnalysisSystem;
window.initializeFuelSystem = initializeFuelSystem;

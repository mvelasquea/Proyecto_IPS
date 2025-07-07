let loginEmailInput = document.getElementById("loginEmail");
let loginPasswordInput = document.getElementById("loginPassword");
let loginBtn = document.getElementById("loginBtn");
let signupAnchor = document.getElementById("signupAnchor");

let users = [];

if (localStorage.getItem("users") != null) {
  users = JSON.parse(localStorage.getItem("users"));
}

function signIn() {
  let loginEmail = loginEmailInput.value;
  let loginPassword = loginPasswordInput.value;

  if (loginEmailInput.value === "" || loginPasswordInput.value === "") {
    swal({
      text: "Please fill in all fields",
    });
    return;
  }

  if (isCorrectEmailAndPassword(loginEmail, loginPassword)) {
    window.location.href = "home.html";
  } else {
    swal({
      text: "Incorrect email or password",
    });
  }
}

function isCorrectEmailAndPassword(email, password) {
  for (let i = 0; i < users.length; i++) {
    if (users[i].email === email && users[i].password === password) {
      localStorage.setItem("userName", users[i].name);
      return true;
    }
  }
  return false;
}

loginBtn.addEventListener("click", function () {
  signIn();
});

signupAnchor.addEventListener("click", function () {
  window.location.href = "signup.html";
});

// Sistema de Análisis de Combustible
class FuelAnalysisSystem {
  constructor() {
    this.baseURL = "http://localhost:8000";
    this.currentFile = null;
    this.currentAnalysis = null;
    this.init();
  }

  init() {
    console.log("Iniciando sistema de análisis de combustible...");
    this.setupEventListeners();
    this.checkAPIHealth();
    this.showSection("dashboard");
  }

  setupEventListeners() {
    // Navegación del menú
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const section = e.target.getAttribute("data-section");
        this.showSection(section);
      });
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

    // Botón de análisis
    const analyzeBtn = document.getElementById("analyzeBtn");
    if (analyzeBtn) {
      analyzeBtn.addEventListener("click", () => this.analyzeData());
    }

    // Botón de reporte
    const reportBtn = document.getElementById("generateReportBtn");
    if (reportBtn) {
      reportBtn.addEventListener("click", () => this.generateReport());
    }
  }

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

    // Mostrar información del archivo
    const fileInfo = document.getElementById("fileInfo");
    if (fileInfo) {
      fileInfo.innerHTML = `
                <div class="file-details">
                    <h4>✅ Archivo seleccionado:</h4>
                    <p><strong>Nombre:</strong> ${file.name}</p>
                    <p><strong>Tamaño:</strong> ${(file.size / 1024 / 1024).toFixed(
                      2
                    )} MB</p>
                    <p><strong>Tipo:</strong> ${file.type}</p>
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

      const response = await fetch(`${this.baseURL}/analizar/`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok || result.status === "error") {
        throw new Error(result.message || result.detalle || "Error desconocido");
      }

      console.log("Análisis completado:", result);
      this.currentAnalysis = result;
      this.displayResults(result);
      this.showMessage("✅ Análisis completado exitosamente", "success");
    } catch (error) {
      console.error("Error en análisis:", error);
      this.showMessage(`❌ Error: ${error.message}`, "error");
    } finally {
      this.showLoading(false);
    }
  }

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

    // Habilitar botón de reporte
    const reportBtn = document.getElementById("generateReportBtn");
    if (reportBtn) {
      reportBtn.disabled = false;
    }

    // Cambiar a la sección de resultados
    this.showSection("results");
  }

  createResultsTable(data, container) {
    if (!data || data.length === 0) {
      container.innerHTML =
        '<div class="no-results">✅ No se encontraron anomalías en los datos analizados.</div>';
      return;
    }

    const table = document.createElement("table");
    table.className = "results-table";

    // Crear encabezados
    const headers = ["Fecha", "Placa", "Galones", "Tipo de Anomalía", "Score"];
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

  showMessage(message, type = "info") {
    const messageContainer = document.getElementById("messageContainer") || document.body;

    const messageElement = document.createElement("div");
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;

    messageContainer.appendChild(messageElement);

    // Remover mensaje después de 5 segundos



























}  initFuelSystem();} else {  document.addEventListener("DOMContentLoaded", initFuelSystem);if (document.readyState === "loading") {// Inicializar cuando el DOM esté listo}  window.fuelSystem = new FuelAnalysisSystem();  console.log("Documento cargado, iniciando sistema...");function initFuelSystem() {// Función para inicializar el sistema}  }    }      loadingElement.style.display = show ? "block" : "none";    if (loadingElement) {    const loadingElement = document.getElementById("loadingIndicator");  showLoading(show) {  }    }, 5000);      }        messageElement.parentNode.removeChild(messageElement);      if (messageElement.parentNode) {    setTimeout(() => {    setTimeout(() => {
      if (messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
      }
    }, 5000);
  }

  showLoading(show) {
    const loadingElement = document.getElementById("loadingIndicator");
    if (loadingElement) {
      loadingElement.style.display = show ? "block" : "none";
    }
  }
}

// Función para inicializar el sistema
function initFuelSystem() {
  console.log("Documento cargado, iniciando sistema...");
  window.fuelSystem = new FuelAnalysisSystem();
}

// Inicializar cuando el DOM esté listo
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initFuelSystem);
} else {
  initFuelSystem();
}

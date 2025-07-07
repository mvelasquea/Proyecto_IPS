const API_URL = "http://localhost:8000";

class FuelAPI {
  constructor() {
    this.baseURL = "http://localhost:8000";
    this.endpoints = {
      analyze: "/analizar/",
      report: "/generar-reporte/",
      health: "/health",
    };
  }

  /**
   * Analiza un archivo de combustible
   * @param {File} file - Archivo Excel a analizar
   * @returns {Promise<Object>} Resultado del análisis
   */
  async analyzeFile(file) {
    try {
      // Validar archivo
      if (!file) {
        throw new Error("No se ha seleccionado ningún archivo");
      }

      if (
        !file.name.toLowerCase().endsWith(".xlsx") &&
        !file.name.toLowerCase().endsWith(".xls")
      ) {
        throw new Error("El archivo debe ser de formato Excel (.xlsx o .xls)");
      }

      // Crear FormData
      const formData = new FormData();
      formData.append("file", file);

      // Realizar petición
      const response = await fetch(`${this.baseURL}${this.endpoints.analyze}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error HTTP: ${response.status}`);
      }

      const result = await response.json();

      if (result.status === "error") {
        throw new Error(
          result.message || result.detalle || "Error desconocido"
        );
      }

      return result;
    } catch (error) {
      console.error("Error en análisis:", error);
      throw error;
    }
  }

  /**
   * Genera un reporte PDF
   * @param {Object} data - Datos para el reporte
   * @returns {Promise<Blob>} Archivo PDF
   */
  async generateReport(data) {
    try {
      const response = await fetch(`${this.baseURL}${this.endpoints.report}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Error generando reporte: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error("Error generando reporte:", error);
      throw error;
    }
  }

  /**
   * Verifica el estado de la API
   * @returns {Promise<Object>} Estado de la API
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseURL}${this.endpoints.health}`);

      if (!response.ok) {
        throw new Error(`API no disponible: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error verificando estado de API:", error);
      throw error;
    }
  }

  /**
   * Formatea los resultados para mostrar en tabla
   * @param {Array} results - Resultados del análisis
   * @returns {Array} Resultados formateados
   */
  formatResults(results) {
    return results.map((item) => ({
      ...item,
      fecha: item.fecha
        ? new Date(item.fecha).toLocaleDateString("es-ES")
        : "N/A",
      galones: item.galones ? parseFloat(item.galones).toFixed(2) : "N/A",
      costo: item.costo ? `$${parseFloat(item.costo).toFixed(2)}` : "N/A",
      rendimiento: item.rendimiento
        ? `${parseFloat(item.rendimiento).toFixed(2)} km/gal`
        : "N/A",
    }));
  }
}

// Exportar instancia
const fuelAPI = new FuelAPI();

// Para uso en navegador
if (typeof window !== "undefined") {
  window.fuelAPI = fuelAPI;
}

// Para uso en Node.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = fuelAPI;
}

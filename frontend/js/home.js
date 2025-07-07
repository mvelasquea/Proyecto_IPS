// Reemplazar con:
import { FuelApi } from "/js/api/fuelApi.js";

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const history = await FuelApi.getHistory();
    // Actualizar UI con datos históricos
  } catch (error) {
    console.error("Error loading history:", error);
  }
});

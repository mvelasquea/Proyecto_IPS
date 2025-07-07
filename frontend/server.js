const express = require("express");
const path = require("path");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 3000;

// Configuración simple de CORS (puedes quitarlo si no haces peticiones fetch con otros orígenes)
app.use(cors());

// Middleware para parsear JSON y formularios
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Servir archivos estáticos (CSS, JS, imágenes, etc.)
app.use(express.static(path.join(__dirname)));

// Rutas principales
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

app.get("/panel", (req, res) => {
  res.sendFile(path.join(__dirname, "panel.html"));
});

app.get("/home", (req, res) => {
  res.sendFile(path.join(__dirname, "home.html"));
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`✅ Servidor frontend corriendo en: http://localhost:${PORT}`);
});

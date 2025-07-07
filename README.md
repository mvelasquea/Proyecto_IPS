# Sistema de Análisis de Combustible

Sistema para detección de anomalías y fraudes en el consumo de combustible de vehículos.

## 🚀 Características

- **Análisis automático** de archivos Excel con datos de combustible
- **Detección de anomalías** usando algoritmos de machine learning
- **Interfaz web** intuitiva y responsive
- **Reportes PDF** personalizables
- **API REST** completa con FastAPI

## 🛠️ Tecnologías

- **Backend**: Python, FastAPI, Pandas, Scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript ES6
- **Machine Learning**: Isolation Forest, DBSCAN, análisis estadístico
- **Reportes**: FPDF2

## 📋 Requisitos

- Python 3.8+
- Navegador web moderno
- Archivos Excel con datos de combustible

## 🔧 Instalación

1. **Clonar el repositorio**

   ```bash
   git clone <url-del-repositorio>
   cd Proyecto_IPS_fraude_combstible
   ```

2. **Instalar dependencias**

   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

3. **Iniciar el servidor**

   ```bash
   uvicorn server:app --reload
   ```

4. **Abrir el frontend**
   - Abrir `frontend/index.html` en el navegador
   - O usar un servidor local: `python -m http.server 3000`

## 📊 Formato de datos

El archivo Excel debe contener las siguientes columnas:

| Columna                        | Descripción                      | Ejemplo    |
| ------------------------------ | -------------------------------- | ---------- |
| `fecha` o `FECHA_INGRESO_VALE` | Fecha del repostaje              | 2024-01-15 |
| `placa` o `NOMBRE_PLACA`       | Placa del vehículo               | ABC-123    |
| `galones` o `GALONES`          | Cantidad de combustible          | 15.5       |
| `kilometraje` o `KILOMETRAJE`  | Kilometraje (opcional)           | 50000      |
| `costo` o `COSTO_TOTAL`        | Costo del combustible (opcional) | 45.50      |

## 🔍 Tipos de anomalías detectadas

1. **Consumo excesivo**: Valores atípicos en galones
2. **Frecuencia alta**: Repostajes muy frecuentes
3. **Rendimiento anormal**: Km/galón fuera del rango normal
4. **Patrones ML**: Anomalías detectadas por Isolation Forest

## 📈 API Endpoints

- `POST /analizar/` - Analizar archivo Excel
- `POST /generar-reporte/` - Generar reporte PDF
- `GET /health` - Estado de la API
- `GET /` - Información de la API

## 🚀 Uso rápido

1. Ejecutar `start.bat` (Windows) o iniciar manualmente
2. Abrir http://localhost:8000 para verificar la API
3. Cargar archivo Excel en la interfaz web
4. Revisar anomalías detectadas
5. Generar reporte si es necesario

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT.

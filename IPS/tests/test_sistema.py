"""
Pruebas unitarias para el sistema de análisis de combustible
"""
import unittest
import pandas as pd
import numpy as np
import os
import tempfile
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from backend.analisis_combustible import procesar_datos, aplicar_filtros, detectar_anomalias
    from backend.utils import validar_archivo_excel, calcular_metricas_basicas, detectar_outliers_iqr
    IMPORTS_OK = True
except ImportError as e:
    print(f"Advertencia: No se pudieron importar algunos módulos: {e}")
    IMPORTS_OK = False

class TestAnalisisCombustible(unittest.TestCase):
    """Pruebas para el módulo de análisis de combustible"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        if not IMPORTS_OK:
            self.skipTest("Módulos requeridos no disponibles")
            
        # Crear datos de prueba
        self.df_test = pd.DataFrame({
            'FECHA_INGRESO_VALE': pd.date_range('2023-01-01', periods=100, freq='D'),
            'UNIDAD_ORGANICA': ['GERENCIA_A'] * 50 + ['GERENCIA_B'] * 50,
            'CANTIDAD_GALONES': np.random.normal(20, 5, 100),
            'KM_RECORRIDO': np.random.normal(200, 50, 100),
            'TOTAL_CONSUMO': np.random.normal(100, 20, 100),
            'PRECIO': np.random.normal(5, 1, 100),
            'PLACA': [f'ABC-{i:03d}' for i in range(100)]
        })
        
        # Asegurar valores positivos
        self.df_test['CANTIDAD_GALONES'] = self.df_test['CANTIDAD_GALONES'].abs()
        self.df_test['KM_RECORRIDO'] = self.df_test['KM_RECORRIDO'].abs()
        self.df_test['TOTAL_CONSUMO'] = self.df_test['TOTAL_CONSUMO'].abs()
        self.df_test['PRECIO'] = self.df_test['PRECIO'].abs()
        
        # Añadir mes
        self.df_test['MES'] = self.df_test['FECHA_INGRESO_VALE'].dt.month
    
    def test_procesar_datos(self):
        """Probar la función de procesamiento de datos"""
        df_procesado = procesar_datos(self.df_test.copy())
        
        # Verificar que se procesó correctamente
        self.assertIsNotNone(df_procesado)
        self.assertFalse(df_procesado.empty)
        
        # Verificar que se crearon las columnas calculadas
        self.assertIn('EFICIENCIA', df_procesado.columns)
        self.assertIn('COSTO_POR_KM', df_procesado.columns)
        self.assertIn('DIA_SEMANA', df_procesado.columns)
        
        # Verificar que la eficiencia es razonable
        eficiencia_valida = df_procesado['EFICIENCIA'].between(1, 50)
        self.assertTrue(eficiencia_valida.any())
    
    def test_aplicar_filtros(self):
        """Probar la función de aplicación de filtros"""
        df_procesado = procesar_datos(self.df_test.copy())
        
        # Aplicar filtros
        df_filtrado = aplicar_filtros(df_procesado, 1, 'GERENCIA_A')
        
        # Verificar que el filtro funcionó
        self.assertFalse(df_filtrado.empty)
        self.assertTrue(all(df_filtrado['MES'] == 1))
        self.assertTrue(all(df_filtrado['UNIDAD_ORGANICA'] == 'GERENCIA_A'))
    
    def test_detectar_anomalias(self):
        """Probar la función de detección de anomalías"""
        df_procesado = procesar_datos(self.df_test.copy())
        
        # Añadir algunos valores anómalos
        df_procesado.loc[0, 'CANTIDAD_GALONES'] = 1000  # Valor muy alto
        df_procesado.loc[1, 'EFICIENCIA'] = 0.5  # Eficiencia muy baja
        
        df_anomalias = detectar_anomalias(df_procesado)
        
        # Verificar que se detectaron anomalías
        self.assertIn('ANOMALIA', df_anomalias.columns)
        self.assertIn('SCORE_ANOMALIA', df_anomalias.columns)
        self.assertIn('NIVEL_RIESGO', df_anomalias.columns)
        
        # Verificar que se detectó al menos una anomalía
        self.assertTrue(df_anomalias['ANOMALIA'].sum() > 0)
    
    def test_datos_vacios(self):
        """Probar comportamiento con datos vacíos"""
        df_vacio = pd.DataFrame()
        
        # Verificar que las funciones manejan datos vacíos
        resultado = procesar_datos(df_vacio)
        self.assertIsNone(resultado)
        
        df_filtrado = aplicar_filtros(df_vacio, 1, 'TEST')
        self.assertTrue(df_filtrado.empty)
    
    def test_columnas_faltantes(self):
        """Probar comportamiento con columnas faltantes"""
        df_incompleto = pd.DataFrame({
            'FECHA_INGRESO_VALE': pd.date_range('2023-01-01', periods=10),
            'CANTIDAD_GALONES': [10] * 10
        })
        
        df_procesado = procesar_datos(df_incompleto)
        self.assertIsNotNone(df_procesado)

class TestUtils(unittest.TestCase):
    """Pruebas para el módulo de utilidades"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.df_test = pd.DataFrame({
            'numeros': [1, 2, 3, 4, 100],  # 100 es outlier
            'textos': ['a', 'b', 'c', 'd', 'e'],
            'fechas': pd.date_range('2023-01-01', periods=5)
        })
    
    def test_calcular_metricas_basicas(self):
        """Probar cálculo de métricas básicas"""
        metricas = calcular_metricas_basicas(self.df_test)
        
        self.assertEqual(metricas['total_registros'], 5)
        self.assertEqual(metricas['columnas_numericas'], 1)
        self.assertEqual(metricas['columnas_texto'], 1)
        self.assertEqual(metricas['columnas_fecha'], 1)
    
    def test_detectar_outliers_iqr(self):
        """Probar detección de outliers"""
        outliers = detectar_outliers_iqr(self.df_test['numeros'])
        
        # El valor 100 debería ser detectado como outlier
        self.assertTrue(outliers.any())
        self.assertEqual(outliers.sum(), 1)
    
    def test_validar_archivo_excel(self):
        """Probar validación de archivos Excel"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.df_test.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            # Validar archivo
            resultado = validar_archivo_excel(tmp_path)
            self.assertTrue(resultado['valid'])
            
            # Probar con archivo inexistente
            resultado_inexistente = validar_archivo_excel('archivo_inexistente.xlsx')
            self.assertFalse(resultado_inexistente['valid'])
            
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_path)

class TestIntegracion(unittest.TestCase):
    """Pruebas de integración del sistema completo"""
    
    def test_flujo_completo(self):
        """Probar el flujo completo del análisis"""
        # Crear datos de prueba
        df_original = pd.DataFrame({
            'FECHA_INGRESO_VALE': pd.date_range('2023-01-01', periods=50, freq='D'),
            'UNIDAD_ORGANICA': ['GERENCIA_TEST'] * 50,
            'CANTIDAD_GALONES': np.random.normal(20, 5, 50),
            'KM_RECORRIDO': np.random.normal(200, 50, 50),
            'TOTAL_CONSUMO': np.random.normal(100, 20, 50),
            'PRECIO': np.random.normal(5, 1, 50),
            'PLACA': [f'TEST-{i:03d}' for i in range(50)]
        })
        
        # Asegurar valores positivos
        for col in ['CANTIDAD_GALONES', 'KM_RECORRIDO', 'TOTAL_CONSUMO', 'PRECIO']:
            df_original[col] = df_original[col].abs()
        
        # Añadir mes
        df_original['MES'] = df_original['FECHA_INGRESO_VALE'].dt.month
        
        # Ejecutar flujo completo
        try:
            # 1. Procesar datos
            df_procesado = procesar_datos(df_original.copy())
            self.assertIsNotNone(df_procesado)
            
            # 2. Aplicar filtros
            df_filtrado = aplicar_filtros(df_procesado, 1, 'GERENCIA_TEST')
            self.assertFalse(df_filtrado.empty)
            
            # 3. Detectar anomalías
            df_anomalias = detectar_anomalias(df_filtrado)
            self.assertIn('ANOMALIA', df_anomalias.columns)
            
            # 4. Verificar estadísticas
            total_registros = len(df_filtrado)
            total_anomalias = df_anomalias['ANOMALIA'].sum()
            
            self.assertGreaterEqual(total_registros, 1)
            self.assertGreaterEqual(total_anomalias, 0)
            
        except Exception as e:
            self.fail(f"El flujo completo falló: {str(e)}")

def ejecutar_pruebas():
    """Ejecutar todas las pruebas"""
    print("=== INICIANDO PRUEBAS DEL SISTEMA ===\n")
    
    if not IMPORTS_OK:
        print("❌ Error: No se pudieron importar los módulos necesarios")
        print("   Asegúrate de que el proyecto esté configurado correctamente")
        return False
    
    # Configurar suite de pruebas
    suite = unittest.TestSuite()
    
    # Añadir pruebas
    suite.addTest(unittest.makeSuite(TestAnalisisCombustible))
    suite.addTest(unittest.makeSuite(TestUtils))
    suite.addTest(unittest.makeSuite(TestIntegracion))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n=== RESUMEN DE PRUEBAS ===")
    print(f"Pruebas ejecutadas: {resultado.testsRun}")
    print(f"Errores: {len(resultado.errors)}")
    print(f"Fallos: {len(resultado.failures)}")
    print(f"Éxito: {resultado.wasSuccessful()}")
    
    return resultado.wasSuccessful()

if __name__ == '__main__':
    ejecutar_pruebas()

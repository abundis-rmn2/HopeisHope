# DeepSeek (DS)

Esta carpeta contiene scripts diseñados para procesar y analizar descripciones de tatuajes utilizando la API de DeepSeek y otras herramientas. Los scripts están orientados a categorizar tatuajes, extraer información clave y generar resultados procesados que pueden ser utilizados en análisis posteriores.

---

## Propósito General

El propósito principal de esta carpeta es automatizar el análisis de descripciones de tatuajes provenientes de diferentes conjuntos de datos. Esto incluye:
- La categorización de tatuajes basada en descripciones textuales.
- La extracción de información clave como ubicación, texto extraído, categorías y palabras clave.
- La generación de resultados estructurados en formato CSV para facilitar su integración con otros procesos.

---

## Archivos y Funciones

### `shared.py`
- **Funciones clave:**
  - Proporciona funciones compartidas para interactuar con la API de DeepSeek y manejar respuestas.
- **Procesos:**
  - Genera prompts para la API de DeepSeek y procesa las respuestas.
  - Limpia las respuestas para extraer arreglos JSON válidos.
  - Guarda resultados procesados en archivos CSV.
- **Fuente de datos:** Ninguno directamente.
- **Exporta:** Archivos CSV en el directorio `csv/equi`.

### `cat_tattoo_REPD.py`
- **Funciones clave:**
  - Procesa descripciones de tatuajes del conjunto REPD utilizando la API de DeepSeek.
- **Procesos:**
  - Carga descripciones de tatuajes desde un archivo CSV.
  - Genera prompts para categorizar tatuajes y extraer información clave.
  - Exporta los resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`repd_vp_cedulas_senas.csv`).
- **Exporta:** Archivo CSV (`llm_tatuajes_procesados_REPD.csv`).

### `cat_tattoo_PFSI.py`
- **Funciones clave:**
  - Procesa descripciones de tatuajes del conjunto PFSI utilizando la API de DeepSeek.
- **Procesos:**
  - Carga descripciones de tatuajes desde un archivo CSV.
  - Genera prompts para categorizar tatuajes y extraer información clave.
  - Exporta los resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`pfsi_v2_principal.csv`).
- **Exporta:** Archivo CSV (`llm_tatuajes_procesados_PFSI.csv`).

---

## Fuentes de Datos

- **Archivos CSV:** Utilizados como entrada para procesar descripciones de tatuajes y exportar resultados procesados.
- **API de DeepSeek:** Utilizada para analizar y categorizar descripciones de tatuajes.

---

## Formatos de Exportación

- **CSV:** Exportado por los scripts para almacenar resultados procesados de tatuajes.

---

## Ejemplo de Uso

### Procesar Tatuajes del Conjunto REPD
1. Asegúrate de que el archivo `repd_vp_cedulas_senas.csv` esté ubicado en el directorio `csv/equi`.
2. Configura la clave de la API de DeepSeek en un archivo `.env` con la variable `DEEPSEEK_API_KEY`.
3. Ejecuta el script `cat_tattoo_REPD.py`:
   ```bash
   python cat_tattoo_REPD.py
   ```
4. Los resultados procesados se guardarán en el archivo `llm_tatuajes_procesados_REPD.csv`.

### Procesar Tatuajes del Conjunto PFSI
1. Asegúrate de que el archivo `pfsi_v2_principal.csv` esté ubicado en el directorio `csv/equi`.
2. Configura la clave de la API de DeepSeek en un archivo `.env` con la variable `DEEPSEEK_API_KEY`.
3. Ejecuta el script `cat_tattoo_PFSI.py`:
   ```bash
   python cat_tattoo_PFSI.py
   ```
4. Los resultados procesados se guardarán en el archivo `llm_tatuajes_procesados_PFSI.csv`.

---

## Requisitos Previos

1. **Python 3.8+**: Asegúrate de tener una versión compatible de Python instalada.
2. **Dependencias**: Instala las dependencias necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuración del Entorno**:
   - Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura:
     ```
     DEEPSEEK_API_KEY=tu_clave_deepseek
     ```

---

## Notas Adicionales

- Los scripts están diseñados para manejar grandes volúmenes de datos, pero es importante verificar que los archivos CSV de entrada estén correctamente formateados.
- Si encuentras errores relacionados con la API de DeepSeek, asegúrate de que tu clave de API sea válida y que tengas acceso a la red.

---

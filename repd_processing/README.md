# REPD Processing

Esta carpeta contiene scripts y herramientas diseñadas para procesar y analizar los datos del Registro Estatal de Personas Desaparecidas (REPD). A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `EntityRuler_SQL_Fetch.py`
- **Funciones clave:**
  - Configura un modelo SpaCy con patrones personalizados para identificar entidades como fechas, horas, direcciones y colonias.
  - Se conecta a una base de datos MySQL para extraer datos de descripciones de desapariciones.
  - Procesa las descripciones para extraer información relevante como calles y colonias.
- **Procesos:**
  - Carga patrones personalizados en SpaCy mediante `EntityRuler`.
  - Extrae datos de la tabla `repd_vp_cedulas_principal` en la base de datos.
  - Procesa las descripciones con el modelo SpaCy para identificar entidades clave.
- **Fuente de datos:** Base de datos SQL (`repd_vp_cedulas_principal`).
- **Exporta:** Ningún archivo directamente.

### `fetch.py`
- **Funciones clave:**
  - Interactúa con una API externa para obtener datos de búsqueda de personas desaparecidas.
  - Itera a través de todas las páginas de la API para recuperar registros completos.
- **Procesos:**
  - Realiza solicitudes HTTP a la API.
  - Recupera datos en formato JSON y los almacena en memoria.
- **Fuente de datos:** API externa (`https://repd.jalisco.gob.mx/api/v1/...`).
- **Exporta:** Ningún archivo directamente.

### `metadata_violence_to_csv.py`
- **Funciones clave:**
  - Detecta palabras clave relacionadas con violencia en descripciones de desapariciones.
  - Clasifica casos violentos y calcula puntajes de violencia.
  - Exporta los resultados a un archivo CSV.
- **Procesos:**
  - Preprocesa texto eliminando palabras vacías y aplicando tokenización.
  - Detecta términos violentos utilizando coincidencias de prefijos.
  - Entrena un modelo de aprendizaje automático para clasificar casos violentos.
- **Fuente de datos:** Archivo CSV (`sisovid.csv`).
- **Exporta:** Archivo CSV (`filtered_cases_with_violence_terms.csv`).

### `ner_location_sql.py`
- **Funciones clave:**
  - Procesa descripciones de desapariciones para identificar ubicaciones utilizando el modelo SpaCy.
  - Extrae entidades relacionadas con ubicaciones como calles y colonias.
- **Procesos:**
  - Carga descripciones desde la base de datos.
  - Utiliza SpaCy para identificar entidades de ubicación.
- **Fuente de datos:** Base de datos SQL (`repd_vp_cedulas_principal`).
- **Exporta:** Ningún archivo directamente.

### `repd_marker_location_sql.py`
- **Funciones clave:**
  - Genera un mapa interactivo con marcadores basados en ubicaciones extraídas de descripciones.
  - Utiliza Google Maps API para geocodificar ubicaciones.
- **Procesos:**
  - Extrae datos de la base de datos.
  - Geocodifica ubicaciones y las visualiza en un mapa interactivo.
- **Fuente de datos:** Base de datos SQL (`repd_vp_cedulas_principal`).
- **Exporta:** Archivo HTML (`map.html`).

### `repd_heatmap_located_sql.py`
- **Funciones clave:**
  - Crea un mapa de calor interactivo que muestra la distribución de ubicaciones relacionadas con desapariciones.
  - Clasifica los puntos según el estado de localización (e.g., "Con Vida", "Sin Vida").
- **Procesos:**
  - Extrae datos de la base de datos.
  - Geocodifica ubicaciones y las agrupa en un mapa de calor.
- **Fuente de datos:** Base de datos SQL (`repd_vp_cedulas_principal`).
- **Exporta:** Archivo HTML (`heat_map.html`).

### `repd_ner_spacy.py`
- **Funciones clave:**
  - Procesa descripciones de desapariciones utilizando SpaCy para extraer entidades como fechas, horas, direcciones y colonias.
  - Visualiza las entidades extraídas.
- **Procesos:**
  - Carga descripciones desde un conjunto de datos en memoria.
  - Aplica patrones personalizados de SpaCy para identificar entidades clave.
- **Fuente de datos:** Datos en memoria (ejemplo en código).
- **Exporta:** Ningún archivo directamente.

### `repd_ner_to_sql.py`
- **Funciones clave:**
  - Extrae entidades de descripciones de desapariciones, como ubicaciones y fechas, utilizando SpaCy.
  - Geocodifica ubicaciones y guarda los resultados en una base de datos MySQL.
  - Registra frecuencias de palabras y términos relacionados.
- **Procesos:**
  - Extrae datos de la base de datos.
  - Procesa descripciones con SpaCy para identificar entidades clave.
  - Geocodifica ubicaciones y actualiza la base de datos.
- **Fuente de datos:** Base de datos SQL (`repd_vp_cedulas_principal`).
- **Exporta:** Base de datos SQL (`repd_vp_inferencias`).

### `violence_csv_to_sql.py`
- **Funciones clave:**
  - Carga un archivo CSV con datos procesados sobre violencia.
  - Actualiza una base de datos MySQL con puntajes de violencia y términos detectados.
- **Procesos:**
  - Verifica y actualiza la estructura de la tabla en la base de datos.
  - Itera a través de los registros del CSV y actualiza los datos en la base de datos.
- **Fuente de datos:** Archivo CSV (`filtered_cases_with_violence_terms.csv`).
- **Exporta:** Base de datos SQL (`repd_vp_inferencia3`).

---

## Archivos Obligatorios

1. **`db_credentials.json`:** Archivo de configuración con las credenciales de la base de datos y la clave de la API de Google Maps.
2. **`sisovid.csv`:** Archivo CSV con datos iniciales de desapariciones (utilizado por `metadata_violence_to_csv.py`).
3. **`filtered_cases_with_violence_terms.csv`:** Archivo CSV generado por `metadata_violence_to_csv.py` y utilizado por `violence_csv_to_sql.py`.

---

## Fuentes de Datos

- **Base de datos SQL:** Utilizada por la mayoría de los scripts para extraer y actualizar datos.
- **Archivos CSV:** Utilizados para procesar y exportar datos relacionados con violencia.
- **API externa:** Utilizada por `fetch.py` para obtener datos de búsqueda de personas desaparecidas.

---

## Formatos de Exportación

- **CSV:** Exportado por `metadata_violence_to_csv.py` para almacenar casos filtrados con términos de violencia.
- **HTML:** Exportado por `repd_marker_location_sql.py` y `repd_heatmap_located_sql.py` para mapas interactivos.
- **Base de datos SQL:** Actualizada por `repd_ner_to_sql.py` y `violence_csv_to_sql.py` para almacenar inferencias y datos procesados.

---


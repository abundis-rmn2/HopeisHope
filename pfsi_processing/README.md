# PFSI Processing

Esta carpeta contiene scripts y herramientas diseñadas para procesar y analizar datos relacionados con el procesamiento de información del PFSI (Personas Fallecidas Sin Identificar). A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `location_map.py`
- **Funciones clave:**
  - Genera un mapa interactivo con marcadores basados en ubicaciones extraídas de datos del PFSI.
  - Utiliza Google Maps API para geocodificar ubicaciones.
- **Procesos:**
  - Recupera datos de un formulario web mediante solicitudes HTTP.
  - Geocodifica ubicaciones y las visualiza en un mapa interactivo.
- **Fuente de datos:** Formulario web (`http://consultas.cienciasforenses.jalisco.gob.mx/buscarpfsi_v2.php`).
- **Exporta:** Archivo HTML (`delegaciones_map_<rango_fechas>.html`).

### `pfsi_location_geo.py`
- **Funciones clave:**
  - Genera un mapa interactivo con marcadores basados en ubicaciones extraídas de una base de datos MySQL.
  - Utiliza Google Maps API para geocodificar ubicaciones.
- **Procesos:**
  - Recupera datos de la tabla `pfsi_v2_principal` en la base de datos.
  - Geocodifica ubicaciones y las visualiza en un mapa interactivo.
- **Fuente de datos:** Base de datos SQL (`pfsi_v2_principal`).
- **Exporta:** Archivo HTML (`sql_delegaciones_map_<rango_fechas>.html`).

### `pfsi_make_stoplist_senas.py`
- **Funciones clave:**
  - Procesa descripciones de señas particulares para identificar palabras clave y categorías.
  - Genera listas de palabras y categorías basadas en las descripciones.
- **Procesos:**
  - Filtra datos de señas particulares desde un archivo CSV.
  - Crea un "bag of words" y clasifica las descripciones en categorías predefinidas.
- **Fuente de datos:** Archivo CSV (`pfsi_v2_principal.csv`).
- **Exporta:** Archivos de texto (`word_counts_senas.txt`, `word_categories_senas.txt`, `cat_senas.txt`).

### `pfsi_make_stoplist_tattoos.py`
- **Funciones clave:**
  - Procesa descripciones de tatuajes para identificar palabras clave y categorías.
  - Genera listas de palabras y categorías basadas en las descripciones.
- **Procesos:**
  - Filtra datos de tatuajes desde un archivo CSV.
  - Crea un "bag of words" y clasifica las descripciones en categorías predefinidas.
- **Fuente de datos:** Archivo CSV (`pfsi_v2_principal.csv`).
- **Exporta:** Archivos de texto (`word_counts.txt`, `word_categories.txt`, `cat_tattoos.txt`).

### `weekly_distribution.py`
- **Funciones clave:**
  - Analiza la distribución semanal de desapariciones y genera visualizaciones interactivas.
  - Identifica y agrupa ubicaciones en clústeres utilizando el algoritmo DBSCAN.
- **Procesos:**
  - Recupera datos de una API externa.
  - Calcula clústeres geográficos y genera gráficos de barras, gráficos de pastel y mapas interactivos.
- **Fuente de datos:** API externa (`https://datades.abundis.com.mx/api/specificDate.php`).
- **Exporta:** Archivo HTML (`weekly_cluster_distribution.html`).

---

## Archivos Obligatorios

1. **`db_credentials.json`:** Archivo de configuración con las credenciales de la base de datos y la clave de la API de Google Maps.
2. **`pfsi_v2_principal.csv`:** Archivo CSV con datos iniciales del PFSI (utilizado por `pfsi_make_stoplist_senas.py` y `pfsi_make_stoplist_tattoos.py`).

---

## Fuentes de Datos

- **Formulario web:** Utilizado por `location_map.py` para extraer datos de ubicaciones.
- **Base de datos SQL:** Utilizada por `pfsi_location_geo.py` para extraer datos de ubicaciones.
- **Archivos CSV:** Utilizados para procesar y exportar datos relacionados con señas particulares y tatuajes.
- **API externa:** Utilizada por `weekly_distribution.py` para obtener datos de desapariciones.

---

## Formatos de Exportación

- **HTML:** Exportado por `location_map.py`, `pfsi_location_geo.py` y `weekly_distribution.py` para mapas interactivos y visualizaciones.
- **TXT:** Exportado por `pfsi_make_stoplist_senas.py` y `pfsi_make_stoplist_tattoos.py` para almacenar listas de palabras y categorías.

---
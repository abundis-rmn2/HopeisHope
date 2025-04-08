# Utils

Esta carpeta contiene scripts auxiliares diseñados para realizar diversas tareas relacionadas con la manipulación de datos, conexión a bases de datos y procesamiento de información geográfica. A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `sql_to_csv.py`
- **Funciones clave:**
  - Conecta a una base de datos MySQL para extraer datos de una tabla específica.
  - Exporta los datos extraídos a un archivo CSV.
- **Procesos:**
  - Carga las credenciales de la base de datos desde un archivo JSON.
  - Ejecuta una consulta SQL para recuperar todos los registros de la tabla.
  - Convierte los resultados en un DataFrame de pandas y los guarda como CSV.
- **Fuente de datos:** Base de datos SQL.
- **Exporta:** Archivo CSV (`./csv/equi/{table}.csv`).

### `sql_check.py`
- **Funciones clave:**
  - Verifica la conexión a una base de datos MySQL.
  - Cierra la conexión de manera segura.
- **Procesos:**
  - Carga las credenciales de la base de datos desde un archivo JSON.
  - Intenta establecer una conexión con la base de datos.
  - Imprime el estado de la conexión y la cierra.
- **Fuente de datos:** Archivo JSON (`db_credentials.json`).
- **Exporta:** Ningún archivo directamente.

### `add_latlng_fosas.py`
- **Funciones clave:**
  - Geocodifica ubicaciones en México utilizando la API de OpenCage.
  - Agrega columnas de latitud y longitud a un archivo CSV existente.
- **Procesos:**
  - Lee un archivo CSV con datos de municipios y estados.
  - Utiliza la API de OpenCage para obtener coordenadas geográficas.
  - Agrega las coordenadas al DataFrame y guarda los resultados en un nuevo archivo CSV.
- **Fuente de datos:** Archivo CSV (`./csv/estatal_limpio.csv`).
- **Exporta:** Archivo CSV (`./csv/estatal_limpio_with_lat_lng.csv`).

---

## Archivos Obligatorios

1. **`db_credentials.json`:** Archivo de configuración con las credenciales de la base de datos.
2. **`estatal_limpio.csv`:** Archivo CSV con datos iniciales de municipios y estados (utilizado por `add_latlng_fosas.py`).

---

## Fuentes de Datos

- **Base de datos SQL:** Utilizada por `sql_to_csv.py` y `sql_check.py` para extraer y verificar datos.
- **Archivos CSV:** Utilizados por `add_latlng_fosas.py` para procesar y exportar datos geográficos.
- **API externa:** Utilizada por `add_latlng_fosas.py` para geocodificar ubicaciones.

---

## Formatos de Exportación

- **CSV:** Exportado por `sql_to_csv.py` y `add_latlng_fosas.py` para almacenar datos procesados.

---

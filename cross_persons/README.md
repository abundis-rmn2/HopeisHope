# Cross Persons

Esta carpeta contiene scripts diseñados para procesar y analizar coincidencias entre personas desaparecidas y cuerpos no identificados. A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `crossPersons.py`
- **Funciones clave:**
  - Encuentra coincidencias potenciales entre personas desaparecidas y cuerpos no identificados.
- **Procesos:**
  - Carga datos de personas desaparecidas y cuerpos no identificados desde archivos CSV.
  - Filtra registros basados en criterios como fecha de desaparición, sexo, edad y ubicación.
  - Calcula similitudes entre nombres y evalúa coincidencias basadas en un puntaje.
  - Exporta los resultados a un archivo CSV.
- **Fuente de datos:** Archivos CSV (`repd_vp_cedulas_principal.csv`, `pfsi_v2_principal.csv`).
- **Exporta:** Archivo CSV (`person_matches_name_age.csv`).

### `load_all.py`
- **Funciones clave:**
  - Carga múltiples archivos CSV relacionados con personas desaparecidas y sus características.
- **Procesos:**
  - Verifica la existencia de los archivos necesarios en el directorio especificado.
  - Carga los datos en memoria como DataFrames de pandas para su posterior procesamiento.
- **Fuente de datos:** Archivos CSV (`pfsi_v2_principal.csv`, `repd_vp_cedulas_principal.csv`, `repd_vp_cedulas_senas.csv`, `repd_vp_cedulas_vestimenta.csv`).
- **Exporta:** Ningún archivo directamente.

---

## Fuentes de Datos

- **Archivos CSV:** Utilizados como entrada para procesar coincidencias entre personas desaparecidas y cuerpos no identificados.

---

## Formatos de Exportación

- **CSV:** Exportado por `crossPersons.py` para almacenar coincidencias potenciales entre personas desaparecidas y cuerpos no identificados.

---

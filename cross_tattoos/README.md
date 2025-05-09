# Cross Tattoos

Esta carpeta contiene scripts diseñados para procesar y analizar coincidencias de tatuajes entre diferentes conjuntos de datos. A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `cat_tattoo_PFSI.py`
- **Funciones clave:**
  - Procesa descripciones de tatuajes del conjunto de datos PFSI.
  - Categoriza tatuajes por palabras clave y extrae ubicaciones.
- **Procesos:**
  - Carga datos desde un archivo CSV.
  - Divide descripciones en tatuajes individuales.
  - Exporta resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`pfsi_v2_principal.csv`).
- **Exporta:** Archivo CSV (`tatuajes_procesados_PFSI.csv`).

### `cat_tattoo_RPED.py`
- **Funciones clave:**
  - Procesa descripciones de tatuajes del conjunto de datos REPD.
  - Categoriza tatuajes por palabras clave y extrae ubicaciones.
- **Procesos:**
  - Carga datos desde un archivo CSV.
  - Divide descripciones en tatuajes individuales.
  - Exporta resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`repd_vp_cedulas_senas.csv`).
- **Exporta:** Archivo CSV (`tatuajes_procesados_REPD.csv`).

### `compare_tattoos.py`
- **Funciones clave:**
  - Compara ubicaciones de tatuajes entre los conjuntos PFSI y REPD.
- **Procesos:**
  - Carga datos procesados de tatuajes y coincidencias de personas.
  - Identifica coincidencias basadas en ubicaciones.
- **Fuente de datos:** Archivos CSV (`llm_tatuajes_procesados_PFSI.csv`, `llm_tatuajes_procesados_REPD.csv`, `person_matches_name_age.csv`).
- **Exporta:** Ningún archivo directamente.

### `cross_llm_tattoo.py`
- **Funciones clave:**
  - Encuentra relaciones entre tatuajes utilizando similitud de texto y categorías.
- **Procesos:**
  - Calcula similitudes entre descripciones de tatuajes.
  - Identifica coincidencias basadas en ubicaciones, categorías y descripciones.
- **Fuente de datos:** Archivos CSV (`llm_tatuajes_procesados_PFSI.csv`, `llm_tatuajes_procesados_REPD.csv`).
- **Exporta:** Archivo CSV (`tattoo_relationships.csv`).

### `cross_tattoo_location_design_llm.py`
- **Funciones clave:**
  - Compara tatuajes basándose en ubicaciones y diseños.
- **Procesos:**
  - Calcula similitudes utilizando TF-IDF.
  - Identifica coincidencias entre tatuajes de personas desaparecidas y cuerpos no identificados.
- **Fuente de datos:** Archivos CSV (`llm_tatuajes_procesados_PFSI.csv`, `llm_tatuajes_procesados_REPD.csv`, `person_matches_name_age.csv`).
- **Exporta:** Archivo CSV (`tattoo_matches_location_design_llm.csv`).

### `cross_tattoo_prevlist.py`
- **Funciones clave:**
  - Calcula similitudes entre tatuajes utilizando múltiples características.
- **Procesos:**
  - Filtra datos basados en coincidencias probables.
  - Calcula similitudes entre descripciones, ubicaciones y palabras clave.
- **Fuente de datos:** Archivos CSV (`tatuajes_procesados_PFSI.csv`, `tatuajes_procesados_REPD.csv`, `person_matches_name_age.csv`).
- **Exporta:** Archivo CSV (`tattoo_matches_all.csv`).

### `cross_tattoo_prevlist_strict.py`
- **Funciones clave:**
  - Calcula similitudes estrictas entre tatuajes para pares específicos de personas.
- **Procesos:**
  - Compara tatuajes solo para pares definidos en un archivo de coincidencias.
  - Calcula similitudes entre descripciones, ubicaciones y palabras clave.
- **Fuente de datos:** Archivos CSV (`tatuajes_procesados_PFSI.csv`, `tatuajes_procesados_REPD.csv`, `person_matches_name_age.csv`).
- **Exporta:** Archivo CSV (`tattoo_matches_strict.csv`).

### `crossTattoo.py`
- **Funciones clave:**
  - Calcula similitudes entre tatuajes utilizando características combinadas.
- **Procesos:**
  - Compara descripciones, ubicaciones y palabras clave.
  - Identifica coincidencias entre tatuajes de diferentes conjuntos de datos.
- **Fuente de datos:** Archivos CSV (`tatuajes_procesados_PFSI.csv`, `tatuajes_procesados_REPD.csv`).
- **Exporta:** Archivo CSV (`tattoo_matches.csv`).

### `crossTattooDS.py`
- **Funciones clave:**
  - Encuentra coincidencias entre tatuajes utilizando similitudes de ubicaciones, categorías y palabras clave.
- **Procesos:**
  - Normaliza texto y calcula similitudes.
  - Identifica coincidencias basadas en un puntaje de similitud.
- **Fuente de datos:** Archivos CSV (`tatuajes_procesados_PFSI.csv`, `tatuajes_procesados_REPD.csv`).
- **Exporta:** Archivo CSV (`tattoo_matches_ds.csv`).

### `deepseek_cat_tattoo_PFSI.py`
- **Funciones clave:**
  - Utiliza la API de DeepSeek para categorizar tatuajes del conjunto PFSI.
- **Procesos:**
  - Genera descripciones detalladas de tatuajes utilizando un modelo de lenguaje.
  - Exporta resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`pfsi_v2_principal.csv`).
- **Exporta:** Archivo CSV (`llm_tatuajes_procesados_PFSI.csv`).

### `deepseek_cat_tattoo_REPD.py`
- **Funciones clave:**
  - Utiliza la API de DeepSeek para categorizar tatuajes del conjunto REPD.
- **Procesos:**
  - Genera descripciones detalladas de tatuajes utilizando un modelo de lenguaje.
  - Exporta resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`repd_vp_cedulas_senas.csv`).
- **Exporta:** Archivo CSV (`llm_tatuajes_procesados_REPD.csv`).

### `llm_prompts.py`
- **Funciones clave:**
  - Genera prompts para modelos de lenguaje para categorizar tatuajes.
- **Procesos:**
  - Define y ajusta prompts para mejorar la precisión de las respuestas.
- **Fuente de datos:** Ninguno.
- **Exporta:** Ningún archivo directamente.

### `llm_tattoo_RPED.py`
- **Funciones clave:**
  - Procesa tatuajes del conjunto REPD utilizando un modelo de lenguaje.
- **Procesos:**
  - Completa descripciones de tatuajes y categoriza palabras clave.
  - Exporta resultados procesados a un archivo CSV.
- **Fuente de datos:** Archivo CSV (`repd_vp_cedulas_senas.csv`).
- **Exporta:** Archivo CSV (`llm_tatuajes_procesados_REPD.csv`).

### `relationship_nodes.py`
- **Funciones clave:**
  - Filtra registros de tatuajes basados en coincidencias y organiza datos en conjuntos.
- **Procesos:**
  - Carga datos de coincidencias de tatuajes.
  - Filtra y guarda registros relevantes en nuevos archivos CSV.
- **Fuente de datos:** Archivos CSV (`tattoo_matches_all.csv`, `pfsi_v2_principal.csv`, `repd_vp_cedulas_principal.csv`).
- **Exporta:** Archivos CSV (`pfsi_tats.csv`, `repd_principal_tats.csv`, `repd_tats_inferencia.csv`).

### `tats_csv_to_graph.py`
- **Funciones clave:**
  - Crea un grafo a partir de coincidencias de tatuajes.
- **Procesos:**
  - Genera nodos y aristas basados en datos de coincidencias.
  - Exporta el grafo en formato GraphML.
- **Fuente de datos:** Archivo CSV (`tattoo_matches_strict.csv`).
- **Exporta:** Archivo GraphML (`tattoo_matches.graphml`).

---

## Fuentes de Datos

- **Archivos CSV:** Utilizados como entrada para procesar coincidencias de tatuajes y exportar resultados procesados.

---

## Formatos de Exportación

- **CSV:** Exportado por múltiples scripts para almacenar resultados procesados y coincidencias.
- **GraphML:** Exportado por `tats_csv_to_graph.py` para visualizar coincidencias en un grafo.

---

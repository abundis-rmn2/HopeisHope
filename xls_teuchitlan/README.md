# XLS Teuchitlán

Esta carpeta contiene scripts diseñados para procesar datos de archivos Excel relacionados con el proyecto Teuchitlán. A continuación, se describen los archivos principales, sus funciones clave, procesos, fuentes de datos y formatos de exportación.

---

## Archivos y Funciones

### `ods_teucitlan.py`
- **Funciones clave:**
  - Extrae hipervínculos de la columna G de un archivo Excel.
  - Procesa todos los datos del archivo Excel, incluyendo encabezados y columnas significativas.
  - Exporta los datos procesados y los hipervínculos a archivos CSV.
- **Procesos:**
  - Lee un archivo Excel (`teuchitlan.xlsx`) y extrae hipervínculos de la columna G.
  - Filtra columnas significativas basándose en datos no vacíos.
  - Genera un archivo CSV con todos los datos, incluyendo una columna de hipervínculos y un ID incremental.
  - Exporta un archivo CSV separado con los hipervínculos.
- **Fuente de datos:** Archivo Excel (`teuchitlan.xlsx`).
- **Exporta:**
  - Archivo CSV con datos completos (`complete_data3.csv`).
  - Archivo CSV con hipervínculos (`hyperlinks3.csv`).

### `download_images.py`
- **Funciones clave:**
  - Descarga imágenes desde enlaces proporcionados en un archivo CSV.
  - Extrae el ID de archivo de Google Drive desde URLs en las columnas `LINK FOTO` o `hyperlink`.
  - Guarda las imágenes descargadas en una carpeta local.
- **Procesos:**
  - Lee un archivo CSV (`complete_data3.csv`) generado por `ods_teucitlan.py`.
  - Extrae el ID de archivo de Google Drive desde las URLs.
  - Descarga las imágenes y las guarda con nombres basados en el ID de cada fila.
  - Maneja errores y omite descargas duplicadas.
- **Fuente de datos:** Archivo CSV (`complete_data3.csv`).
- **Exporta:** Imágenes descargadas en la carpeta `./img/indicios3`.

---

## Archivos Obligatorios

1. **`teuchitlan.xlsx`:** Archivo Excel con datos iniciales para procesar.
2. **`complete_data3.csv`:** Archivo CSV generado por `ods_teucitlan.py` que contiene datos procesados y enlaces.

---

## Fuentes de Datos

- **Archivo Excel:** Utilizado por `ods_teucitlan.py` para extraer datos y enlaces.
- **Archivo CSV:** Utilizado por `download_images.py` para descargar imágenes desde enlaces.

---

## Formatos de Exportación

- **CSV:** Exportado por `ods_teucitlan.py` para almacenar datos completos y enlaces.
- **Imágenes:** Exportadas por `download_images.py` y almacenadas en la carpeta `./img/indicios3`.

---

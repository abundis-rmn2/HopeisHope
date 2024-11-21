import requests
import mysql.connector
import time

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "your_database"
}

# Base URL of the API
BASE_URL = "https://repd.jalisco.gob.mx/api/v1/version_publica/repd-version-publica-cedulas-busqueda/"

def fetch_data(limit=120):
    """Fetch data from the API and return all results."""
    try:
        response = requests.get(f"{BASE_URL}?limit={limit}&page=1")
        response.raise_for_status()
        data = response.json()
        total_pages = data.get("total_pages", 1)

        all_results = []

        # Iterate through all pages
        for page in range(1, total_pages + 1):
            print(f"Fetching page {page}/{total_pages}...")
            response = requests.get(f"{BASE_URL}?limit={limit}&page={page}")
            response.raise_for_status()
            page_data = response.json()
            all_results.extend(page_data.get("results", []))
            time.sleep(0.1)

        return all_results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def insert_data_to_db(data):
    """Insert the API data into the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for record in data:
            # Insert into `repd_vp_cedulas_principal`
            principal_query = """
                INSERT INTO repd_vp_cedulas_principal (
                    id_cedula_busqueda, autorizacion_informacion_publica, condicion_localizacion,
                    nombre_completo, edad_momento_desaparicion, sexo, genero, complexion, estatura,
                    tez, cabello, ojos_color, municipio, estado, fecha_desaparicion,
                    estatus_persona_desaparecida, descripcion_desaparicion, ruta_foto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    autorizacion_informacion_publica=VALUES(autorizacion_informacion_publica),
                    condicion_localizacion=VALUES(condicion_localizacion),
                    nombre_completo=VALUES(nombre_completo),
                    edad_momento_desaparicion=VALUES(edad_momento_desaparicion),
                    sexo=VALUES(sexo), genero=VALUES(genero),
                    complexion=VALUES(complexion), estatura=VALUES(estatura),
                    tez=VALUES(tez), cabello=VALUES(cabello),
                    ojos_color=VALUES(ojos_color), municipio=VALUES(municipio),
                    estado=VALUES(estado), fecha_desaparicion=VALUES(fecha_desaparicion),
                    estatus_persona_desaparecida=VALUES(estatus_persona_desaparecida),
                    descripcion_desaparicion=VALUES(descripcion_desaparicion),
                    ruta_foto=VALUES(ruta_foto)
            """
            principal_values = (
                record["id_cedula_busqueda"],
                record["autorizacion_informacion_publica"],
                record["condicion_localizacion"],
                record["nombre_completo"],
                record["edad_momento_desaparicion"],
                record["sexo"],
                record["genero"],
                record["complexion"],
                record["estatura"],
                record["tez"],
                record["cabello"],
                record["ojos_color"],
                record["municipio"],
                record["estado"],
                record["fecha_desaparicion"],
                record["estatus_persona_desaparecida"],
                record["descripcion_desaparicion"],
                record["ruta_foto"]
            )
            cursor.execute(principal_query, principal_values)

            # Insert into `repd_vp_cedulas_senas`
            for sena in record.get("descripcion_sena_particular", []):
                sena_query = """
                    INSERT INTO repd_vp_cedulas_senas (
                        id, id_cedula_busqueda, especificacion_general, parte_cuerpo, tipo_sena, descripcion
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        especificacion_general=VALUES(especificacion_general),
                        parte_cuerpo=VALUES(parte_cuerpo),
                        tipo_sena=VALUES(tipo_sena),
                        descripcion=VALUES(descripcion)
                """
                sena_values = (
                    sena["id"],
                    sena["id_cedula_busqueda"],
                    sena["especificacion_general"],
                    sena["parte_cuerpo"],
                    sena["tipo_sena"],
                    sena["descripcion"]
                )
                cursor.execute(sena_query, sena_values)

            # Insert into `repd_vp_cedulas_vestimenta`
            for vestimenta in record.get("descripcion_vestimenta", []):
                vestimenta_query = """
                    INSERT INTO repd_vp_cedulas_vestimenta (
                        id, id_cedula_busqueda, clase_prenda, grupo_prenda, prenda, marca, color,
                        material, talla, tipo, descripcion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        clase_prenda=VALUES(clase_prenda),
                        grupo_prenda=VALUES(grupo_prenda),
                        prenda=VALUES(prenda),
                        marca=VALUES(marca),
                        color=VALUES(color),
                        material=VALUES(material),
                        talla=VALUES(talla),
                        tipo=VALUES(tipo),
                        descripcion=VALUES(descripcion)
                """
                vestimenta_values = (
                    vestimenta["id"],
                    vestimenta["id_cedula_busqueda"],
                    vestimenta["clase_prenda"],
                    vestimenta["grupo_prenda"],
                    vestimenta["prenda"],
                    vestimenta["marca"],
                    vestimenta["color"],
                    vestimenta["material"],
                    vestimenta["talla"],
                    vestimenta["tipo"],
                    vestimenta["descripcion"]
                )
                cursor.execute(vestimenta_query, vestimenta_values)

        # Commit changes
        conn.commit()
        print("Data successfully inserted into the database!")

    except mysql.connector.Error as e:
        print(f"Error inserting data into database: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    data = fetch_data()
    if data:
        insert_data_to_db(data)

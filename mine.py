import requests
import mysql.connector
import time
import json


# Load database configuration from config.json
def load_db_config():
    with open('db_credentials.json', 'r') as file:
        return json.load(file)


# Database configuration
DB_CONFIG = load_db_config()
# Base URL of the API
BASE_URL = "https://repd.jalisco.gob.mx/api/v1/version_publica/repd-version-publica-cedulas-busqueda/"


def fetch_data(limit=3, pause_time=1):
    """Fetch all data by checking count, total pages, and iterating through all pages."""
    try:
        # First, get the total count and total pages from the API
        initial_response = requests.get(f"{BASE_URL}?limit={limit}&page=1")
        initial_response.raise_for_status()
        initial_data = initial_response.json()

        total_count = initial_data.get("count", 0)
        total_pages = initial_data.get("total_pages", 1)

        # Calculate the probable total pages from count and limit
        probable_total_pages = (total_count // limit) + (1 if total_count % limit != 0 else 0)

        # Check if probable total pages matches the API's total pages
        if probable_total_pages == total_pages:
            print(f"Total pages match: {probable_total_pages}. Proceeding to fetch all pages.")
        else:
            print(
                f"Warning: Probable total pages ({probable_total_pages}) does not match the API's total pages ({total_pages}). Proceeding cautiously.")

        all_results = []

        # Iterate through all pages based on total pages
        for page in range(1, total_pages + 1):
            print(f"Fetching page {page}/{total_pages}...")
            response = requests.get(f"{BASE_URL}?limit={limit}&page={page}")
            response.raise_for_status()
            page_data = response.json()

            # Iterate through the results and print the id_cedula_busqueda
            for result in page_data.get("results", []):
                print(f"Fetched ID: {result.get('id_cedula_busqueda')}")
                insert_data_to_db([result])

            # Adding a pause between requests
        time.sleep(pause_time)


    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


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
    # You can now pass limit and pause_time as arguments
    data = fetch_data(limit=100, pause_time=2)  # Limiting to 20 records with 1 second pause
    if data:
        insert_data_to_db(data)

import spacy
# from geopy.geocoders import Nominatim  # Commented out geolocation import
import mysql.connector
import json

# Load spaCy model
nlp = spacy.load(r'venv/lib/python3.12/site-packages/es_core_news_sm/es_core_news_sm-3.8.0')

# Nominatim geolocator
# geolocator = Nominatim(user_agent="geoapiExercises")  # Commented out geolocator initialization

# Load database configuration
def load_db_config():
    with open('db_credentials.json', 'r') as file:
        return json.load(file)

# Database configuration
DB_CONFIG = load_db_config()

# Function to fetch records from the database
def fetch_records_from_db(limit=10, offset=0):
    """Fetch records from the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id_cedula_busqueda, nombre_completo, descripcion_desaparicion
            FROM repd_vp_cedulas_principal
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        records = cursor.fetchall()
        return records
    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Function to process NER for locations
def process_ner_and_geolocation(records):
    """Process each record, detect locations with spaCy."""
    for record in records:
        description = record["descripcion_desaparicion"].lower()
        doc = nlp(description)

        # Create a list to store detected locations
        locations = []

        print(f"Record ID: {record['id_cedula_busqueda']}")
        print(f"Nombre: {record['nombre_completo']}")
        print(f"Descripción: {record['descripcion_desaparicion']}")

        # Iterate over the entities detected by spaCy
        for ent in doc.ents:
            print(f"Entity: {ent.text}")
            print(f"  - Label: {ent.label_}")
            #print(f"  - Start: {ent.start_char}, End: {ent.end_char}")

            # If the entity is a location, add it to the locations list
            if ent.label_ == "LOC":  # "LOC" is the label for locations in spaCy
                location = ent.text
                print(f"Detected location: {location}")
                locations.append({
                    "location": location,
                })

        print(f"Locations: {locations}")
        print("-" * 50)

# Example usage: process records in batches
def main():
    offset = 0
    limit = 10  # You can adjust this limit as needed
    while True:
        records = fetch_records_from_db(limit=limit, offset=offset)
        if not records:
            break  # Exit if no more records to process

        process_ner_and_geolocation(records)
        offset += limit  # Move to the next batch of records

if __name__ == "__main__":
    main()

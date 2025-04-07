import spacy
from spacy.pipeline import EntityRuler
import pandas as pd
import mysql.connector
import json
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut
import folium
from spacy import displacy
import os
from jinja2 import Template
import logging
from collections import Counter, defaultdict
import re
import time  # Import time module

# Load spaCy model
NLP_MODEL_PATH = r'venv/lib/python3.12/site-packages/es_core_news_sm/es_core_news_sm-3.8.0'
nlp = spacy.load(NLP_MODEL_PATH)

# Add EntityRuler to the pipeline with refined patterns
ruler = nlp.add_pipe('entity_ruler', before='ner')
DATE_PATTERNS = [{"LOWER": "día"}, {"IS_DIGIT": True}, {"LOWER": "de"},
                 {"LOWER": {"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                                   "julio", "agosto", "septiembre", "octubre", "noviembre",
                                   "diciembre"]}},
                 {"LOWER": "del"}, {"IS_DIGIT": True}]
TIME_PATTERNS = [{"LOWER": {"REGEX": "\\d{1,2}(:\\d{2})?(am|pm)?"}}]
ADDRESS_PATTERNS = [{"LOWER": "calle"}, {"IS_ALPHA": True, "OP": "+"},
                    {"IS_PUNCT": True}, {"IS_DIGIT": True}]
COLONIA_PATTERNS = [{"LOWER": "colonia"}, {"IS_ALPHA": True, "OP": "+"},
                    {"IS_ALPHA": True, "OP": "*"}]
patterns = [
    {"label": "DATE", "pattern": DATE_PATTERNS},
    {"label": "TIME", "pattern": TIME_PATTERNS},
    {"label": "ADDRESS", "pattern": ADDRESS_PATTERNS},
    {"label": "COLONIA", "pattern": COLONIA_PATTERNS},
    {"label": "COLONIA", "pattern": [{"LOWER": "san"}, {"LOWER": "pedro"},
                                     {"LOWER": "tlaquepaque"}]}
]
ruler.add_patterns(patterns)


# Function to load database configuration
def load_db_config(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        return json.load(file)


# Database and API key configuration
config = load_db_config()
DB_CONFIG = {
    'host': config['host'],
    'user': config['user'],
    'password': config['password'],
    'database': config['database'],
}
GOOGLE_MAPS_API_KEY = config['google_api']

# Global cache for geocoding results
CACHE_FILE = 'geocode_cache.json'
TERMS_FILE = 'terms_frequency.txt'


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file)


geocode_cache = load_cache()


def save_terms_frequency(counts):
    with open(TERMS_FILE, 'w') as file:
        for term, collocates in counts.items():
            if any(count > 1 for count in collocates.values()):  # Only log terms with at least 2 occurrences
                collocate_str = '; '.join([f"{k}: {v}" for k, v in collocates.items() if v > 1])
                file.write(f"{term} --- {collocate_str}\n")


def load_terms_frequency():
    if os.path.exists(TERMS_FILE):
        with open(TERMS_FILE, 'r') as file:
            lines = file.readlines()
        counts = {}
        for line in lines:
            term, collocates_str = line.strip().split(" --- ")
            collocates = {k: int(v) for k, v in (colloc.split(": ") for colloc in collocates_str.split("; "))}
            counts[term] = collocates
        return counts
    return {}


# Function to fetch data from the database
def fetch_data_from_db(limit=30):
    """Fetch a limited number of records from the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = f"""
        SELECT id_cedula_busqueda, autorizacion_informacion_publica, 
               condicion_localizacion, nombre_completo, edad_momento_desaparicion, 
               sexo, genero, complexion, estatura, tez, cabello, ojos_color, 
               municipio, estado, fecha_desaparicion, estatus_persona_desaparecida, 
               descripcion_desaparicion, ruta_foto
        FROM repd_vp_cedulas_principal
        LIMIT {limit}
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return pd.DataFrame(results)
    except mysql.connector.Error as e:
        logging.error(f"Error fetching data from database: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def clean_location_text(location):
    """Remove 'calle' and 'colonia' from the location text."""
    words_to_remove = ['calle', 'colonia']
    location_words = location.lower().split()
    return ' '.join(word for word in location_words if word not in words_to_remove)


def extract_tipo_loc(location):
    """Extract 'calle' or 'colonia' from the beginning of the address."""
    words_to_check = ['calle', 'colonia']
    location_words = location.lower().split()
    if location_words[0] in words_to_check:
        return location_words[0]
    return None


def get_location(geolocator, address):
    if address in geocode_cache:
        print(f"DEBUG: Cache hit for address: {address}")
        return geocode_cache[address]
    else:
        print(f"DEBUG: Cache miss for address: {address}")
        try:
            location = geolocator.geocode(address)
        except GeocoderTimedOut:
            logging.error(f"Geocoding timed out for address: {address}")
            return None
        if location:
            geocode_cache[address] = (location.latitude, location.longitude)
            save_cache(geocode_cache)
            return (location.latitude, location.longitude)
        return None


def get_lat_long(location, municipio, estado, geolocator):
    """Geocode a location to get latitude and longitude, limiting to Jalisco, Mexico."""
    cleaned_location = clean_location_text(location)
    full_location = f"{cleaned_location}, {municipio}, {estado}, México"
    return get_location(geolocator, full_location)


def clean_date_text(text):
    """Remove 'día' from the text."""
    return text.replace('día', '').strip()


def process_word_frequencies(df):
    """Process descriptions and record word frequencies while excluding stop words."""
    stop_words = set(spacy.lang.es.stop_words.STOP_WORDS)
    word_counter = Counter()
    collocates = defaultdict(lambda: Counter())

    for description in df['descripcion_desaparicion'].dropna():
        words = re.findall(r'\b\w+\b', description.lower())
        filtered_words = [word for word in words if word not in stop_words]
        word_counter.update(filtered_words)

        for i, word in enumerate(filtered_words):
            if i > 0:  # Check previous word
                collocates[word][f"before {filtered_words[i - 1]}"] += 1
            if i < len(filtered_words) - 1:  # Check next word
                collocates[word][f"after {filtered_words[i + 1]}"] += 1

    combined_counts = {word: dict(collocate) for word, collocate in collocates.items()}
    return combined_counts


def process_descriptions(df, geolocator):
    """Process descriptions using spaCy NER pipeline and plot entities on a map."""
    map_center = [20.676667, -103.3475]  # Center map on Guadalajara, Jalisco
    folium_map = folium.Map(location=map_center, zoom_start=12)
    location_count = 0  # Initialize the location count
    inferences = []  # List to hold inference results

    for idx, row in df.iterrows():
        try:
            description = row['descripcion_desaparicion'].lower()
            municipio = row['municipio']
            estado = row['estado']
            condicion_localizacion = row['condicion_localizacion']
            doc = nlp(description)

            # Extract location entity and tipo_loc
            location_entity = next(((ent.text, ent.label_) for ent in doc.ents
                                    if ent.label_ in ["ADDRESS", "COLONIA"]), None)
            if location_entity:
                loc_text, label = location_entity
                tipo_loc = extract_tipo_loc(loc_text)
                clean_loc_text = clean_location_text(loc_text)  # Remove 'calle' or 'colonia'
                lat, long = get_lat_long(clean_loc_text, municipio, estado, geolocator)
                if lat and long:
                    lat_long = f"{lat},{long}"
                    location_count += 1

            # Extract date entity and clean it
            date_entity = next((ent.text for ent in doc.ents if ent.label_ == "DATE"), None)
            if date_entity:
                clean_date = clean_date_text(date_entity)

            inferences.append({
                "id_cedula_busqueda": row['id_cedula_busqueda'],
                "tipo_loc": tipo_loc if location_entity else None,
                "loc": clean_loc_text if location_entity else None,
                "lat_long": lat_long if location_entity else None,
                "fecha": clean_date if date_entity else None
            })

            # Pause for 10 seconds after every 500 rows
            if idx > 0 and idx % 250 == 0:
                time.sleep(10)

        except Exception as e:
            logging.error(f"Error processing text for ID {row['id_cedula_busqueda']}: {e}")

    logging.info(f"Total locations found by geopy: {location_count}")

    df_inferences = pd.DataFrame(inferences)
    print(df_inferences.to_string())

    return df_inferences


# Function to save DataFrame to SQL
def save_df_to_sql(df, table_name):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id_cedula_busqueda VARCHAR(255) PRIMARY KEY,
            tipo_loc VARCHAR(255),
            loc TEXT,
            lat_long VARCHAR(255),
            fecha VARCHAR(255)
        )
        """)

        for _, row in df.iterrows():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id_cedula_busqueda = %s",
                           (row['id_cedula_busqueda'],))
            record_exists = cursor.fetchone()[0]

            if record_exists:
                print(f"Record with id_cedula_busqueda {row['id_cedula_busqueda']} already exists. Skipping...")
                continue

            cursor.execute(f"""
            INSERT INTO {table_name} (id_cedula_busqueda, tipo_loc, loc, lat_long, fecha)
            VALUES (%s, %s, %s, %s, %s)
            """, (row['id_cedula_busqueda'], row['tipo_loc'], row['loc'], row['lat_long'], row['fecha']))

        conn.commit()

    except mysql.connector.Error as e:
        logging.error(f"Error saving DataFrame to SQL: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Fetch data and process
df = fetch_data_from_db(limit=9000)
if df is not None and not df.empty:
    logging.info(f"Fetched {len(df)} records")

    # Initialize geolocator
    geolocator = GoogleV3(api_key=GOOGLE_MAPS_API_KEY)

    # Process descriptions for geocoding and entity extraction
    processed_df = process_descriptions(df, geolocator)

    # Save DataFrame to SQL
    save_df_to_sql(processed_df, 'repd_vp_inferencias')

    # Update the word frequencies and save to file
    term_frequencies = process_word_frequencies(df)
    save_terms_frequency(term_frequencies)

    logging.info(f"Term frequencies saved to {TERMS_FILE}")

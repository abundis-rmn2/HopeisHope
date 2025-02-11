import spacy
from spacy.pipeline import EntityRuler
import pandas as pd
import mysql.connector
import json
import os
from jinja2 import Template
import logging

# Load spaCy model
NLP_MODEL_PATH = r'venv/lib/python3.12/site-packages/es_core_news_sm/es_core_news_sm-3.8.0'
nlp = spacy.load(NLP_MODEL_PATH)

# Add EntityRuler to the pipeline with refined patterns
ruler = nlp.add_pipe('entity_ruler', before='ner')
DATE_PATTERNS = [{"LOWER": "día"}, {"IS_DIGIT": True}, {"LOWER": "de"},
                 {"LOWER": {"IN": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                   "septiembre", "octubre", "noviembre", "diciembre"]}},
                 {"LOWER": "del"}, {"IS_DIGIT": True}]
TIME_PATTERNS = [{"LOWER": {"REGEX": "\\d{1,2}(:\\d{2})?(am|pm)?"}}]
ADDRESS_PATTERNS = [{"LOWER": "calle"}, {"IS_ALPHA": True, "OP": "+"}, {"IS_PUNCT": True}, {"IS_DIGIT": True}]
COLONIA_PATTERNS = [{"LOWER": "colonia"}, {"IS_ALPHA": True, "OP": "+"}, {"IS_ALPHA": True, "OP": "*"}]
patterns = [
    {"label": "DATE", "pattern": DATE_PATTERNS},
    {"label": "TIME", "pattern": TIME_PATTERNS},
    {"label": "ADDRESS", "pattern": ADDRESS_PATTERNS},
    {"label": "COLONIA", "pattern": COLONIA_PATTERNS},
    {"label": "COLONIA", "pattern": [{"LOWER": "san"}, {"LOWER": "pedro"}, {"LOWER": "tlaquepaque"}]}
]
ruler.add_patterns(patterns)


# Function to load database configuration
def load_db_config(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        return json.load(file)


# Database configuration
config = load_db_config()
DB_CONFIG = {
    'host': config['host'],
    'user': config['user'],
    'password': config['password'],
    'database': config['database'],
}


# Function to fetch data from the database
def fetch_data_from_db(limit=30):
    """Fetch a limited number of records from the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = f"""
        SELECT id_cedula_busqueda, autorizacion_informacion_publica, condicion_localizacion,
               nombre_completo, edad_momento_desaparicion, sexo, genero, complexion, estatura,
               tez, cabello, ojos_color, municipio, estado, fecha_desaparicion,
               estatus_persona_desaparecida, descripcion_desaparicion, ruta_foto
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


def get_status_color(condicion_localizacion):
    """Get color based on the condicion_localizacion."""
    status_colors = {
        'NO APLICA': 'red',
        'CON VIDA': 'green',
        'SIN VIDA': 'black'
    }
    return status_colors.get(condicion_localizacion.upper(), 'gray')


def process_descriptions(df, weight=1):
    """Process descriptions using spaCy NER pipeline and extract relevant information."""
    inferences = []

    for idx, row in df.iterrows():
        if row['descripcion_desaparicion'] is None:
            row['descripcion_desaparicion'] = "   "
        try:
            description = row['descripcion_desaparicion'].lower()
            municipio = row['municipio']
            estado = row['estado']
            condicion_localizacion = row['condicion_localizacion']

            doc = nlp(description)
            calle = None
            colonia = None

            for ent in doc.ents:
                if ent.label_ == "ADDRESS":
                    calle = ent.text
                elif ent.label_ == "COLONIA":
                    colonia = ent.text

            if calle or colonia:
                inferences.append({
                    "id_cedula_busqueda": row['id_cedula_busqueda'],
                    "calle": calle,
                    "colonia": colonia,
                    "ciudad": municipio,
                    "lat-long": None,  # Placeholder for the actual lat-long values
                })

        except Exception as e:
            logging.error(f"Error processing text for ID {row['id_cedula_busqueda']}: {e}")

    return pd.DataFrame(inferences)


df = fetch_data_from_db(limit=83)
if df is not None and not df.empty:
    logging.info(f"Fetched {len(df)} records")
    repd_vp_inferences = process_descriptions(df, weight=0.2)  # Adjust the weight as needed
    print(repd_vp_inferences)
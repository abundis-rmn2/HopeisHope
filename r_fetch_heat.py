import spacy
from spacy.pipeline import EntityRuler
import pandas as pd
import mysql.connector
import json
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut
import folium
from folium.plugins import HeatMap
from spacy import displacy
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


# Database and API key configuration
config = load_db_config()
DB_CONFIG = {
    'host': config['host'],
    'user': config['user'],
    'password': config['password'],
    'database': config['database'],
}
GOOGLE_MAPS_API_KEY = config['google_api']


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


def get_lat_long(location, municipio, estado, geolocator):
    """Geocode a location to get latitude and longitude, limiting to Jalisco, Mexico."""
    cleaned_location = clean_location_text(location)
    full_location = f"{cleaned_location}, {municipio}, {estado}, México"
    try:
        loc = geolocator.geocode(full_location, timeout=10)
        return (loc.latitude, loc.longitude) if loc else (None, None)
    except GeocoderTimedOut:
        logging.error(f"Geocoding timed out for location: {full_location}")
        return None, None


def get_status_color(condicion_localizacion):
    """Get color based on the condicion_localizacion."""
    status_colors = {
        'NO APLICA': 'red',
        'CON VIDA': 'green',
        'SIN VIDA': 'black'
    }
    return status_colors.get(condicion_localizacion.upper(), 'gray')


def process_descriptions(df, geolocator, weight=1):
    """Process descriptions using spaCy NER pipeline and plot entities on a map."""
    map_center = [20.676667, -103.3475]  # Center map on Guadalajara, Jalisco
    folium_map = folium.Map(location=map_center, zoom_start=12)

    fg_na = folium.FeatureGroup(name='No Aplica')
    fg_cv = folium.FeatureGroup(name='Con Vida')
    fg_sv = folium.FeatureGroup(name='Sin Vida')

    heat_data_na = []
    heat_data_cv = []
    heat_data_sv = []

    for idx, row in df.iterrows():
        if row['descripcion_desaparicion'] is None:
            row['descripcion_desaparicion'] = "   "
        try:
            description = row['descripcion_desaparicion'].lower()
            municipio = row['municipio']
            estado = row['estado']
            condicion_localizacion = row['condicion_localizacion']
            status_color = get_status_color(condicion_localizacion)
            tooltip_text = (f"ID: {row['id_cedula_busqueda']}\n"
                            f"Condición Localización: {condicion_localizacion}\n"
                            f"Municipio: {municipio}\n"
                            f"Estado: {estado}\n")

            doc = nlp(description)
            location_entity = next(((ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["ADDRESS", "COLONIA"]),
                                   None)
            if location_entity:
                text, label = location_entity
                lat, long = get_lat_long(text, municipio, estado, geolocator)
                if lat and long:
                    if condicion_localizacion.upper() == 'NO APLICA':
                        heat_data_na.append([lat, long, weight])
                        folium.CircleMarker(
                            location=[lat, long],
                            radius=2,
                            color=status_color,
                            fill=True,
                            fill_color=status_color,
                            fill_opacity=0.7,
                            popup=tooltip_text
                        ).add_to(fg_na)
                    elif condicion_localizacion.upper() == 'CON VIDA':
                        heat_data_cv.append([lat, long, weight])
                        folium.CircleMarker(
                            location=[lat, long],
                            radius=2,
                            color=status_color,
                            fill=True,
                            fill_color=status_color,
                            fill_opacity=0.7,
                            popup=tooltip_text
                        ).add_to(fg_cv)
                    elif condicion_localizacion.upper() == 'SIN VIDA':
                        heat_data_sv.append([lat, long, weight])
                        folium.CircleMarker(
                            location=[lat, long],
                            radius=2,
                            color=status_color,
                            fill=True,
                            fill_color=status_color,
                            fill_opacity=0.7,
                            popup=tooltip_text
                        ).add_to(fg_sv)
            displacy.render(doc, style="ent", jupyter=False)
        except Exception as e:
            logging.error(f"Error processing text for ID {row['id_cedula_busqueda']}: {e}")

    # Create heat maps for each "condicion_localizacion"
    if heat_data_na:
        HeatMap(heat_data_na, name='No Aplica', gradient={0: 'white', 0.2: 'red'}).add_to(fg_na)
    if heat_data_cv:
        HeatMap(heat_data_cv, name='Con Vida', gradient={0: 'white', 0.2: 'green'}).add_to(fg_cv)
    if heat_data_sv:
        HeatMap(heat_data_sv, name='Sin Vida', gradient={0: 'white', 0.2: 'black'}).add_to(fg_sv)

    fg_na.add_to(folium_map)
    fg_cv.add_to(folium_map)
    fg_sv.add_to(folium_map)

    folium.LayerControl().add_to(folium_map)

    folium_map.save("heat_map.html")
    logging.info("Heat map has been saved to heat_map.html")


df = fetch_data_from_db(limit=8033)
if df is not None and not df.empty:
    logging.info(f"Fetched {len(df)} records")
    print(df.to_string())
    geolocator = GoogleV3(api_key=GOOGLE_MAPS_API_KEY)
    process_descriptions(df, geolocator, weight=0.2)  # Adjust the weight as needed

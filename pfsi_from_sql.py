import json
import requests
import folium
import html
import re
from bs4 import BeautifulSoup
from datetime import datetime
from geopy.geocoders import GoogleV3
from folium.plugins import MarkerCluster
import mysql.connector


def load_api_key(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        config = json.load(file)
        return config['google_api']


def load_db_credentials(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        config = json.load(file)
    try:
        return config['user'], config['password'], config['host'], config['database']
    except KeyError as e:
        raise KeyError(f"Missing required key in the configuration file: {str(e)}")


def connect_to_database():
    user, password, host, database = load_db_credentials()
    return mysql.connector.connect(
        user=user,
        password=password,
        host=host,
        database=database
    )


def retrieve_data_from_db(start_date, end_date):
    db_connection = connect_to_database()
    cursor = db_connection.cursor(dictionary=True)

    query = """
    SELECT 
        ID, 
        Fecha_Ingreso, 
        Sexo, 
        Probable_nombre, 
        Edad, 
        Tatuajes, 
        Indumentarias, 
        Senas_Particulares, 
        Delegacion_IJCF 
    FROM pfsi_v2_principal 
    WHERE Fecha_Ingreso BETWEEN %s AND %s
    """

    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()

    cursor.close()
    db_connection.close()

    if not rows:
        print("DEBUG: No data found for the given date range.")
        return {"datos": []}

    return {"datos": rows}


def clean_html(raw_html):
    clean_text = raw_html.encode().decode('unicode_escape')
    clean_text = html.unescape(clean_text)
    clean_text = clean_text.replace('\\/', '/')
    clean_text = re.sub(r'\r\n|\t', '', clean_text)
    clean_text = re.sub(r'>\s+<', '><', clean_text)
    return clean_text


geocode_cache = {}


def get_location(geolocator, address):
    if address in geocode_cache:
        print(f"DEBUG: Cache hit for address: {address}")
        return geocode_cache[address]
    else:
        print(f"DEBUG: Cache miss for address: {address}")
        location = geolocator.geocode(address)
        if location:
            geocode_cache[address] = (location.latitude, location.longitude)
            return (location.latitude, location.longitude)
        return None


def generate_map(data, api_key, start_date, end_date):
    geolocator = GoogleV3(api_key=api_key)
    map_center = get_location(geolocator, "Guadalajara, Jalisco, Mexico")
    location_map = folium.Map(location=map_center, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(location_map)
    for entry in data["datos"]:
        delegacion = entry.get("Delegacion_IJCF", "")
        if delegacion:
            location = get_location(geolocator, delegacion + ", Jalisco, Mexico")
            if location:
                folium.Marker(
                    location=location,
                    popup=f'{entry["Probable_nombre"]}, {entry["Fecha_Ingreso"]}, {entry["Sexo"]}',
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(marker_cluster)
    filename = f"sql_delegaciones_map_{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}.html"
    location_map.save(filename)



def main():
    api_key = load_api_key()
    start_date = "2018-01-01"
    end_date = "2024-11-22"
    json_response = retrieve_data_from_db(start_date, end_date)
    if json_response:
        generate_map(json_response, api_key, start_date, end_date)


if __name__ == '__main__':
    main()

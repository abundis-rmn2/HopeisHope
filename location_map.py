import requests
from bs4 import BeautifulSoup
import json
import html
import re
from geopy.geocoders import GoogleV3
import folium
from folium.plugins import MarkerCluster
from datetime import datetime


# Function to load API key from the configuration file
def load_api_key(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        config = json.load(file)
        return config['google_api']


def clean_html(raw_html):
    """
    Cleans HTML content by removing unwanted escape sequences and preserving table structures.
    """
    clean_text = raw_html.encode().decode('unicode_escape')
    clean_text = html.unescape(clean_text)
    clean_text = clean_text.replace('\\/', '/')
    clean_text = re.sub(r'\r\n|\t', '', clean_text)
    clean_text = re.sub(r'>\s+<', '><', clean_text)
    return clean_text


def retrieve_data(start_date, end_date):
    url = 'http://consultas.cienciasforenses.jalisco.gob.mx/buscarpfsi_v2.php'
    payload = {
        'inicio': start_date,
        'fin': end_date,
        'sexo': '',
        'tatuajes': '',
        'nocache': '0.6192728608924991',
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("DEBUG: Response Status Code: 200")
        print("DEBUG: Response Text (first 500 chars):\n", response.text[:500])
        json_prefix = '{"datos":"'
        bom = '\ufeff'
        raw_text = response.text
        if raw_text.startswith(bom):
            print("DEBUG: BOM detected and removed.")
            raw_text = raw_text.lstrip(bom)
        if raw_text.startswith(json_prefix):
            html_content = raw_text[len(json_prefix):-2]
            html_content = clean_html(html_content)
            print("DEBUG: Cleaned HTML Content (first 500 chars):\n", html_content[:500])
            return html_content
        else:
            print("DEBUG: Unexpected response format.")
            return None
    else:
        print(f"DEBUG: Request failed with status code {response.status_code}")
        return None


def parse_html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if table is None:
        print("DEBUG: Table not found in the HTML.")
        return json.dumps({"datos": []}, indent=4, ensure_ascii=False)
    headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
    print("DEBUG: Parsed Headers:", headers)
    rows = table.find('tbody').find_all('tr')
    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) != len(headers):
            print("DEBUG: Mismatch in number of cells and headers")
            continue
        entry = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
        data.append(entry)
        print(f"DEBUG: Parsed Entry: {entry}")
    return {"datos": data}


# In-memory cache for geocoded locations
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

    # Add marker clustering
    marker_cluster = MarkerCluster().add_to(location_map)

    for entry in data["datos"]:
        delegacion = entry.get("Delegación IJCF", "")
        if delegacion:
            location = get_location(geolocator, delegacion + ", Jalisco, Mexico")
            if location:
                folium.Marker(
                    location=location,
                    popup=f'{entry["Probable nombre"]}, {entry["Fecha Ingreso"]}, {entry["Sexo"]}',
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(marker_cluster)

    # Save the map to a file named based on the date range
    filename = f"delegaciones_map_{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}.html"
    location_map.save(filename)


def main():
    api_key = load_api_key()

    # Specify date range
    start_date = "01/01/2018"
    end_date = "22/11/2024"

    raw_response = retrieve_data(start_date, end_date)
    if raw_response:
        json_response = parse_html_to_json(raw_response)
        generate_map(json_response, api_key, start_date, end_date)


if __name__ == '__main__':
    main()
import requests
from bs4 import BeautifulSoup
import json
import html
import re
import mysql.connector
from datetime import datetime


def load_db_credentials(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        return json.load(file)


def clean_html(raw_html):
    """
    Cleans HTML content by removing unwanted escape sequences and preserving table structures.
    """
    # Decode Unicode escape sequences and HTML entities
    clean_text = raw_html.encode().decode('unicode_escape')
    clean_text = html.unescape(clean_text)

    # Remove unnecessary escape characters
    clean_text = clean_text.replace('\\/', '/')

    # Retain the basic structure by keeping table-related tags
    clean_text = re.sub(r'\r\n|\t', '', clean_text)  # Remove new lines and tabs
    clean_text = re.sub(r'>\s+<', '><', clean_text)  # Remove extra spaces between tags

    return clean_text


def retrieve_data():
    url = 'http://consultas.cienciasforenses.jalisco.gob.mx/buscarpfsi_v2.php'

    # Define the payload for the POST request
    payload = {
        'inicio': '01/11/2018',
        'fin': '30/11/2024',
        'sexo': '',
        'tatuajes': '',
        'nocache': '0.6192728608924991',
    }

    # Make the POST request
    response = requests.post(url, data=payload)

    # Check the response status code
    if response.status_code == 200:
        print("DEBUG: Response Status Code: 200")
        # Debug: print response text
        print("DEBUG: Response Text (first 500 chars):\n", response.text[:500])

        # Handle BOM and isolate the HTML content by stripping out the JSON structure
        json_prefix = '{"datos":"'
        bom = '\ufeff'  # BOM character
        raw_text = response.text

        if raw_text.startswith(bom):
            print("DEBUG: BOM detected and removed.")
            raw_text = raw_text.lstrip(bom)

        if raw_text.startswith(json_prefix):
            html_content = raw_text[
                           len(json_prefix):-2]  # Remove the prefix and the last two characters (\"", and trailing "}")
            # Clean the HTML content
            html_content = clean_html(html_content)

            print("DEBUG: Cleaned HTML Content (first 500 chars):\n",
                  html_content[:500])  # Debug: print cleaned HTML content
            return html_content
        else:
            print("DEBUG: Unexpected response format.")
            return None
    else:
        print(f"DEBUG: Request failed with status code {response.status_code}")
        return None


def parse_html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table in the HTML and parse it
    table = soup.find('table')
    if table is None:
        print("DEBUG: Table not found in the HTML.")
        return {"datos": []}

    headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
    print("DEBUG: Parsed Headers:", headers)  # Debug: print parsed headers

    rows = table.find('tbody').find_all('tr')
    data = []

    for row in rows:
        cells = row.find_all('td')
        if len(cells) != len(headers):
            print("DEBUG: Mismatch in number of cells and headers")
            continue
        entry = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
        data.append(entry)
        print(f"DEBUG: Parsed Entry: {entry}")  # Debug: print each parsed entry

    return {"datos": data}


def insert_entry(cursor, entry):
    sql = """
    INSERT INTO pfsi_v2_principal (
        ID, Fecha_Ingreso, Sexo, Probable_nombre, Edad,
        Tatuajes, Indumentarias, Senas_Particulares, Delegacion_IJCF
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        Fecha_Ingreso=VALUES(Fecha_Ingreso),
        Sexo=VALUES(Sexo),
        Probable_nombre=VALUES(Probable_nombre),
        Edad=VALUES(Edad),
        Tatuajes=VALUES(Tatuajes),
        Indumentarias=VALUES(Indumentarias),
        Senas_Particulares=VALUES(Senas_Particulares),
        Delegacion_IJCF=VALUES(Delegacion_IJCF)
    """
    # Parse the date appropriately
    fecha_ingreso = datetime.strptime(entry["Fecha Ingreso"], "%d/%m/%Y").strftime("%Y-%m-%d")

    values = (
        entry["ID"],
        fecha_ingreso,
        entry["Sexo"],
        entry["Probable nombre"],
        entry["Edad"],
        entry["Tatuajes"],
        entry["Indumentarias"],
        entry["Señas Particulares"],
        entry["Delegación IJCF"]
    )
    cursor.execute(sql, values)


def update_database(json_response):
    # Load database credentials
    credentials = load_db_credentials()

    # Connect to the database
    cnx = mysql.connector.connect(
        host=credentials['host'],
        user=credentials['user'],
        password=credentials['password'],
        database=credentials['database']
    )
    cursor = cnx.cursor()

    # Insert each entry in the JSON response
    for entry in json_response["datos"]:
        insert_entry(cursor, entry)

    # Commit the transaction
    cnx.commit()

    # Close the connection
    cursor.close()
    cnx.close()


def main():
    raw_response = retrieve_data()
    if raw_response:
        json_response = parse_html_to_json(raw_response)
        update_database(json_response)


if __name__ == '__main__':
    main()
import pandas as pd
from opencage.geocoder import OpenCageGeocode


def get_lat_lng(geocoder, place):
    try:
        result = geocoder.geocode(place)
        if result and len(result) > 0:
            return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    except Exception as e:
        print(f"Error geocoding {place}: {e}")
    return None, None


def add_lat_lng_to_csv(input_file: str, output_file: str, api_key: str):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Initialize OpenCage Geocoder
    geocoder = OpenCageGeocode(api_key)

    # Columns to add
    df['latitude'] = None
    df['longitude'] = None

    # Geocode each municipality
    for i, row in df.iterrows():
        place = f"{row['nom_mun']}, {row['nom_ent']}, Mexico"
        print(f"Geocoding {place}...")
        lat, lng = get_lat_lng(geocoder, place)
        df.at[i, 'latitude'] = lat
        df.at[i, 'longitude'] = lng

    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_file, index=False)


# Example usage with your OpenCage API key
api_key = 'efbcee3fff2948c4a724eed8281b8f2e'
add_lat_lng_to_csv('./csv/estatal_limpio.csv', './csv/estatal_limpio_with_lat_lng.csv', api_key)

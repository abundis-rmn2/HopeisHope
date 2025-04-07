import requests
import time

BASE_URL = "https://repd.jalisco.gob.mx/api/v1/version_publica/repd-version-publica-cedulas-busqueda/"


def fetch_all_data(limit=3, pause_time=1):
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

            # Collect all results
            all_results.extend(page_data.get("results", []))

            # Adding a pause between requests
            time.sleep(pause_time)

        print(f"Fetched {len(all_results)} records.")
        return all_results

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


# Example of usage
all_data = fetch_all_data(limit=100, pause_time=1)

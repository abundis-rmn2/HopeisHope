import csv
import os
import requests
import time
from urllib.parse import urlparse, parse_qs

# Create directory structure if it doesn't exist
os.makedirs('./img/indicios3', exist_ok=True)

def extract_file_id(url):
    """Extract Google Drive file ID from URL"""
    if not url:
        return None
        
    # Handle standard Google Drive file URL format
    if '/file/d/' in url:
        # Format: https://drive.google.com/file/d/FILE_ID/view?...
        file_id = url.split('/file/d/')[1].split('/')[0]
        return file_id
    
    # Handle Google Drive "open" URL format
    elif 'drive.google.com/open' in url:
        # Format: https://drive.google.com/open?id=FILE_ID&usp=...
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'id' in query_params:
                return query_params['id'][0]
        except Exception:
            pass
    
    return None

def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive"""
    # Google Drive direct download URL
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Start a session to handle cookies
    session = requests.Session()
    response = session.get(url, stream=True)
    
    # Check if there's a download warning (for large files Google shows a confirmation page)
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            # If there is a warning, we need to confirm the download
            url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={value}"
            response = session.get(url, stream=True)
    
    # Save the file
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

def main():
    csv_path = '/home/abundis/PycharmProjects/HopeisHope/csv/complete_data3.csv'
    processed = 0
    skipped = 0
    failed = 0
    
    print("Starting download process...")
    
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Skip empty rows
            if not row['id'] or row['id'].strip() == '':
                continue
            
            # Get the link (try both columns)
            link = row.get('LINK FOTO') or ''
            hyperlink = row.get('hyperlink') or ''
            
            # First try getting file ID from hyperlink column (which seems more reliable)
            file_id = extract_file_id(hyperlink)
            
            # If that fails, try LINK FOTO column
            if not file_id:
                file_id = extract_file_id(link)
            
            # If both fail, report the error
            if not file_id:
                print(f"Could not extract file ID for {row['id']}: {link or hyperlink}")
                failed += 1
                continue
            
            # Define destination path
            destination = f"./img/indicios2/{row['id']}.jpg"
            
            # Skip if already downloaded
            if os.path.exists(destination):
                print(f"Skipping {row['id']} - already downloaded")
                skipped += 1
                continue
            
            # Download the file
            try:
                print(f"Downloading {row['id']}...")
                download_file_from_google_drive(file_id, destination)
                print(f"✓ Successfully saved to {destination}")
                processed += 1
                # Delay to avoid overloading Google Drive
                time.sleep(1)
            except Exception as e:
                print(f"✗ Error downloading {row['id']}: {str(e)}")
                failed += 1
    
    print(f"\nDownload complete: {processed} downloaded, {skipped} skipped, {failed} failed")

if __name__ == "__main__":
    main()

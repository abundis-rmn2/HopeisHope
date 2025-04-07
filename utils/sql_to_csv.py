import mysql.connector
import pandas as pd
import json
import logging

table = 'pfsi_v2_principal'

def load_db_config(file_path='db_credentials.json'):
    with open(file_path, 'r') as file:
        return json.load(file)

def fetch_all_data():
    """Fetch all records from the database."""
    config = load_db_config()
    
    DB_CONFIG = {
        'host': config['host'],
        'user': config['user'],
        'password': config['password'],
        'database': config['database'],
    }
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM {table}"
        cursor.execute(query)
        results = cursor.fetchall()
        df = pd.DataFrame(results)
        print(f"Retrieved {len(df)} records")
        return df
        
    except mysql.connector.Error as e:
        logging.error(f"Error fetching data from database: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Execute the function
df_all = fetch_all_data()
if df_all is not None:
    df_all.to_csv(f'./csv/equi/{table}.csv', index=False)
    print("Data saved to CSV file")
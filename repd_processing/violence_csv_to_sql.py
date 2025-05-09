import json
import pandas as pd
import mysql.connector
from mysql.connector import Error

def load_db_config(file_path='db_credentials.json'):
    """Load database configuration from JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

# Load database configuration
config = load_db_config()

DB_CONFIG = {
    'host': config['host'],
    'user': config['user'],
    'password': config['password'],
    'database': config['database'],
}

# Load CSV file
csv_file_path = "filtered_cases_with_violence_terms.csv"  # Update with actual path
df = pd.read_csv(csv_file_path)

try:
    # Establish database connection
    connection = mysql.connector.connect(**DB_CONFIG)
    if connection.is_connected():
        cursor = connection.cursor()

        # Check if `id_cedula_busqueda` column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'repd_vp_inferencia3' 
            AND COLUMN_NAME = 'id_cedula_busqueda'
        """)
        if cursor.fetchone()[0] == 0:
            print("Error: Column 'id_cedula_busqueda' does not exist. Exiting.")
            exit()

        # Ensure required columns exist
        required_columns = {
            "sum_score": "FLOAT DEFAULT 0",
            "violence_score": "FLOAT DEFAULT 0",
            "violence_terms": "TEXT"
        }

        for column, data_type in required_columns.items():
            cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'repd_vp_inferencia3' 
                AND COLUMN_NAME = '{column}'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute(f"ALTER TABLE repd_vp_inferencia3 ADD COLUMN {column} {data_type}")
                print(f"Column '{column}' added to the database.")

        connection.commit()  # Save schema changes

        # Iterate through CSV data and update database
        for _, row in df.iterrows():
            id_cedula = row["id_cedula_busqueda"]
            sum_score = row["sum_score"]
            violence_score = row["violence_score"]
            violence_terms = row["violence_terms"]  # New field

            # Update query
            update_query = """
            UPDATE repd_vp_inferencia3
            SET sum_score = %s, violence_score = %s, violence_terms = %s
            WHERE id_cedula_busqueda = %s
            """
            cursor.execute(update_query, (sum_score, violence_score, violence_terms, id_cedula))
            print( id_cedula + " record Updated")

        # Commit changes
        connection.commit()
        print("Database updated successfully.")

except Error as e:
    print(f"Error: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed.")

import json
import mysql.connector
from mysql.connector import Error

# Load MySQL credentials from external file
def load_db_credentials(file_path='db_credentials.json'):
    try:
        with open(file_path, 'r') as file:
            credentials = json.load(file)
        return credentials
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the credentials file.")
        return None

# Check MySQL connection
def check_mysql_connection():
    credentials = load_db_credentials()

    if credentials is None:
        return

    try:
        # Establish connection to MySQL database
        connection = mysql.connector.connect(
            host=credentials['host'],
            user=credentials['user'],
            password=credentials['password'],
            database=credentials['database']
        )

        if connection.is_connected():
            print("Connection to MySQL database successful")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection is closed")

# Close the connection
def close_connection(connection):
    if connection:
        connection.close()
        print("MySQL connection closed")

# Example usage
if __name__ == "__main__":
    connection = check_mysql_connection()
    close_connection(connection)

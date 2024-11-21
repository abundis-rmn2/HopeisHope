import json
import mysql.connector
from mysql.connector import Error


# Load MySQL credentials from external file
def load_db_credentials():
    with open('db_credentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials


# Check MySQL connection
def check_mysql_connection():
    credentials = load_db_credentials()

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
            return connection
        else:
            print("Failed to connect to MySQL database")

    except Error as e:
        print(f"Error: {e}")
        return None


# Close the connection
def close_connection(connection):
    if connection:
        connection.close()
        print("MySQL connection closed")


# Example usage
if __name__ == "__main__":
    connection = check_mysql_connection()
    close_connection(connection)

import requests
import sqlite3
import json

# Database connection details
DB_NAME = 'metro_tickets.db'
STATIONS_TABLE_NAME = 'stations'
API_URL = 'https://quickticketapi.chennaimetrorail.org/api/airtel/stations'

def create_stations_table(conn):
    """Creates the stations table in the database if it doesn't exist."""
    try:
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {STATIONS_TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                lineId TEXT,
                stationId TEXT,
                code TEXT,
                name TEXT,
                taName TEXT,
                address TEXT,
                latitude REAL,
                longitude REAL,
                sequenceNo INTEGER
            )
        ''')
        conn.commit()
        print(f"Table '{STATIONS_TABLE_NAME}' created or already exists.")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def fetch_stations_data(api_url):
    """Fetches station data from the CMRL API."""
    try:
        response = requests.get(api_url, headers={'accept': 'text/plain'})

        # Raise an exception for HTTP errors (4xx or 5xx)
        response.raise_for_status()  

        data = response.json()
        if data['statusCode'] == 200:
            return data['result']
        else:
            print(f"API returned status code: {data['statusCode']} with message: {data['message']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def is_table_populated(conn, table_name):
    """Checks if the specified table has any data."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"Error checking table population: {e}")
        return True  # Assume populated to avoid errors

def store_stations_data(conn, stations_data):
    """Stores the station data into the stations table, only if it's empty."""
    if not stations_data:
        print("No station data to store.")
        return

    if is_table_populated(conn, STATIONS_TABLE_NAME):
        print(f"Table '{STATIONS_TABLE_NAME}' is already populated. Skipping data insertion.")
        return

    try:
        cursor = conn.cursor()
        for station in stations_data:
            cursor.execute(f'''
                INSERT INTO {STATIONS_TABLE_NAME} (id, lineId, stationId, code, name, taName, address, latitude, longitude, sequenceNo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                station['id'],
                station['lineId'],
                station['stationId'],
                station['code'],
                station['name'],
                station['taName'],
                station['address'],
                station['latitude'],
                station['longitude'],
                station['sequenceNo']
            ))
        conn.commit()
        print(f"Successfully stored {len(stations_data)} stations in the database.")
    except sqlite3.Error as e:
        print(f"Error inserting data into the table: {e}")

def main():
    """Main function to orchestrate the data fetching and storage."""
    try:
        conn = sqlite3.connect(DB_NAME)
        print(f"Connected to database: {DB_NAME}")

        create_stations_table(conn)

        # Check if the table is already populated before fetching and storing data
        if not is_table_populated(conn, STATIONS_TABLE_NAME):
            stations_data = fetch_stations_data(API_URL)

            if stations_data:
                store_stations_data(conn, stations_data)
        else:
            print(f"Table '{STATIONS_TABLE_NAME}' is already populated.  Skipping fetch and store.")

    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
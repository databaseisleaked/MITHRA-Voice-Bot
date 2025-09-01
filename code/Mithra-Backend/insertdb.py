import json
import sqlite3

# Load JSON data from file
with open("Station_Details.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Connect to SQLite database (or create it)
conn = sqlite3.connect("NewMetroDetails.db")
cursor = conn.cursor()

# Create tables for stations, platforms, and lifts/escalators
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_name TEXT UNIQUE,
        alias TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS platforms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER,
        platform_no INTEGER,
        direction TEXT,
        FOREIGN KEY (station_id) REFERENCES stations(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lifts_escalators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id INTEGER,
        name TEXT,
        floor TEXT,
        location TEXT,
        FOREIGN KEY (station_id) REFERENCES stations(id)
    )
''')

# Insert data into database
for station in data["stations"]:
    # Convert alias to a string (handle lists)
    alias = ", ".join(station["alias"]) if isinstance(station["alias"], list) else station["alias"]
    
    # Insert station details
    cursor.execute("INSERT OR IGNORE INTO stations (station_name, alias) VALUES (?, ?)", 
                   (station["station_name"], alias))
    
    # Get the station ID
    cursor.execute("SELECT id FROM stations WHERE station_name = ?", (station["station_name"],))
    station_id = cursor.fetchone()[0]

    # Insert platform details
    for platform in station.get("platforms", []):  # ✅ Using .get() to avoid KeyError
        cursor.execute("INSERT INTO platforms (station_id, platform_no, direction) VALUES (?, ?, ?)", 
                       (station_id, platform["platform_no"], platform["direction"]))

    # Insert lifts/escalators details (Check if key exists)
    if "lifts_escalators" in station:  # ✅ Checking if key exists before looping
        for lift in station["lifts_escalators"]:
            cursor.execute("INSERT INTO lifts_escalators (station_id, name, floor, location) VALUES (?, ?, ?, ?)", 
                           (station_id, lift["name"], lift["floor"], lift["location"]))

# Commit and close connection
conn.commit()
conn.close()

print("✅ Data successfully stored in NewMetroDetails.db!")

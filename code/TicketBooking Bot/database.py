import sqlite3

conn = sqlite3.connect("metro_tickets.db")  # Connect to the database
cursor = conn.cursor()

# Create the 'tickets' table if it does not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        source TEXT,
        destination TEXT,
        num_tickets INTEGER,
        journey_type TEXT,
        phone_number TEXT,
        cost REAL,
        payment_method TEXT,
        booking_time TEXT,
        expiry_time TEXT,
        ticket_type TEXT
    )
''')

conn.commit()
conn.close()

print("✅ Table 'tickets' has been created successfully!")
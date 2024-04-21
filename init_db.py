import sqlite3
import random
from datetime import datetime, timedelta

def get_minimum_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT MIN(price) FROM parking_spots')
    min_price = cursor.fetchone()[0]
    return float(min_price) if min_price is not None else 0.00

def get_maximum_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(price) FROM parking_spots')
    max_price = cursor.fetchone()[0]
    return float(max_price) if max_price is not None else 0.00

def random_coordinates():
    # Coordinates for Düsseldorf ± some offset
    lat = 51.2277 + random.uniform(-0.1, 0.1)
    lng = 6.7735 + random.uniform(-0.1, 0.1)
    return lat, lng

def get_filtered_parking_spots(conn, spot_type, max_price, start_date, end_date, only_available=False):
    cursor = conn.cursor()
    try:
        # Build the SELECT clause
        select_clause = '''
        SELECT ps.id, ps.location, ps.lat, ps.lng, ps.type, ps.price,
        CASE WHEN b.spot_id IS NULL THEN 1 ELSE 0 END AS available
        FROM parking_spots ps
        '''

        # Build the LEFT JOIN clause on bookings to determine availability
        left_join_clause = '''
        LEFT JOIN (
            SELECT spot_id
            FROM bookings
            WHERE end_date >= ? AND start_date <= ?
            GROUP BY spot_id
        ) b ON ps.id = b.spot_id
        '''
        
        # Initialize parameters for the booking overlap condition
        params = [start_date, end_date]

        conditions = []

        # Filter by spot type if specified
        if spot_type and spot_type != 'All':
            conditions.append('ps.type = ?')
            params.append(spot_type)

        # Add condition for price if specified
        if max_price and max_price != 'No Max':
            conditions.append('ps.price <= ?')
            params.append(max_price)

        # Ensure we include only available spots if requested
        if only_available:
            conditions.append('b.spot_id IS NULL')

        # Build the WHERE clause if there are any conditions
        where_clause = ''
        if conditions:
            where_clause = ' WHERE ' + ' AND '.join(conditions)

        # Form the full query with all clauses
        query = select_clause + left_join_clause + where_clause

        # Execute the query with the parameters
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Construct a list of spot dictionaries
        spots = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
       
        print(f"Executing query: {query}")
        print(f"With parameters: {params}")

        # Optional: Print each spot's availability for debugging
        for spot in spots:
            print(f"ID: {spot['id']}, Available: {spot['available']}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    return spots



def get_next_available_date(conn, spot_id):
    # Fetch the latest booking's end date
    booking_row = conn.execute('SELECT end_date FROM bookings WHERE spot_id = ? ORDER BY end_date DESC LIMIT 1', (spot_id,)).fetchone()
    if booking_row:
        last_end_date = datetime.strptime(booking_row['end_date'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < last_end_date:
            return False, (last_end_date + timedelta(days=1)).strftime('%Y-%m-%d')
    return True, None

def initialize_db():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()

    # Create tables if not exists
    c.execute('''
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        type TEXT,
        price REAL,
        lat REAL,
        lng REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spot_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        FOREIGN KEY (spot_id) REFERENCES parking_spots(id)
    )
    ''')
    conn.commit()

    types = ['Standard', 'Electric', 'Handicap']

    # Insert random parking spots data
    spot_ids = []  # List to keep track of the spot IDs
    for _ in range(4000):
        lat, lng = random_coordinates()
        spot_type = random.choice(types)
        c.execute('''
            INSERT INTO parking_spots (location, type, price, lat, lng) VALUES (?, ?, ?, ?, ?)
        ''', (
            'Random Dusseldorf Location', spot_type, random.uniform(1, 10), lat, lng
        ))
        spot_ids.append(c.lastrowid)  # Append the ID of the newly created spot

    conn.commit()

    # Randomly select 20% of the spot IDs to make them unavailable
    unavailable_spot_ids = random.sample(spot_ids, k=int(len(spot_ids) * 0.20))

    # Insert random bookings data for the selected spots to make them unavailable
    for spot_id in unavailable_spot_ids:
        start_date = datetime.now() + timedelta(days=random.randint(0, 3))
        end_date = start_date + timedelta(hours=24) if random.choice([True, False]) else start_date + timedelta(days=random.randint(1, 14))
        c.execute('''
            INSERT INTO bookings (spot_id, start_date, end_date) VALUES (?, ?, ?)
        ''', (
            spot_id, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')
        ))

    conn.commit()
    conn.close()

    print("Database initialized and random data added.")


if __name__ == '__main__':
    initialize_db()

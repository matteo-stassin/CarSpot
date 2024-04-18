import sqlite3
import random
from datetime import datetime, timedelta

def get_filtered_parking_spots(conn, spot_type, max_price, start_date, end_date):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    query = '''
        SELECT ps.*, (b.end_date IS NULL OR b.end_date < ?) AS available
        FROM parking_spots ps
        LEFT JOIN bookings b ON ps.id = b.spot_id AND b.end_date >= ?
        WHERE ps.price <= ? AND (ps.type = ? OR ? = 'All')
    '''
    params = [now, now, max_price, spot_type, spot_type]


    cursor.execute(query, params)
    spots = cursor.fetchall()
    return spots



def get_next_available_date(conn, spot_id):
    # Fetch the latest booking's end date
    booking_row = conn.execute('SELECT end_date FROM bookings WHERE spot_id = ? ORDER BY end_date DESC LIMIT 1', (spot_id,)).fetchone()
    if booking_row:
        last_end_date = datetime.strptime(booking_row['end_date'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < last_end_date:
            return False, (last_end_date + timedelta(days=1)).strftime('%Y-%m-%d')
    return True, None

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
        lng REAL,
        available INTEGER,
        short_term BOOLEAN,
        long_term BOOLEAN
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
    for _ in range(100):
        lat, lng = random_coordinates()
        spot_type = random.choice(types)
        c.execute('''
        INSERT INTO parking_spots (location, type, price, lat, lng, available) VALUES (
            ?, ?, ?, ?, ?, ?
        )
        ''', (
            'Random Düsseldorf Location', spot_type, random.uniform(1, 10), lat, lng, 1  # Assuming all spots are initially available
        ))

    conn.commit()

    # Insert random bookings data
    for i in range(1, 21):  # Assuming IDs 1 through 20 for spots
        start_date = datetime.now() + timedelta(days=random.randint(0, 3))
        end_date = start_date + timedelta(hours=24) if random.choice([True, False]) else start_date + timedelta(days=random.randint(1, 14))
        c.execute('''
        INSERT INTO bookings (spot_id, start_date, end_date) VALUES (?, ?, ?)
        ''', (
            i, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')
        ))

    conn.commit()
    conn.close()

    print("Database initialized and random data added.")

if __name__ == '__main__':
    initialize_db()
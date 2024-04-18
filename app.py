from flask import Flask, render_template, request, redirect, url_for, jsonify, g
from init_db import get_filtered_parking_spots, initialize_db, get_next_available_date, get_minimum_price, get_maximum_price
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)


def get_fontawesome_class(spot_type):
    return {
        'standard': 'fas fa-car',
        'electric': 'fas fa-charging-station',
        'handicap': 'fas fa-wheelchair'
    }.get(spot_type.lower(), 'fas fa-parking')  # Include the 'fas' prefix for default


app.jinja_env.globals.update(get_fontawesome_class=get_fontawesome_class)

def get_db_connection():
    conn = sqlite3.connect('parking.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return conn

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/map')
def show_map():
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM parking_spots')
    spots = [dict(row) for row in cursor.fetchall()]  # Convert rows to dictionaries here
    min_price = get_minimum_price(conn)  # This should be done before closing the connection.
    max_price = get_maximum_price(conn)
    conn.close()
    return render_template('map.html', parking_spots=spots, min_price=min_price, max_price=max_price)



@app.route('/api/filter_parking_spots', methods=['POST'])
def filter_parking_spots():
    filters = request.json
    conn = get_db_connection()
    filtered_spots = get_filtered_parking_spots(
        conn, 
        filters['type'], 
        filters['price'], 
        filters['startDate'], 
        filters['endDate'], 
    )
    conn.close()
    return jsonify(filteredSpots=[dict(row) for row in filtered_spots])


@app.route('/book/<int:spot_id>', methods=['GET'])
def book(spot_id):
    conn = get_db_connection()
    spot_row = conn.execute('SELECT id, location, type, price, available, short_term, long_term FROM parking_spots WHERE id = ?', (spot_id,)).fetchone()
    
    if not spot_row:
        return "Spot not found", 404

    # Convert sqlite3.Row to dict and format price
    spot_details = {key: spot_row[key] for key in spot_row.keys()}
    spot_details['price'] = "{:.2f}".format(spot_details['price'])

    # Check for booking details and next available date
    available, next_available_date = get_next_available_date(conn, spot_id)
    conn.close()

    # Format dates to pass to the template
    now = datetime.now()
    default_end_date = now + timedelta(hours=24)
    formatted_default_start_date = now.strftime('%Y-%m-%d')
    formatted_default_end_date = default_end_date.strftime('%Y-%m-%d')
    formatted_max_date = (now + timedelta(days=3)).strftime('%Y-%m-%d')
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    return render_template(
        'book.html',
        spot=spot_details,
        available=available,
        default_start_date=formatted_default_start_date,
        default_end_date=formatted_default_end_date,
        max_date=formatted_max_date,
        next_available_date=next_available_date, 
        start_date=start_date, 
        end_date=end_date
    )

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    spot_id = request.form.get('spot_id')  # Use .get() to avoid KeyError if not present
    booking_type = request.form.get('booking_type')
    
    # Debug: Log the received form data
    print('Received spot_id:', spot_id)
    print('Received booking_type:', booking_type)

    # You would implement the booking logic here, including calculating the price
    # ...

    # For now, just redirect to the map to see if the logging works
    return redirect(url_for('show_map'))


initialize_db()

if __name__ == '__main__':
    app.run(debug=True)

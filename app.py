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

def get_spot_details(spot_id):
    """
    Retrieve the details of a parking spot from the database.
    :param spot_id: The ID of the parking spot to retrieve.
    :return: A dictionary containing the details of the parking spot.
    """
    conn = get_db_connection()
    try:
        # Fetch the spot details from the database
        spot_row = conn.execute('SELECT id, location, type, price, lat, lng FROM parking_spots WHERE id = ?', (spot_id,)).fetchone()
        if spot_row:
            # Convert the row to a dictionary
            spot_details = {key: spot_row[key] for key in spot_row.keys()}
            return spot_details
        else:
            # If no spot is found, return None or raise an exception as needed
            return None
    except Exception as e:
        # Handle any exceptions, such as database errors
        print(f"An error occurred while fetching spot details: {e}")
        return None
    finally:
        # Ensure the database connection is closed
        conn.close()


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
    today = datetime.now().strftime('%Y-%m-%d')
    start_of_day = f"{today} 00:00:00"
    end_of_day = f"{today} 23:59:59"

    # Get minimum and maximum price from the database
    min_price = get_minimum_price(conn)
    max_price = get_maximum_price(conn)

    default_filters = {
        'type': 'All',
        'price': 'No Max',
        'startDate': start_of_day,
        'endDate': end_of_day
    }

    spots_with_availability = get_filtered_parking_spots(
        conn,
        default_filters['type'],
        default_filters['price'],
        default_filters['startDate'],
        default_filters['endDate']
    )
    
    conn.close()

    # Pass the min_price and max_price to the template
    return render_template(
        'map.html',
        parking_spots=spots_with_availability,
        min_price=min_price,
        max_price=max_price,
        today=today
    )




# Corrected function without double jsonify
@app.route('/api/filter_parking_spots', methods=['POST'])
def filter_parking_spots():
    print("filter_parking_spots route called")  # Debug print
    filters = request.json
    conn = get_db_connection()
    only_available = filters.get('onlyAvailable', False)
    filtered_spots = get_filtered_parking_spots(
        conn,
        filters['type'],
        filters['price'],
        filters['startDate'],
        filters['endDate'],
        only_available
    )
    print(f"onlyAvailable filter received: {only_available}")  # Debug print
    print(f"Filters received: {filters}")  # Debug print
    conn.close()
    print("Sending filtered spots:", filtered_spots)

    return jsonify(filteredSpots=[dict(spot) for spot in filtered_spots])



@app.route('/book/<int:spot_id>', methods=['GET'])
def book(spot_id):
    conn = get_db_connection()
    spot_row = conn.execute('SELECT id, location, type, price FROM parking_spots WHERE id = ?', (spot_id,)).fetchone()
    
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
    today = datetime.today().strftime('%Y-%m-%d')
    default_end_date = now + timedelta(hours=24)
    formatted_default_start_date = now.strftime('%Y-%m-%d')
    formatted_default_end_date = default_end_date.strftime('%Y-%m-%d')
    formatted_max_date = (now + timedelta(days=3)).strftime('%Y-%m-%d')
    start_date = request.args.get('start_date', formatted_default_start_date)
    end_date = request.args.get('end_date', formatted_default_end_date)
    
        # You would need to calculate the minimum end date in Python
    if not available:
        min_end_date = datetime.strptime(next_available_date, '%Y-%m-%d') + timedelta(days=1)
    else:
        min_end_date = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=1)
    
    formatted_min_end_date = min_end_date.strftime('%Y-%m-%d')
    

    conn.close()

    return render_template(
        'book.html',
        spot=spot_details,
        available=available,
        today=today,
        default_start_date=formatted_default_start_date,
        default_end_date=formatted_default_end_date,
        min_end_date=formatted_min_end_date,
        max_date=formatted_max_date,
        next_available_date=next_available_date, 
        start_date=start_date,  
        end_date=end_date  
    )

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    # Get the form data
    spot_id = request.form.get('spot_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    # Perform your booking logic here, like saving the booking to the database.
    # ...

    # Assuming the booking was successful, redirect to the confirmation page.
    return redirect(url_for('confirmation', spot_id=spot_id, start_date=start_date, end_date=end_date))

@app.route('/confirmation')
def confirmation():
    spot_id = request.args.get('spot_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    spot_details = get_spot_details(spot_id)

    if spot_details:
        # Include 'lat' and 'lng' in the 'booking_details'
        booking_details = {
            'spot_id': spot_id,
            'start_date': start_date,
            'end_date': end_date,
            'type': spot_details['type'],
            'icon_class': get_fontawesome_class(spot_details['type']),
            'location': spot_details['location'],
            'price': spot_details['price'],
            'lat': spot_details['lat'],  # Add this line
            'lng': spot_details['lng'],  # And this line
        }

        return render_template('confirmation.html', booking=booking_details)
    else:
        return "Spot details not found for ID: {}".format(spot_id), 404



initialize_db()

if __name__ == '__main__':
    app.run(debug=True)

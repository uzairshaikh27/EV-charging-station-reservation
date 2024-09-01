from flask import Flask, jsonify, request, session
import requests
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mysqldb import MySQL
from datetime import datetime
from bcrypt import hashpw, gensalt,checkpw
from flask import render_template


app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)
bcrypt = Bcrypt(app)

# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '9759856474@Uz'
app.config['MYSQL_DB'] = 'ev_reservation'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
# def init_db():
#     connection = mysql.connection
#     cursor = connection.cursor()
#     for result in cursor.execute(create_tables_sql, multi=True):
#         pass
#     cursor.close()

OPENCHARGEMAP_API_KEY = 'fcb56927-55f7-42ec-b5bc-0271d75d34cd'

@app.route('/')
def index():
        return render_template('login.html')

@app.route('/stations')
def stations_page():
    return render_template('stations.html')


@app.route('/stations2', methods=['GET'])
def get_stations():
    search_query = request.args.get('search', '')

    try:
        cursor = mysql.connection.cursor()

        if search_query:
            search_query = f"%{search_query}%"
            cursor.execute('''
                SELECT * FROM stations2 
                WHERE address LIKE %s OR state LIKE %s OR pincode LIKE %s
            ''', (search_query, search_query, search_query))
        else:
            cursor.execute('SELECT * FROM stations2')

        stations = cursor.fetchall()
        cursor.close()

        return jsonify(stations)
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'error': 'Database operation failed', 'details': str(err)}), 500


@app.route('/store_stations', methods=['GET'])
def store_stations():
    url = f'https://api.openchargemap.io/v3/poi/?output=json&countrycode=IN&maxresults=100&compact=true&verbose=false&key={OPENCHARGEMAP_API_KEY}'
    response = requests.get(url)
    stations2 = response.json()

    try:
        cursor = mysql.connection.cursor()

        for station in stations2:
            station_id = station['ID']
            address_info = station['AddressInfo']
            name = address_info['Title']
            address = address_info.get('AddressLine1', '')
            state = address_info.get('StateOrProvince', '')
            pincode = address_info.get('Postcode', '')
            latitude = address_info.get('Latitude', 0)
            longitude = address_info.get('Longitude', 0)
            available_slots = 10  # Placeholder for available slots
            total_slots = 10     # Placeholder for total slots

            cursor.execute('''
                INSERT INTO stations2 (id, name, address, state, pincode, latitude, longitude, available_slots, total_slots)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name), address = VALUES(address), state = VALUES(state), pincode = VALUES(pincode),
                latitude = VALUES(latitude), longitude = VALUES(longitude), available_slots = VALUES(available_slots), total_slots = VALUES(total_slots)
            ''', (station_id, name, address, state, pincode, latitude, longitude, available_slots, total_slots))

        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Stations stored successfully'})
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'error': 'Database operation failed', 'details': str(err)}), 500

@app.route('/reservations', methods=['POST'])
def make_reservation():
    data = request.json

    try:
        user_name = data['user_name']
        user_contact = data['user_contact']
        reservation_time = datetime.strptime(data['reservation_time'], '%Y-%m-%d %H:%M')
        station_id = data['station_id']
    except KeyError as e:
        return jsonify({'error': f'Missing data: {e}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {e}'}), 400

    try:
        cursor = mysql.connection.cursor()
        
        # Check if the station_id exists and has available slots
        cursor.execute('SELECT available_slots FROM stations2 WHERE id = %s AND available_slots > 0', (station_id,))
        station = cursor.fetchone()
        if station is None:
            return jsonify({'error': 'Station ID does not exist or no available slots'}), 400

        cursor.execute('''
            INSERT INTO reservations (user_name, user_contact, reservation_time, station_id)
            VALUES (%s, %s, %s, %s)
        ''', (user_name, user_contact, reservation_time, station_id))

        cursor.execute('''
            UPDATE stations2
            SET available_slots = available_slots - 1
            WHERE id = %s
        ''', (station_id,))

        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Reservation made successfully'})
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'error': 'Database operation failed', 'details': str(err)}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data['username']
        email = data['email']
        mobile = data['mobile']
        password = data['password']
        hashed_password = hashpw(password.encode('utf-8'), gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, mobile, password)
            VALUES (%s, %s, %s, %s)
        ''', (username, email, mobile, hashed_password))

        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        print(f"Error: {e}")  # Print error to console
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()

        
        if checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
    
            session['user_id'] = user['id']
            return jsonify({'user_id': user['id']})
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"Error: {e}")  # Print error to console
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)



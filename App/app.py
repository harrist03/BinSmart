from flask import Flask, render_template, redirect, url_for, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import requests
from functools import wraps
from db import db, get_or_create_user, User, Bin, BinReading
from pubnub_auth import generate_token

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("MYSQL_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Configure OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.route("/")
def index():
    user = session.get('user')
    return render_template("index.html", user=user)

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    user = get_or_create_user(
        google_id=user_info['sub'],
        email=user_info['email'],
        username=user_info['name']
    )

    session['user'] = {
        'id': user.id,
        'google_id': user_info['sub'],
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info.get('picture'),
        'is_admin': user.is_admin
    }

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Decorators (login_required and admin_required)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for("unauthorized"))
        
        user = session.get('user')
        db_user = User.query.get(user['id'])
        if db_user:
            session['user']['is_admin'] = db_user.is_admin

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if not user:
            return redirect(url_for('unauthorized'))
        
        if not user.get('is_admin'):
            return redirect(url_for('forbidden'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html")

@app.route("/forbidden")
def forbidden():
    return render_template("forbidden.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = session.get('user')
    user_id = f"user-{user['id']}"

    # Generate token based on user role (admins get read-write everywhere)
    access_type = "grant_read_write" if user.get('is_admin') else "grant_read"
    pubnub_token = generate_token(user_id, access_type, ttl=60)

    return render_template(
        "dashboard.html",
        user=user,
        pubnub_token=pubnub_token,
        pubnub_subscribe_key=os.getenv("PUBNUB_SUBSCRIBE_KEY"),
        pubnub_publish_key=os.getenv("PUBNUB_PUBLISH_KEY"),
        pubnub_channel=os.getenv("PUBNUB_CHANNEL")
    )   

@app.route("/admin_panel")
@login_required
@admin_required
def admin_panel():
    user = session.get('user')
    users = User.query.all()

    return render_template(
        "admin_panel.html",
        user=user,
        users=users
    )

@app.route("/api/bins")
@login_required
def get_bins():
    bins = Bin.query.all()
    bins_data = []

    for bin in bins:
        latest_reading = bin.get_latest_reading()

        bins_data.append({
            'id': bin.id,
            'name': bin.name,
            'latitude': bin.latitude,
            'longitude': bin.longitude,
            'address': bin.address,
            'capacity': bin.capacity,
            'is_full': bin.is_full,
            'fill_percentage': latest_reading.fill_percentage if latest_reading else 0,
            'fill_level': latest_reading.fill_level if latest_reading else 0,
            'distance': latest_reading.distance if latest_reading else bin.capacity
        })

    return jsonify(bins_data)

@app.route("/api/sensor/reading", methods=['POST'])
@login_required
def save_sensor_reading():
    try:
        data = request.json

        # Validate data
        if not data.get('bin_id') or data.get('distance') is None:
            return jsonify({'error': 'Missing bin_id or distance'}), 400
        
        # Validate bin exists
        bin = Bin.query.get(data['bin_id'])
        if not bin:
            return jsonify({'error': 'Invalid bin_id'}), 400
        
        # Validate distance is reasonable
        if data['distance'] < 0 or data['distance'] > bin.capacity * 1.2:
            return jsonify({'error': 'Invalid distance reading'}), 400
        
        # Create new reading
        reading = BinReading(
            bin_id=data['bin_id'],
            distance=data['distance']
        )
        db.session.add(reading)

        bin.is_full = data['distance'] <= 5

        db.session.commit()

        print(f"Saved reading: {bin.name}, distance: {data['distance']}cm")

        return jsonify({
            'success': True,
            'message': 'Reading saved',
            'fill_percentage': reading.fill_percentage
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error saving reading: {e}")
        return jsonify({'error': str(e)}), 500
    

@app.route("/api/token/refresh", methods=["POST"])
@login_required
def refresh_pubnub_token():
    user = session.get('user')
    user_id = f"user-{user['id']}"

    access_type = "grant_read_write" if user.get('is_admin') else "grant_read"

    new_token = generate_token(user_id, access_type, ttl=60)

    return jsonify({'token': new_token})

@app.route("/api/route/calculate", methods=['POST'])
@login_required
def calculate_route():
    try:
        data = request.json
        bin_ids = data.get('bin_ids')
        origin = data.get('origin')

        # Validate bin ids in database
        bins = Bin.query.filter(Bin.id.in_(bin_ids)).all()

        if len(bins) == 0:
            return jsonify({
                'success': False,
                'message': 'No valid bins found with provided IDs'
            }), 404

        # Extract locations for each bin from database
        waypoints = [f"{bin.latitude},{bin.longitude}" for bin in bins[:-1]]
        last_bin = bins[-1]

        bins_metadata = []
        for bin in bins:
            latest_reading = bin.get_latest_reading()
            bins_metadata.append({
                'id': bin.id,
                'name': bin.name,
                'location': {'lat': bin.latitude, 'lng': bin.longitude},
                'address': bin.address,
                'fill_percentage': latest_reading.fill_percentage
            })

        # Call Google Directions API
        api_key = os.getenv("GOOGLE_MAPS_BACKEND_API_KEY")
        base_url = "https://maps.googleapis.com/maps/api/directions/json"

        params = {
            'origin': f"{origin['lat']},{origin['lng']}",
            'destination': f"{last_bin.latitude},{last_bin.longitude}",
            'mode': 'driving',
            'key': api_key
        }

        if len(waypoints) > 0:
            params['waypoints'] = 'optimize:true|' + '|'.join(waypoints) 

        response = requests.get(base_url, params=params)
        directions_data = response.json()

        # Google API error handling
        if directions_data.get('status') != 'OK':
            return jsonify({
                'success': False,
                'message': f"Google Directions API error: {directions_data.get('status')}"
            }), 400
        
        # Extract route data
        route = directions_data['routes'][0]
        waypoint_order = route.get('waypoint_order', [])

        # Reorder bins based on Google's optimization
        if len(waypoint_order) > 0:
            optimized_bins = [bins_metadata[i] for i in waypoint_order]
            # Add last bin at the end
            optimized_bins.append(bins_metadata[-1])
        else:
            # only 1 bin (origin -> destination)
            optimized_bins = bins_metadata

        # Calculate total distance and duration
        total_distance = 0
        total_duration = 0
        for leg in route['legs']:
            total_distance += leg['distance']['value']
            total_duration += leg['duration']['value']

        return jsonify({
            'success': True,
            'route': {
                'polyline': route['overview_polyline']['points'],
                'bounds': route['bounds'],
                'optimized_bins': optimized_bins,
                'total_distance_km': round(total_distance / 1000, 2),
                'total_duration_min': round(total_duration / 60, 1)
            }
        })
    except Exception as e:
        print(f"Error calculating route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
        }), 500
    
@app.route("/api/users/<int:user_id>/admin", methods=["PUT"])
@login_required
@admin_required
def update_admin_status(user_id):
    try:
        current_user = session.get('user')

        if current_user['id'] == user_id:
            return jsonify({'success': False, 'message': 'You cannot modify your own admin status'}), 403
        
        data = request.get_json()
        is_admin = data.get('is_admin')

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404
        
        user.is_admin = is_admin
        db.session.commit()

        return jsonify({'success': True, 'message': f'User {user.id} admin status has been updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating admin status:  {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
from functools import wraps
from db import db, get_or_create_user
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

    # generate read-only token for regular users
    pubnub_token = generate_token(user_id, "grant_read", ttl=60)

    return render_template(
        "dashboard.html",
        user=user,
        pubnub_token=pubnub_token,
        pubnub_subscribe_key=os.getenv("PUBNUB_SUBSCRIBE_KEY"),
        pubnub_channel=os.getenv("PUBNUB_CHANNEL")
    )   

@app.route("/admin_panel")
@login_required
@admin_required
def admin_panel():
    user = session.get('user')
    user_id = f"admin-{user['id']}"

    # Generate read/write token for admins
    pubnub_token = generate_token(user_id, "grant_read_write", ttl=60)

    return render_template(
        "admin.html",
        user=user,
        pubnub_token=pubnub_token,
        pubnub_subscribe_key=os.getenv("PUBNUB_SUBSCRIBE_KEY"),
        pubnub_publish_key=os.getenv("PUBNUB_PUBLISH_KEY"),
        pubnub_channel=os.getenv("PUBNUB_CHANNEL")
    )


if __name__ == '__main__':
    app.run(debug=True)
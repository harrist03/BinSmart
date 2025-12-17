from flask import Flask, render_template, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

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

    session['user'] = {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info.get('picture')
    }

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for("unauthorized"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")   

if __name__ == '__main__':
    app.run(debug=True)
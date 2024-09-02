from flask import Flask, request, jsonify, render_template
from google.oauth2 import id_token
from google.auth.transport import requests
from oauthlib.oauth2 import WebApplicationClient
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import sqlite3
import requests
import datetime
import os

# Internal imports
from db import init_db_command
from user import User

# Ensure you set your client ID here
CLIENT_ID = '496812288990-o702g9h779lv2l3d2dae25rj7rcr3978.apps.googleusercontent.com'
CLIENT_SECRET = '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'
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

def auth_user(user_id, email):
    # Create a user in your db with the information provided
    # by Google
    user = User(id_=user_id, name="who", email=email, profile="pic")

    # Doesn't exist? Add it to the database.
    if not User.get(user_id):
        User.create(user_id, "who", users_email, "pic")

    # Begin user session by logging the user in
    login_user(user)

@app.route('/auth/google', methods=['POST'])
def auth_google():
    data = request.get_json()
    id_token_str = data.get('id_token')

    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(id_token_str, requests.Request(), CLIENT_ID)
        
        # Extract user information
        user_id = id_info['sub']
        email = id_info['email']
        
        # You can add logic here to handle user info, e.g., saving to a database
        auth_user(user_id,email)

        return jsonify({'message': 'User authenticated', 'user_id': user_id, 'email': email})

    except ValueError as e:
        # Invalid token
        return jsonify({'error': 'Invalid token', 'details': str(e)}), 400

@app.route("/")
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        dummy_times = [
            datetime.datetime(2018, 1, 1, 10, 0, 0),
            datetime.datetime(2018, 1, 2, 10, 30, 0),
            datetime.datetime(2018, 1, 3, 11, 0, 0),
        ]
        return render_template("index.html", times=dummy_times)

@app.route("/home")
@login_required
def home():
    return render_template("home.html", who=current_user.email)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("/"))

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

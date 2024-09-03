from flask import Flask, request, jsonify, render_template, redirect, session
from firestore_session import FirestoreSessionInterface
from google.oauth2 import id_token
from google.auth.transport import requests
from oauthlib.oauth2 import WebApplicationClient
from PIL import Image, ImageOps
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
) 

import datetime
import os
import zipfile
import hashlib
from flask_cors import CORS
from google.cloud import storage
import os
import replicate

# Internal imports
from user import User

# Ensure you set your client ID here
CLIENT_ID = '496812288990-o702g9h779lv2l3d2dae25rj7rcr3978.apps.googleusercontent.com'
CLIENT_SECRET = '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'
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
UPLOAD_FOLDER = '/tmp/uploads/'
PROCESSED_FOLDER = '/tmp/processed/'
ZIP_FOLDER = '/tmp/zipped/'
REPLICATE_USER = "scottspace"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ZIP_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Initialize the GCS client
storage_client = storage.Client()
bucket_name = "neurolens"

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Initialize Firebase session interface
# Replace 'your-firebase-database-url' and 'serviceAccountKey.json' with your actual values
app.session_interface = FirestoreSessionInterface()

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

print("Main.py 1")

def auth_user(user_id, name, email, profile_pic):
    # Create a user in your db with the information provided
    # by Google
    user = User(id_=user_id, name=name, email=email, profile_pic=profile_pic)

    # Doesn't exist? Add it to the database.
    if not User.get(user_id):
        User.create(user_id, name, email, profile_pic)

    # Begin user session by logging the user in
    login_user(user)
    
    # remember userid
    session['user_id'] = user_id
    
    print("Logged in user")

@app.route('/auth/google', methods=['POST'])
def auth_google():
    print("***Auth/google")
    #print(request.headers)

    data = request.get_json()
    id_token_str = data.get('id_token')

    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(id_token_str, requests.Request(), CLIENT_ID)
        
        # Extract user information
        user_id = id_info['sub']
        email = id_info['email']
        name = id_info['name']
        pic = id_info['picture']
        print("Got google info")
        print(id_info)
        
        # You can add logic here to handle user info, e.g., saving to a database
        auth_user(user_id,name,email,pic)

        return jsonify({'message': 'User authenticated', 'user_id': user_id, 'email': email})

    except ValueError as e:
        # Invalid token
        return jsonify({'error': 'Invalid token', 'details': str(e)}), 400

@app.route("/")
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    if current_user.is_authenticated:
        return redirect("/home")
    else:
        return render_template("index.html")

@app.route("/home")
@login_required
def home():
    print("***Home")
    #print(request.headers)
    return render_template("home.html", email=current_user.email, name=current_user.name)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

def user_code(user):
    return hashlib.md5(user.email.encode()).hexdigest()

def zip_user_photos(userid):
    bucket = storage_client.bucket(bucket_name)
    zpath = zip_path(userid)
    
    # get a list of files in bucket
    blobs = storage_client.list_blobs(bucket_name, prefix=image_dir(userid), delimiter='/')
    
    # Zip the files
    udir = user_code(current_user)
    os.makedirs(ZIP_FOLDER+"/"+udir, exist_ok=True)
    local_zpath = os.path.join(ZIP_FOLDER, zpath)
    with zipfile.ZipFile(local_zpath, 'w') as zipf:
        count = 0
        for blob in blobs:
            count += 1
            file_path = os.path.join(UPLOAD_FOLDER, blob.name)
            print("Downloading", blob.name, "to", file_path)
            blob.download_to_filename(file_path)
            zipf.write(file_path, os.path.basename(file_path))
            os.remove(file_path)
    print(f"Created a zip with {count} files.")
    
    # # Upload the zip file to Google Cloud Storage
    print("Storing zip file {zpath}")
    blob = bucket.blob(zpath)
    blob.upload_from_filename(local_zpath)
    # cleanup
    os.remove(local_zpath)
    
@app.route("/photo_count")
def photo_count():
    if current_user.is_authenticated:
        count = user_photo_count(current_user.id)
        return jsonify({'photo_count': count})
    else:
        return jsonify({'photo_count': 69})

    
def user_photo_count(userid):
    pre = image_dir(userid)+"/"
    print(f"prefix is {pre} of {bucket_name}")
    #bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket_name, prefix=pre, delimiter='/')
    #blobs = bucket.list_blobs(prefix=image_dir(userid), delimiter='/')
    #blobs = bucket.list_blobs()
    count = 0
    for blob in blobs:
        count += 1
        print("got blob",blob.name)
    return count
    return sum(1 for _ in blobs)
    
@app.route("/my_data")
def my_data():
    user = User.get(current_user.id)
    return jsonify({'zip': user.photo_url, 'photo_count': user_photo_count(current_user.id)})

@app.route("/me")
def me():
    # Get the user's profile information
    try:
        user_info = id_token.verify_oauth2_token(request.cookies.get('session'), requests.Request(), CLIENT_ID)
    except:
        user_info = None
    return jsonify({'user': user_info, 'code': user_code(current_user)})
    
def zip_path(userid):
    user = User.get(userid)
    udir = user_code(user)
    return os.path.join(udir, "uploaded_files.zip")

def image_dir(userid):
    user = User.get(userid)
    udir = user_code(user)
    return os.path.join(udir, "images")

def image_path(userid, filename):
    user = User.get(userid)
    udir = user_code(user)
    return os.path.join(udir, "images", filename)

def thumb_path(userid, filename):
    user = User.get(userid)
    udir = user_code(user)
    return os.path.join(udir, "thumbs", filename)

def thumb_dir(userid):
    user = User.get(userid)
    udir = user_code(user)
    return os.path.join(udir, "thumbs")

@app.route('/zip/<userzip>')
def zip_user(userzip):
    userid = userzip.split(".")[0]
    bucket = storage_client.bucket(bucket_name)
    
    # see if zip file exists in bucket
    blob = bucket.blob(zip_path(userid))
    
    # see if blob exists
    if not blob.exists():
        zip_user_photos(userid)

    # return zip file contents
    print(f"Here are the zip contents of {blob.name}: [not]")

@app.route('/upload', methods=['POST'])
def upload_file():
    print("***Upload")
    #print(request.headers)
    if session.get('user_id') is not None:
        uid = session['user_id']
        print("User ID: "+uid)
    else:
        print("No user id")
    print("current user:")
    print(current_user)
    if 'filepond' in request.files:
        files = request.files.getlist('filepond')
        file_paths = []
        bucket = storage_client.bucket(bucket_name)
        zip_dir = user_code(current_user)

        # Save the uploaded images
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            processed_file = change_extension_to_png(file.filename)
            processed_thumb = "thumb_"+processed_file
            processed_path = os.path.join(PROCESSED_FOLDER, processed_file)
            local_thumb_path = os.path.join(PROCESSED_FOLDER, processed_thumb)
            file.save(file_path)
            print(f"Processing {file_path} to {processed_path}")
            resize_image_to_square(file_path, processed_path)
            print(f"Removing {file_path}")
            create_thumbnail(processed_path, local_thumb_path)
            os.remove(file_path)
            file_paths.append(processed_path)
            
            # Upload the processed file to Google Cloud Storage
            blob = bucket.blob(image_path(uid, processed_file))
            blob.upload_from_filename(processed_path)
            
            # Upload the thumbnail to Google Cloud Storage
            blob = bucket.blob(thumb_path(uid, processed_thumb))
            blob.upload_from_filename(local_thumb_path)

        # Cleanup temporary files
        for file_path in file_paths:
            os.remove(file_path)
        os.remove(local_thumb_path)

        # Return the public URL of the uploaded file
        uid = current_user.id
        public_url = f"https://neurolens.scott.ai/zip/{uid}"
        User.update_photo_url(uid, public_url)
        return jsonify({'message': 'Files uploaded and zipped successfully', 'url': public_url}), 200
    else:
        return jsonify({'message': 'No files uploaded'}), 400
    
def change_extension_to_png(file_path):
    # Split the file path into root and extension
    root, _ = os.path.splitext(file_path)
    
    # Create a new file path with the .png extension
    new_file_path = root + '.png'
    
    return new_file_path

def resize_image_to_square(input_image_path, output_image_path, size=1024):
    # Open the image file
    with Image.open(input_image_path) as img:
        # Ensure the image has an alpha channel for transparency
        img = img.convert("RGBA")
        
        # Resize the image while maintaining aspect ratio
        img.thumbnail((size, size), Image.LANCZOS)

        # Create a new square image with a transparent background
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        # Calculate the position to paste the resized image on the square canvas
        paste_position = ((size - img.width) // 2, (size - img.height) // 2)
        
        # Paste the resized image onto the center of the square canvas
        new_img.paste(img, paste_position, img)

        # Save the final image as PNG with transparency
        new_img.save(output_image_path, format='PNG')

def create_thumbnail(input_image_path, output_image_path, size=(228, 228)):
    # Open the image file
    with Image.open(input_image_path) as img:
        # Convert the image to RGBA mode to ensure it supports transparency
        img = img.convert("RGBA")

        # Create a thumbnail while maintaining the aspect ratio
        img.thumbnail(size, Image.LANCZOS)

        # Create a new blank image with a transparent background
        thumb = Image.new('RGBA', size, (0, 0, 0, 0))

        # Calculate the position to paste the thumbnail
        paste_position = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
        
        # Paste the thumbnail onto the center of the new transparent image
        thumb.paste(img, paste_position, img)

        # Save the final thumbnail as a PNG to retain transparency
        thumb.save(output_image_path, format='PNG')

def make_model(name):
    try:
         model = replicate.models.create(
                owner=REPLICATE_USER,
                name=name,
                visibility="public",
                hardware="gpu-a40-large"
         )
    except Exception as e:
        print(e)
    return f"{REPLICATE_USER}/{name}"

@app.route('/train')
@login_required
def train():
    code = user_code(current_user)
    model = make_model(f"flux-dev-lora-{code}")
    webhook = f"https://neurolens.scott.ai/train_complete/{current_user.id}"
    input_images = f"https://neurolens.scott.ai/zip/{current_user.id}.zip"
    print("webhook", webhook)
    print("input_images", input_images)
    print("model", model)
    return jsonify({'message': 'Training started', 'model': model})
    training = replicate.trainings.create(
    # You need to create a model on Replicate that will be the destination for the trained version.                        
        destination=model,
        version="ostris/flux-dev-lora-trainer:7f53f82066bcdfb1c549245a624019c26ca6e3c8034235cd4826425b61e77bec",
        webhook=webhook,
        input={
            "steps": 1000,
            "lora_rank": 16,
            "optimizer": "adamw8bit",
            "batch_size": 1,
            "resolution": "512,768,1024",
            "autocaption": True,
            "input_images": input_images,
            "trigger_word": "me:-)",
            "learning_rate": 0.0004
        },
    )
    User.update_training(current_user.id, training.urls())
    return jsonify({'message': 'Training started', 'urls': current_user.training_data})

@app.route('/train_complete/{userid}', methods=['POST'])
def train_complete(userid):
    User.update_model(userid, request.get_json())
    return jsonify({'message': 'Training complete'})

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

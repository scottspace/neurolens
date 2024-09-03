from flask import Flask, request, jsonify, render_template, redirect, session
from flask import stream_with_context, Response
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
import mimetypes

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

@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return redirect("/")

def user_code(user):
    return hashlib.md5(user.email.encode()).hexdigest()

def zip_user_photos(userid):
    bucket = storage_client.bucket(bucket_name)
    zpath = zip_path(userid)
    zuser = User.get(userid)
    
    # get a list of files in bucket
    pre = image_dir(userid)+"/"
    blobs = storage_client.list_blobs(bucket_name, prefix=pre, delimiter='/')
    
    # Zip the files
    udir = user_code(zuser)
    os.makedirs(ZIP_FOLDER+"/"+udir, exist_ok=True)
    local_zpath = os.path.join(ZIP_FOLDER, zpath)
    count = 0
    with zipfile.ZipFile(local_zpath, 'w') as zipf:
        for blob in blobs:
            count += 1
            file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(blob.name))
            print("Downloading", blob.name, "to", file_path)
            blob.download_to_filename(file_path)
            zipf.write(file_path, os.path.basename(file_path))
            silent_remove(file_path)
    print(f"Created a zip with {count} files.")
    
    # # Upload the zip file to Google Cloud Storage
    print("Storing zip file {zpath}")
    blob = bucket.blob(zpath)
    blob.upload_from_filename(local_zpath)
    # cleanup
    silent_remove(local_zpath)

    
@app.route("/photo_count")
@login_required
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
@login_required
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
    blob = bucket.blob(zip_path(userid))
    
    # see if blob exists, if it doesn't zip up photos
    if not blob.exists():
        zip_user_photos(userid)

    # return zip file contents
    blob = bucket.blob(zip_path(userid))
    content_type, _ = mimetypes.guess_type(blob.name)
    response = Response(generate_zip_stream(blob), content_type=content_type)
    response.headers['Content-Type'] = content_type
        
    return response, 200

def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

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
            create_square_thumbnail(file_path, local_thumb_path)
            print(f"Removing {file_path}")
            silent_remove(file_path)
            file_paths.append(processed_path)
            
            # Upload the processed file to Google Cloud Storage
            blob = bucket.blob(image_path(uid, processed_file))
            blob.upload_from_filename(processed_path)
            
            # Upload the thumbnail to Google Cloud Storage
            blob = bucket.blob(thumb_path(uid, processed_thumb))
            blob.upload_from_filename(local_thumb_path)

        # Cleanup temporary files
        for file_path in file_paths:
            silent_remove(file_path)
        silent_remove(local_thumb_path)

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
        
def create_square_thumbnail(input_image_path, output_image_path, size=228):
    """
    Create a square thumbnail of the specified size from the input image and save it to the output path.

    Args:
        input_image_path (str): Path to the input image file.
        output_image_path (str): Path where the thumbnail will be saved.
        size (int): The size (width and height) of the square thumbnail. Default is 228.
    """
    try:
        # Open the image
        with Image.open(input_image_path) as image:
            width, height = image.size
            
            # Determine the crop box for the largest square
            if width > height:  # Landscape
                left = (width - height) // 2
                crop_box = (left, 0, left + height, height)
            elif height > width:  # Portrait
                top = 0
                crop_box = (0, top, width, top + width)
            else:  # Square
                crop_box = (0, 0, width, height)

            # Crop the image to the largest square
            image = image.crop(crop_box)

            # Resize the cropped image to the desired size
            image = image.resize((size, size), Image.LANCZOS)

            # Save the thumbnail to the output path
            image.save(output_image_path, format='JPEG')

    except Exception as e:
        print(f"An error occurred: {e}")

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

# TODO only allow training if there are images, and a training isn't already in progress

def valid_model(user):
    m = user.model
    if m is not None and m.get('status', None) == 'success':
        return True
    return False

@app.route('/state')
@login_required
def state():
    updated = User.get(current_user.id)  # refresh
    if user_photo_count(updated.id) < 20:  
        ans = 'upload'
    elif valid_model(updated):
        ans = 'ready'
    elif updated.training_data is None:
        ans = 'submit'
    else:
        ans = 'training'
    return jsonify({'state': ans})

def get_train_info(training):
    base = training.urls
    base['id'] = training.id
    base['destination'] = training.destination
    base['created-at'] = training.created_at
    return base

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
    #return jsonify({'message': 'Training started', 'model': model})
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
    User.update_training(current_user.id,get_train_info(training))
    return jsonify({'message': 'Training started', 'id': training.id})

@app.route('/train_complete/<userid>', methods=['POST'])
def train_complete(userid):
    j = request.get_json()
    feedback_id = j.get('id', None)
    print(f"Training complete for job {feedback_id}!")
    u = User.get(userid)
    try:
        training_id = u.training_data.get('id', None)
        if training_id != feedback_id:
            print("Older training, ignoring.")
            return jsonify({'message': 'Training not active'})
        else:
            User.update_model(userid, j)
            return jsonify({'message': 'Training complete'})
    except:
        print("No training found, ignoring feedback.")
        return jsonify({'message': 'Training not found'})

@app.route('/clear')
@login_required
def clear():
    try:
        delete_blob(bucket_name, zip_path(current_user.id))
    except:
        pass
    return jsonify({'message': 'zip deleted'})

@app.route('/reset')
@login_required
def reset():
    # erase zip
    clear()
    
    # Delete all images and thumbnails
    blobs = storage_client.list_blobs(bucket_name, prefix=image_dir(current_user.id)+"/", delimiter='/')
    for blob in blobs:
        blob.delete()
    blobs = storage_client.list_blobs(bucket_name, prefix=thumb_dir(current_user.id)+"/", delimiter='/')
    for blob in blobs:
        blob.delete()
    return jsonify({'message': 'All images and thumbnails deleted'})

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    generation_match_precondition = None

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to delete is aborted if the object's
    # generation number does not match your precondition.
    blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
    generation_match_precondition = blob.generation

    blob.delete(if_generation_match=generation_match_precondition)

    print(f"Blob {blob_name} deleted.")
    
@app.route('/kill/<path:path>')
def kill(path):
    # first, delete the thumbnail this represents thumb_photo.png
    try:
        delete_blob(bucket_name, path)
    except:
        print("Thumbnail not found")
    
    # now delete the soruce image photo.png
    file = os.path.basename(path)
    parts = file.split("_")
    source = '_'.join(parts[1:])
    try:
        delete_blob(bucket_name, image_path(current_user.id, source))
    except:
        print("Source image not found")
    return redirect("/home")
    
#
## Photo Grid
#

def generate_image_stream(blob):
    """Generator that streams the image in chunks."""
    chunk_size = 1024 * 1024  # 1 MB per chunk
    with blob.open("rb") as image_file:
        while True:
            chunk = image_file.read(chunk_size)
            if not chunk:
                break
            yield chunk
            
def generate_zip_stream(blob):
    return generate_image_stream(blob)

def kill_photo(img,kill):
    base = """
    <div class="relative flex justify-center items-center">
    <img class="max-w-full rounded-lg" src="{}" alt="">
       <div class="absolute top-0 right-0 w-4 h-4">
         <a class="text-xl font-bold" href="{}">X</a>
    </div></div> 
    """
    return base.format(img,kill)

@app.route("/photo/<path:path>")
def photo(path):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(path)
    if blob.exists():
        content_type, _ = mimetypes.guess_type(blob.name)
        # Create a streaming response with the image data
        response = Response(generate_image_stream(blob), content_type=content_type)
        
        # Set cache headers for browser caching (e.g., cache for 1 week)
        response.headers['Cache-Control'] = 'public, max-age=604800'  # 1 week in seconds
        response.headers['Content-Type'] = content_type
        
        return response, 200
    else:
        return "No such photo", 404

@app.route("/grid")
@login_required
def photo_grid():
    user_id = current_user.id
    bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket_name, prefix=thumb_dir(user_id)+"/", delimiter='/')
    names = [blob.name for blob in blobs]
    images = [[f"/photo/{name}", f"/kill/{name}"] for name in names]
    out= "<div class='grid grid-cols-2 md:grid-cols-3 gap-4'>"
    for imgkill in images:
        img = imgkill[0]
        out += kill_photo(imgkill[0],imgkill[1])
    out += "</div>"
    return out

def replicate_model_name(user):
    return f"scottspace/flux-dev-lora-{user_code(user)}"

def genImage(prompt):
    return None
    model = replicate.models.get("ai-forever/kandinsky-2.2")
    version = model.versions.get("ea1addaab376f4dc227f5368bbd8eff901820fd1cc14ed8cad63b29249e9d463")
    prediction = replicate.predictions.create(
        version=version,
        input={"prompt":"Watercolor painting of an underwater submarine"},
        webhook="https://example.com/your-webhook",
        webhook_events_filter=["completed"]
    ) 

    output = replicate.run(
    "scottspace/flux-dev-lora-03c5b0ad5b66ca449de0c36954bfdb8f:75d0360ee8a63adfa39139bca6679f0c8e0fb1c29eb1782f0ca624728b24a84f",
    input={
        "model": "dev",
        "lora_scale": 1,
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "guidance_scale": 3.5,
        "output_quality": 80,
        "prompt_strength": 0.8,
        "extra_lora_scale": 0.8,
        "num_inference_steps": 28
    }
    )

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

from flask import Flask, request, jsonify, render_template, redirect, session
from flask import stream_with_context, Response, make_response, send_file
from firestore_session import FirestoreSessionInterface
from google.oauth2 import id_token
from google.auth.transport import requests
from oauthlib.oauth2 import WebApplicationClient
from datetime import datetime, timezone
from urllib.parse import urlparse
from tzlocal import get_localzone
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
import requests as webrequests
import uuid

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
    return jsonify({'message': 'User logged out', 'url': 'https://neurolens.scott.ai/'})

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
    print(f"User has {count} photos")
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
    local_tmp = os.path.join('/tmp', os.path.basename(blob.name))
    blob.download_to_filename(local_tmp)
    send_file(local_tmp, as_attachment=True)
    
    #content_type, _ = mimetypes.guess_type(blob.name)
    #response = Response(generate_zip_stream(blob), content_type=content_type)
    #response.headers['Content-Type'] = content_type

def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
    
def process_image_file(uid, bucket, file_path):
    # clean up an image stored locally at file_path and then
    # upload the 1024x1024 and thumb to cloud storage
    processed_file = change_extension_to_png(os.path.basename(file_path))
    processed_thumb = "thumb_"+processed_file
    processed_path = os.path.join(PROCESSED_FOLDER, processed_file)
    local_thumb_path = os.path.join(PROCESSED_FOLDER, processed_thumb)
    print(f"Processing {file_path} to {processed_path}")
    resize_image_to_square(file_path, processed_path)
    create_square_thumbnail(file_path, local_thumb_path)
    print(f"Removing {file_path}")
    silent_remove(file_path)
        
    print("Saving image to cloud")
    # Upload the processed file to Google Cloud Storage
    blob = bucket.blob(image_path(uid, processed_file))
    blob.upload_from_filename(processed_path)
            
    print("Saving thumbnail to cloud")
    # Upload the thumbnail to Google Cloud Storage
    blob = bucket.blob(thumb_path(uid, processed_thumb))
    blob.upload_from_filename(local_thumb_path)
    
    #cleanup
    print("Cleaning up")
    silent_remove(processed_path)
    silent_remove(local_thumb_path)

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
            file.save(file_path)
            process_image_file(current_user.id, bucket, file_path)

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
    #ans = 'ready' # testing TODO
    return nocache_json({'state': ans})

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
    print(j)
    u = User.get(userid)
    try:
        training_id = u.training_data.get('id', None)
        if training_id != feedback_id:
            print("Older training, ignoring.")
            return jsonify({'message': 'Training not active'})
        else:
            User.update_model(u.id, j)
            return jsonify({'message': 'Training complete'})
    except Exception as e:
        print(f"Error checking training, ignoring feedback.\n{e}")
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
    
    # now delete the source image photo.png
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

def kill_photo(img,kill,view):
    base = """
    <div class="relative flex justify-center items-center">
       <a href="{}" target="_blank">
        <img class="max-w-full rounded-lg" src="{}" alt="">
       </a>
       <div class="absolute top-0 right-0 w-4 h-4">
         <a class="text-xl font-bold" href="{}">X</a>
       </div>
    </div> 
    """
    return base.format(view,img,kill)

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
    
def photo_from_thumb(path):
    p1 = path.replace("thumbs","images")
    return p1.replace("thumb_","")

@app.route("/grid")
@login_required
def photo_grid():
    user_id = current_user.id
    bucket = storage_client.bucket(bucket_name)
    blobgen = storage_client.list_blobs(bucket_name, prefix=thumb_dir(user_id)+"/", delimiter='/')
    blobs = [_ for _ in blobgen]
    
    # Sort blobs by their updated time, in descending order (most recent first)
    blobs_sorted = sorted(blobs, key=lambda blob: blob.updated, reverse=True)

    names = [blob.name for blob in blobs_sorted]
    images = [[f"/photo/{name}", f"/kill/{name}", f"/photo/{photo_from_thumb(name)}"] for name in names]
    out= "<div class='grid grid-cols-2 md:grid-cols-3 gap-4'>"
    for imgkill in images:
        img = imgkill[0]
        out += kill_photo(imgkill[0],imgkill[1],imgkill[2])
    out += "</div>"
    return out

#
## Image generation
#

@app.route('/genImage', methods=['POST'])
@login_required
def gen_image_post():
    print("***Gen Image")
    #print(request.headers)

    data = request.get_json()
    print("Got json", data)
    job = genImage(current_user, data.get('prompt'))
    return jsonify({'message': 'Image generation started', 'job': job})

def latest_replicate_model_version(user):
    base_model = f"scottspace/flux-dev-lora-{user_code(user)}"
    model = replicate.models.get(base_model)
    versions = model.versions.list()
    # versions is a page object, which we sort in descending order by creation date 
    sorted(versions,key=lambda x: x.dict()['created_at']).reverse()
    return versions[0]
    
def genImage(user, prompt):
    print("Resettting status")
    user.image_job = str(uuid.uuid4())
    user.image_job_log = None
    user.image_job_status = "requested"
    user.image_job_output = None
    user.save()
    v = latest_replicate_model_version(user)
    print("Trying model version", v.id)
    prediction = replicate.predictions.create(
        version=latest_replicate_model_version(user),
        input={"prompt":str(prompt),
               "output_format": "png",
               "width": 1024,
               "height": 1024,
               "num_outputs": 1,
               "image_job": user.image_job},
        webhook="https://neurolens.scott.ai/image_update/"+user.id)
    user.image_job_status = prediction.status
    user.save()
    print("Started prediction", prediction)
    return user.image_job 

#
## Webhook for images
#

def nocache_json(j):
    response = make_response(jsonify(j))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# this is pinged frequently by the web ui
@app.route('/image_status')
@login_required
def image_status():
    user = User.get(current_user.id) #important to refresh!
    print("status for {}".format(user.email))
    return nocache_json({
        'status': user.image_job_status, 
        'job': user.image_job,
        'output': user.image_job_output,
        'log': user.image_job_log})

# replicate posts back here with updates on the image
@app.route("/image_update/<userid>", methods=['POST'])
def image_update(userid):
    try:
        info = request.get_json(silent=True)
        user = User.get(str(userid))
        print("webhook ",info)
        if info is None:
            print("No json")
            return jsonify({'error': 'no json'})
        user.image_job_status = info.get('status',None)
        imgs = get_images(info)
        if imgs:
            user.image_job_output = {'images': info.get('urls',None)}
            print("Images are ready", imgs)
            copy_images_locally(userid, imgs)
        user.save()
        return jsonify({'success': 0})
    except Exception as e:
        user.image_job_status = 'error'
        user.save()
        print("Image Hook Exception", e)
        return jsonify({'error': str(e)}) #TODO make this string json clean  

def copy_images_locally(userid, urls):
    # handle errors TODO
    bucket = storage_client.bucket(bucket_name)
    for url in urls:
        filename = unique_filename(url)
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        print("Downloading", url, "to", local_path)
        r = webrequests.get(url, stream=True)
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        process_image_file(userid, bucket, local_path)
        
def tz_now():
   n = datetime.now(timezone.utc)
   n = n.astimezone(get_localzone())
   return n

def get_extension(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    _, file_extension = os.path.splitext(filename)
    return file_extension

def unique_filename(url):
    md5 = hashlib.md5(url.encode()).hexdigest() 
    ext = get_extension(url)
    return "{}{}".format(md5,ext)

def sd_success(info):
    return info.get('status',None) in ['success','succeeded']

def sd_processing(info):
    return info.get('status',None) == 'processing'

def get_images(info):
    if sd_success(info):
        print("SD success: {}".format(info))
        all = info.get('output', None)
        if all and all is not None and len(all) > 0:
            if isinstance(all,str):
                # replicate may do this
                return [all]
            return all 
    return None

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

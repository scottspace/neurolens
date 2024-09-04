from flask_login import UserMixin
import firebase_admin
from firebase_admin import firestore, get_app

# Application Default credentials are automatically created.
try:
    # Try to get the default app
    app = get_app()
except ValueError:
    app = firebase_admin.initialize_app()
db = firestore.client()

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = str(id_)
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.photo_url = ""
        self.training_data = None  # indicates we are training
        self.model = None
        self.image_job = None
        self.image_job_status = None
        self.image_job_log = None
        self.image_job_output = None
        
    def __setattr__(self, name, value):
        # set a value and update our datbase too
        super().__setattr__(name, value)  # Call the parent class's __setattr__ to actually set the value
        doc_ref = db.collection("users").document(str(self.id))
        d = doc_ref.get().to_dict()
        if d.get(name, None) != value:
            print("Updating user with", name, value)
            doc_ref.update({name: value})
            
    def save(self):
        # save the user to the database
        data={'id': self.id, 
              'name': self.name, 
              'email': self.email, 
              'profile_pic': self.profile_pic, 
              'photo_url': self.photo_url, 
              'model': self.model, 
              'image_job': self.image_job,
              'image_job_status': self.image_job_status,
              'image_job_log': self.image_job_log,
              'image_job_output': self.image_job_output,
              'training_data': self.training_data}
        doc_ref = db.collection("users").document(str(self.id))
        d = doc_ref.get().to_dict()
        doc_ref.update(data)
        
    @staticmethod
    def get(user_id):
        doc_ref = db.collection("users").document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
          info = doc.to_dict()
          user = User(
              id_=info['id'], 
              name=info['name'], 
              email=info['email'], 
              profile_pic=info['profile_pic']
          )
          user.model = info.get('model', None)
          user.training_data = info.get('training_data', None)
          user.photo_url = info.get('photo_url', None)
          user.image_job = info.get('image_job', None)
          user.image_job_status = info.get('image_job_state', None)
          user.image_job_log = info.get('image_job_log', None)
          user.image_job_output = info.get('image_job_output', None)
          return user
        else:
            return None

    @staticmethod
    def create(id_, name, email, profile_pic):
        data={'id': id_, 
              'name': name, 
              'email': email, 
              'profile_pic': profile_pic, 
              'photo_url': None, 
              'model': None, 
              'image_job': None,
              'image_job_status': None,
              'image_job_log': None,
              'image_job_output': None,
              'training_data': None}
        db.collection("users").document(str(id_)).set(data)
        
    @staticmethod
    def update_photo_url(user_id, url):
        doc_ref = db.collection("users").document(str(user_id))
        doc_ref.update({'photo_url': url})

    @staticmethod
    def update_model(user_id, model_data):
        doc_ref = db.collection("users").document(str(user_id))
        doc_ref.update({'model': model_data, 'training_data': None})
    
    @staticmethod
    def update_training(user_id, training_data):
        doc_ref = db.collection("users").document(str(user_id))
        doc_ref.update({'training_data': training_data, 'model': None})
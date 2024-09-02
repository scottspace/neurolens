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
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.has_photos = False
        self.photo_url = ""

    @staticmethod
    def get(user_id):
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
          info = doc.to_dict()
          user = User(
              id_=info['id'], name=info['name'], email=info['email'], profile_pic=info['profile_pic']
          )
          return user
        else:
            return None

    @staticmethod
    def create(id_, name, email, profile_pic):
        data={'id': id_, 'name': name, 'email': email, 'profile_pic': profile_pic, 
              'has_photos': False, 'photo_url': ""}
        db.collection("users").document(id_).set(data)
        
    @staticmethod
    def update_photo_url(user_id, url):
        doc_ref = db.collection("users").document(user_id)
        doc_ref.update({'photo_url': url})

    @staticmethod
    def update_model(user_id, model_name):
        doc_ref = db.collection("users").document(user_id)
        doc_ref.update({'model': model_name})
    
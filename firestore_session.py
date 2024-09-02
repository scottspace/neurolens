# firestore_session.py
from flask.sessions import SessionInterface, SessionMixin
from datetime import datetime, timedelta, timezone
import pickle
import uuid
import firebase_admin

from firebase_admin import firestore, get_app

# Application Default credentials are automatically created.
try:
    # Try to get the default app
    app = get_app()
except ValueError:
    app = firebase_admin.initialize_app()
    
db = firestore.client()

class FirestoreSession(dict, SessionMixin):
    def __init__(self, initial=None, sid=None):
        super().__init__(initial or {})
        self.sid = sid
        self.modified = False

class FirestoreSessionInterface(SessionInterface):
    def __init__(self, client=None, collection_name='sessions'):
        self.client = db 
        self.collection_name = collection_name

    def generate_sid(self):
        return str(uuid.uuid4())
    
    def get_session(self, sid):
        doc_ref = self.client.collection(self.collection_name).document(sid)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print("Got session", data)
            return pickle.loads(data['data'])
        else:
            print(f"Can't find session {sid}")
        return None
    
    def request_session_id(self, request):
        try:
            return request.cookies.get('session') 
        except:
            return None

    def open_session(self, app, request):
        print("...open_session...")
        sid = self.request_session_id(request)
        print("session id", sid)
        print(request.headers)
        if sid:
            session_data = self.get_session(sid)
            if session_data:
                return FirestoreSession(session_data, sid=sid)
        sid = self.generate_sid()
        return FirestoreSession(sid=sid)

    def save_session(self, app, session, response):
        print("...save_session...")
        print("sid:", session.sid)
        doc_ref = self.client.collection(self.collection_name).document(session.sid)
        doc_ref.set({
            'data': pickle.dumps(dict(session)),
            'expires': datetime.now(timezone.utc) + timedelta(days=30)  # Adjust the expiration as needed
        })

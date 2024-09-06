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
        print("created new session")

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
            print("Got session")
            return pickle.loads(data['data'])
        if sid is None:
            print("No session id")
            return None
        return {}  # empty session data

    def request_session_id(self, request):
        try:
            #print("session request headers:", request.headers)
            #cookie = request.cookies.get('session') 
            cookie = request.headers.get('session')
            if cookie is None:
                cookie = request.args.get('s')
            print("Loooking for session: ", cookie)
            return cookie
        except:
            return None

    def open_session(self, app, request):
        print("...open_session...")
        sid = self.request_session_id(request)
        #print("session id", sid)
        if sid is not None:
            session_data = self.get_session(sid)
            if session_data:
                print("Found session data!")
                print(dict(session_data))
                return FirestoreSession(session_data, sid=sid)
            else:
                print("...no session data yet.")
                return FirestoreSession(sid=sid)
        print("Generating new session id")
        #sid = self.generate_sid()
        return FirestoreSession(sid=None)

    def save_session(self, app, session, response):
        print("...save_session...")
        print("...sid: ", session.sid)
        print(dict(session))
        #print("sid:", session.sid)]
        if session.sid is None:
            print("... ignored save, no session id")
            return
        doc_ref = self.client.collection(self.collection_name).document(session.sid)
        doc_ref.set({
            'data': pickle.dumps(dict(session)),
            'expires': datetime.now(timezone.utc) + timedelta(days=30)  # Adjust the expiration as needed
        })

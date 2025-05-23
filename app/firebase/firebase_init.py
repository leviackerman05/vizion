import os
import firebase_admin
from firebase_admin import credentials, firestore

# Build the absolute path to the JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # this is /app/firebase
json_path = os.path.join(BASE_DIR, "..", "text-to-anim-firebase-adminsdk-fbsvc-69810e8d63.json")
json_path = os.path.abspath(json_path)

cred = credentials.Certificate(json_path)
firebase_admin.initialize_app(cred)

db = firestore.client()
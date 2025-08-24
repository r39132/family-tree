from google.cloud import firestore
from .config import settings

def get_db():
    # Use named database if provided
    db = firestore.Client(project=settings.google_cloud_project, database=settings.firestore_database)
    return db

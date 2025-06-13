#fetch_data_by_id.py

from pymongo import MongoClient
from core.config import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client["valoov_ai_db"]
collection = db["user_qa"]

def fetch_data_by_id(document_id):
    data = collection.find_one({"_id": document_id})
    if not data:
        return None, None
    return data.get("eval_text"), data.get("pdf_text")
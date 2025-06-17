from pymongo import MongoClient
from core.config import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client["valoov"] 
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
def get_database():
    # Строка подключения к MongoDB Atlas
    uri = os.getenv('MONGO_YURI')
    client = MongoClient(uri)
    return client["my_database"]
import os
from pkgutil import get_data

from pymongo import MongoClient
from elasticsearch import Elasticsearch

from db.database import get_database

# Подключение к MongoDB
db = get_database()
resumes_collection = db["resumes"]
CLOUD_URL = os.getenv("ES_CLOUD_URL")
USERNAME = os.getenv("ES_USERNAME")
PASSWORD = os.getenv("ES_PASSWORD")
# Подключение к Elastic Cloud
es = Elasticsearch(CLOUD_URL, basic_auth=(USERNAME, PASSWORD))

# Индексация резюме
def index_resumes():
    for resume in resumes_collection.find():
        es.index(index="resumes", id=str(resume["_id"]), document=resume)
    print("Резюме проиндексированы.")

if __name__ == "__main__":
    index_resumes()
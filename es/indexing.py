import os
from pkgutil import get_data
from bson import ObjectId
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




def prepare_for_elasticsearch(data):
    """Рекурсивно обрабатывает данные для сериализации в JSON."""
    if isinstance(data, dict):
        return {key: prepare_for_elasticsearch(value) for key, value in data.items() if key != "_id"}
    elif isinstance(data, list):
        return [prepare_for_elasticsearch(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

def index_resumes():
    resumes = list(resumes_collection.find())
    for resume in resumes:
        # Извлекаем _id и конвертируем его в строку
        doc_id = str(resume["_id"])
        clean_resume = prepare_for_elasticsearch(resume)

        try:
            # Индексация документа с использованием doc_id в качестве идентификатора
            es.index(index="resumes", id=doc_id, document=clean_resume)
            print(f"Резюме {doc_id} успешно проиндексировано.")
        except Exception as e:
            print(f"Ошибка при индексации резюме {doc_id}: {e}")

if __name__ == "__main__":
    index_resumes()
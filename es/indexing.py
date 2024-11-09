import os
from pkgutil import get_data
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from elasticsearch import Elasticsearch

from db.database import get_database
from front.app import vacancies_collection

load_dotenv()
# Подключение к MongoDB
db = get_database()
resumes_collection = db["resumes"]
vacancies_collection_collection = db["vacancies"]
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


def index_vacancies():
    """Индексирует все вакансии из MongoDB в Elasticsearch."""
    try:
        # Получаем все вакансии из MongoDB
        vacancies = list(vacancies_collection.find())

        for vacancy in vacancies:
            # Преобразуем _id в строку и готовим данные для Elasticsearch
            doc_id = str(vacancy["_id"])
            clean_vacancy = prepare_for_elasticsearch(vacancy)

            # Индексация документа в Elasticsearch
            es.index(index="vacancies", id=doc_id, document=clean_vacancy)
            print(f"Вакансия {doc_id} успешно проиндексирована.")

        print("Все вакансии успешно проиндексированы.")

    except Exception as e:
        print(f"Ошибка при индексации: {e}")

if __name__ == "__main__":
    index_resumes()
    index_vacancies()
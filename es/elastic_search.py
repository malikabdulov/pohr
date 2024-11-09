import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
load_dotenv()
# URL вашего кластера и учетные данные
CLOUD_URL = os.getenv("ES_CLOUD_URL")
USERNAME = os.getenv("ES_USERNAME")
PASSWORD = os.getenv("ES_PASSWORD")

# Подключение к Elastic Cloud
es = Elasticsearch(CLOUD_URL, basic_auth=(USERNAME, PASSWORD))

# Проверка подключения
if es.ping():
    print("Подключение установлено!")
else:
    print("Ошибка подключения.")

# Пример поиска документов
query = {
    "query": {
        "match": {
            "skills": "Python"
        }
    }
}

response = es.search(index="resumes", body=query)
print(response)

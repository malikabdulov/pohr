from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import os
load_dotenv()
# Подключение к Elasticsearch
CLOUD_URL = os.getenv("ES_CLOUD_URL")
USERNAME = os.getenv("ES_USERNAME")
PASSWORD = os.getenv("ES_PASSWORD")

# Подключение к Elastic Cloud
es = Elasticsearch(CLOUD_URL, basic_auth=(USERNAME, PASSWORD))

def search_resumes(query):
    """Ищет резюме в Elasticsearch и выводит результаты в консоль."""
    try:
        response = es.search(index="resumes", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["full_name", "summary", "skills", "work_experience.position"]
                }
            }
        })

        # Извлекаем содержимое ответа
        response_body = response.body

        # Выводим весь ответ в формате JSON
        import json
        print(json.dumps(response_body, indent=2, ensure_ascii=False))

        # Альтернативный вывод: извлекаем только нужные поля
        print("\nРезультаты поиска:")
        for hit in response_body["hits"]["hits"]:
            source = hit["_source"]
            print(f"Имя: {source['full_name']}")
            print(f"Контакт: {source['contact_info']['phone']}, {source['contact_info']['email']}")
            print(f"Описание: {source['summary']}")
            print(f"Навыки: {', '.join(source['skills'])}")
            print("-" * 40)

    except Exception as e:
        print(f"Ошибка при поиске: {e}")

# Пример использования
if __name__ == "__main__":
    search_query = "Python"
    search_resumes(search_query)

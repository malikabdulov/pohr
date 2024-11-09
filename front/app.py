import os
from bson import ObjectId
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)
load_dotenv()
# Подключение к MongoDB
client = MongoClient(os.getenv('MONGO_YURI'))
db = client["my_database"]
vacancies_collection = db["vacancies"]
users_collection = db["resumes"]
es = Elasticsearch(os.getenv("ES_CLOUD_URL"), basic_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")))

def convert_object_id(data):
    """Конвертирует ObjectId в строку и обрабатывает вложенные данные."""
    if isinstance(data, dict):
        return {key: convert_object_id(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_object_id(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

def get_all_vacancies():
    return convert_object_id(list(vacancies_collection.find()))

def get_all_resumes():
    return convert_object_id(list(users_collection.find()))


@app.route('/')
def index():
    """Главная страница со списком вакансий."""
    try:
        vacancies = get_all_vacancies()
        return render_template('base.html', items=vacancies, data_type="vacancies", active_page="vacancies")
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/vacancies')
def show_vacancies():
    vacancies = list(vacancies_collection.find())
    return render_template('vacancies.html', items=vacancies)

@app.route('/resumes')
def show_resumes():
    """Отображает список резюме."""
    try:
        resumes = get_all_resumes()
        return render_template('resumes.html', items=resumes, data_type="resumes", active_page="resumes")
    except Exception as e:
        return render_template('error.html', error=str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os

from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for
import requests
from pymongo import MongoClient
from db.mongo_controller import add_vacancy, get_all_vacancies, get_all_resumes

app = Flask(__name__)

# Подключение к MongoDB
client = MongoClient(os.getenv('MONGO_YURI'))
db = client["my_database"]
vacancies_collection = db["vacancies"]
users_collection = db["resumes"]

@app.route('/')
def index():
    """Главная страница со списком вакансий по умолчанию."""
    try:
        vacancies = list(vacancies_collection.find())
        return render_template('index.html', items=vacancies, data_type="vacancies", active_page="vacancies")
    except Exception as e:
        return render_template('index.html', error=f"Ошибка при получении данных: {e}")

@app.route('/vacancies')
def show_vacancies():
    """Отображает список вакансий."""
    try:
        vacancies = list(vacancies_collection.find())
        return render_template('index.html', items=vacancies, data_type="vacancies", active_page="vacancies")
    except Exception as e:
        return render_template('index.html', error=f"Ошибка при получении данных: {e}")

@app.route('/delete_vacancy/<vacancy_id>', methods=['POST'])
def delete_vacancy(vacancy_id):
    """Удаляет вакансию по ID."""
    vacancies_collection.delete_one({"_id": ObjectId(vacancy_id)})
    return redirect(url_for('show_vacancies'))

@app.route('/edit_vacancy/<vacancy_id>', methods=['GET', 'POST'])
def edit_vacancy(vacancy_id):
    """Редактирует вакансию по ID."""
    if request.method == 'POST':
        title = request.form.get('title')
        experience = request.form.get('experience')
        skills = request.form.get('skills')
        education = request.form.get('education')

        vacancies_collection.update_one(
            {"_id": ObjectId(vacancy_id)},
            {"$set": {
                "title": title,
                "experience": experience,
                "skills": skills,
                "education": education
            }}
        )
        return redirect(url_for('show_vacancies'))

    vacancy = vacancies_collection.find_one({"_id": ObjectId(vacancy_id)})
    return render_template('edit_vacancy.html', vacancy=vacancy)

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

@app.route('/resumes')
def show_resumes():
    """Отображает список резюме."""
    try:
        resumes = list(users_collection.find())
        resumes = convert_object_id(resumes)
        return render_template('index.html', items=resumes, data_type="resumes", active_page="resumes")
    except Exception as e:
        return render_template('index.html', error=f"Ошибка при получении данных: {e}")

@app.route('/create_vacancy', methods=['GET', 'POST'])
def create_vacancy():
    """Страница для создания новой вакансии и сохранения в MongoDB."""
    if request.method == 'POST':
        title = request.form.get('title')
        experience = request.form.get('experience')
        skills = request.form.get('skills')
        education = request.form.get('education')

        if title and experience and skills and education:
            data = {
                'title': title,
                'experience': experience,
                'skills': skills,
                'education': education
            }
            try:
                add_vacancy(data)
                return render_template('create_vacancy.html', success="Вакансия успешно создана.")
            except Exception as e:
                return render_template('create_vacancy.html', error=f"Ошибка при сохранении: {e}")
        return render_template('create_vacancy.html', error="Заполните все поля.")
    return render_template('create_vacancy.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

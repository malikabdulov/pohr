from flask import Flask, render_template, request
import requests
from pymongo import MongoClient
from mongo_controller import add_vacancy, get_all_vacancies

app = Flask(__name__)

# URL вашего backend API
API_SEARCH_URL = "http://localhost:5000/api/search_candidates"

# Подключение к MongoDB


@app.route('/')
def index():
    """Главная страница со списком вакансий."""
    try:
        # Получаем все вакансии из коллекции
        vacancies = get_all_vacancies()
        return render_template('index.html', vacancies=vacancies)
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
    app.run(debug=True)

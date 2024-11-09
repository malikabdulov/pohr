# Добавляем необходимые импорты, если их еще нет
import json
import os
from bson import ObjectId
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from pymongo import MongoClient
from db.mongo_controller import find_vacancy_by_id, get_all_resumes, get_all_vacancies
from gpt.gpt import ai_rank_resumes

app = Flask(__name__)

# Подключение к MongoDB
client = MongoClient(os.getenv('MONGO_YURI'))
db = client["my_database"]
vacancies_collection = db["vacancies"]
users_collection = db["resumes"]
es = Elasticsearch(os.getenv("ES_CLOUD_URL"), basic_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")))


# Новый маршрут для получения деталей вакансии по ID
@app.route('/get_vacancy_details/<vacancy_id>', methods=['GET'])
def get_vacancy_details(vacancy_id):
    try:
        vacancy = vacancies_collection.find_one({"_id": ObjectId(vacancy_id)})
        if vacancy:
            return jsonify({
                "title": vacancy["title"],
                "experience": vacancy["experience"],
                "skills": vacancy["skills"],
                "education": vacancy["education"]
            })
        else:
            return jsonify({"error": "Vacancy not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Главная страница со списком вакансий по умолчанию
@app.route('/')
def index():
    try:
        vacancies = list(vacancies_collection.find())
        return render_template('index.html', items=vacancies, data_type="vacancies", active_page="vacancies")
    except Exception as e:
        return render_template('index.html', error=f"Ошибка при получении данных: {e}")

# Новый маршрут для страницы /ranging
@app.route('/ranging', methods=['GET', 'POST'])
def ranging():
    if request.method == 'POST':
        # Получение данных из формы
        vacancy_id = request.form.get('vacancy')  # Получаем выбранную вакансию
        technical_skills = float(request.form.get('technical_skills', 0)) / 100
        soft_skills = float(request.form.get('soft_skills', 0)) / 100
        cultural_fit = float(request.form.get('cultural_fit', 0)) / 100
        growth_potential = float(request.form.get('growth_potential', 0)) / 100

        # Вызов функции advanced_rank_resumes с весами
        results = advanced_rank_resumes(technical_skills, soft_skills, cultural_fit, growth_potential, vacancy_id)

        # Получаем список вакансий для выпадающего списка
        vacancies = get_all_vacancies()

        # Передаём результаты и веса в шаблон для отображения
        return render_template(
            'ranging.html',
            vacancies=vacancies,
            ranking_results=results,
            selected_vacancy=vacancy_id,
            weights={
                "technical_skills": technical_skills * 100,
                "soft_skills": soft_skills * 100,
                "cultural_fit": cultural_fit * 100,
                "growth_potential": growth_potential * 100
            }
        )

    # GET-запрос: отображаем страницу с выбором вакансий
    vacancies = get_all_vacancies()
    return render_template('ranging.html', vacancies=vacancies)

# Пример функции advanced_rank_resumes с параметрами для весов
def advanced_rank_resumes(technical_skills, soft_skills, cultural_fit, growth_potential, vacancy_id):
    # Здесь будет логика ранжирования резюме, используя vacancy_id и весовые коэффициенты
    # job_description = find_vacancy_by_id(vacancy_id=vacancy_id)

    # resumes = get_all_resumes()

    # weighting_factors = {
    #     "technical_skills": technical_skills,
    #     "soft_skills": soft_skills,
    #     "cultural_fit": cultural_fit,
    #     "growth_potential": growth_potential
    # }

    # ranked_resumes = ai_rank_resumes(job_description=job_description,
    #                 resumes=resumes,
    #                 weighting_factors=weighting_factors)
    
    # return ranked_resumes

    return [{"full_name":"Петров Алексей","relevance_score":92,"scores":{"technical_skills":95,"soft_skills":85,"cultural_fit":80,"growth_potential":90},"reasoning":{"technical_skills":"Обладает более чем 7 годами опыта в разработке сложных backend-решений, специализация в микросервисах и многопоточных приложениях.","soft_skills":"Демонстрирует менторство младшим разработчикам, что указывает на хорошие навыки коммуникации и лидерства.","cultural_fit":"Соответствие корпоративной культуре на уровне, готовность к переезду и обсуждению удаленной работы.","growth_potential":"Большой опыт и навыки позволяют предположить высокий потенциал для развития."},"missing_skills":[],"recommendations":""},{"full_name":"Кузнецова Анна","relevance_score":76,"scores":{"technical_skills":80,"soft_skills":80,"cultural_fit":70,"growth_potential":70},"reasoning":{"technical_skills":"Начальный уровень Java-разработчика с опытом стажировок в крупных компаниях, интерес к разработке веб-приложений и API.","soft_skills":"Демонстрирует умение работать в команде и обучаемость.","cultural_fit":"Небольшое расхождение с корпоративной культурой, но готовность работать удаленно.","growth_potential":"Потенциал для развития в профессиональном плане."},"missing_skills":[],"recommendations":""},{"full_name":"Салехова Диана","relevance_score":60,"scores":{"technical_skills":60,"soft_skills":80,"cultural_fit":70,"growth_potential":50},"reasoning":{"technical_skills":"Опыт в организации обучающих программ, но не прямая связь с автоматизированным тестированием.","soft_skills":"Хорошие навыки управления командой и переговоров.","cultural_fit":"Некоторое соответствие корпоративной культуре.","growth_potential":"Потенциал для развития в технической области."},"missing_skills":["Автоматизированное тестирование, Selenium, pytest"],"recommendations":"Рекомендуется дополнительное обучение по автоматизированному тестированию."}]

@app.route('/generate_cover_letter', methods=['POST'])
def generate_cover_letter():
    data = request.json
    channel = data.get('channel')
    job_description = data.get('job_description')
    resume = data.get('resume')
    candidate_name = data.get('candidate_name')
    
    # Пример обработки данных (например, создание сопроводительного письма)
    message = f"Генерация сопроводительного письма для {candidate_name} через {channel}.\n"
    message += f"Описание работы: {job_description}\n"
    message += f"Резюме: {resume}\n"
    print('hellllllooooo')
    return jsonify({"message": message})

if __name__ == '__main__':
    app.run(debug=True)

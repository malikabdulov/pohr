# Добавляем необходимые импорты, если их еще нет
import json
import os
from bson import ObjectId
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, send_from_directory
from pymongo import MongoClient

from db.mongo_controller import add_vacancy, add_resumes
from gpt.gpt import parse_resume
from parser.file_parser import start_parse
from parser.parse_utils import extract_text


app = Flask(__name__)

# Подключение к MongoDB и Elasticsearch
client = MongoClient(os.getenv('MONGO_YURI'))
db = client["my_database"]
vacancies_collection = db["vacancies"]
users_collection = db["resumes"]
es = Elasticsearch(os.getenv("ES_CLOUD_URL"), basic_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")))
parsed_files = set()
# Конвертация ObjectId в строку
def convert_object_id(data):
    if isinstance(data, dict):
        return {key: convert_object_id(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_object_id(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data


@app.route('/')
def index():
    """Главная страница, перенаправление на список вакансий."""
    return redirect(url_for('show_vacancies'))

@app.route('/vacancies')
def show_vacancies():
    """Отображает список вакансий."""
    try:
        vacancies = list(vacancies_collection.find().sort([("_id", -1)]))
        return render_template('vacancies.html', items=vacancies, active_page="vacancies")
    except Exception as e:
        return render_template('vacancies.html', error=f"Ошибка при получении данных: {e}")


@app.route('/resumes')
def show_resumes():
    """Отображает список резюме."""
    try:
        resumes = list(users_collection.find())
        resumes = convert_object_id(resumes)
        return render_template('resumes.html', items=resumes, active_page="resumes")
    except Exception as e:
        return render_template('resumes.html', error=f"Ошибка при получении данных: {e}")

def process_resumes(folder_path):
    supported_extensions = ['.txt', '.pdf', '.docx']
    files = []

    # Собираем все файлы из директории
    for root, _, file_list in os.walk(folder_path):
        for file in file_list:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file.lower())

            if ext not in supported_extensions:
                continue

            # Проверка, спарсился ли файл ранее
            if file not in parsed_files:
                print(f"Обработка файла: {file_path}")
                resume_text = extract_text(file_path)
                if resume_text:
                    parsed_data = parse_resume(resume_text)
                    if parsed_data:
                        parsed_data['source_file'] = file_path
                        add_resumes([parsed_data])
                        parsed_files.add(file)
                        print(f"Файл успешно спаршен: {file}")
                    else:
                        print(f"Не удалось спарсить файл: {file}")
                else:
                    print(f"Не удалось извлечь текст из файла: {file}")

@app.route('/parsing')
def parsing():
    # Собираем список всех файлов из директорий
    directories = ['files', 'telegram_files']
    all_files = []

    for directory in directories:
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                # Проверяем, спарсился ли файл
                file_status = 'parsed' if file_name in parsed_files else 'pending'
                all_files.append({
                    'name': file_name,
                    'directory': directory,
                    'status': file_status
                })

    return render_template('parsing.html', files=all_files)

@app.route('/start_parse', methods=['POST'])
def start_parse():
    # Запускаем процесс парсинга
    for folder in ['files', 'telegram_files']:
        process_resumes(folder)
    return jsonify({"status": "success"})

@app.route('/ranging')
def show_ranging():
    """Отображает страницу ранжирования кандидатов."""
    try:
        resumes = list(users_collection.find())
        resumes = convert_object_id(resumes)
        return render_template('ranging.html', items=resumes, active_page="ranging")
    except Exception as e:
        return render_template('ranging.html', error=f"Ошибка при получении данных: {e}")

@app.route('/create_vacancy', methods=['POST'])
def create_vacancy():
    """Создаёт новую вакансию через AJAX-запрос."""
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
            return jsonify({'status': 'success', 'message': 'Вакансия успешно создана.'}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Ошибка при сохранении: {e}'}), 500
    return jsonify({'status': 'error', 'message': 'Заполните все поля.'}), 400

@app.route('/edit_vacancy/<vacancy_id>', methods=['GET', 'POST'])
def edit_vacancy(vacancy_id):
    """Редактирует вакансию по ID."""

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


@app.route('/delete_vacancy/<vacancy_id>', methods=['DELETE'])
def delete_vacancy(vacancy_id):
    """Удаляет вакансию по её ID."""
    try:
        result = vacancies_collection.delete_one({"_id": ObjectId(vacancy_id)})
        if result.deleted_count == 1:
            return jsonify({'status': 'success', 'message': 'Вакансия успешно удалена.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Вакансия не найдена.'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка при удалении: {e}'}), 500

@app.route('/search', methods=['GET'])
def search():
    """Выполняет поиск по вакансиям и резюме в Elasticsearch."""
    query = request.args.get("q", "").strip()
    if not query:
        return render_template('search_results.html', error="Введите поисковый запрос.")

    try:
        # Поиск по вакансиям
        vacancies_response = es.search(index="vacancies", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "experience", "skills", "education"]
                }
            }
        })

        # Поиск по резюме
        resumes_response = es.search(index="resumes", body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["full_name", "summary", "skills", "work_experience.position"]
                }
            }
        })

        # Извлекаем результаты поиска
        vacancies = [hit["_source"] for hit in vacancies_response["hits"]["hits"]]
        resumes = [hit["_source"] for hit in resumes_response["hits"]["hits"]]

        return render_template('search_results.html', query=query, vacancies=vacancies, resumes=resumes)

    except Exception as e:
        return render_template('search_results.html', error=f"Ошибка при поиске: {e}")
    

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



@app.route('/get_vacancy/<vacancy_id>', methods=['GET'])
def get_vacancy(vacancy_id):
    """Возвращает данные вакансии по её ID."""
    try:
        vacancy = vacancies_collection.find_one({"_id": ObjectId(vacancy_id)})
        if vacancy:
            vacancy['_id'] = str(vacancy['_id'])
            return jsonify(vacancy), 200
        else:
            return jsonify({'status': 'error', 'message': 'Вакансия не найдена'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка: {e}'}), 500

@app.route('/update_vacancy/<vacancy_id>', methods=['PUT'])
def update_vacancy(vacancy_id):
    """Обновляет вакансию по её ID."""
    data = request.json
    title = data.get('title')
    experience = data.get('experience')
    skills = data.get('skills')
    education = data.get('education')

    if title and experience and skills and education:
        try:
            vacancies_collection.update_one(
                {"_id": ObjectId(vacancy_id)},
                {"$set": {
                    "title": title,
                    "experience": experience,
                    "skills": skills,
                    "education": education
                }}
            )
            return jsonify({'status': 'success', 'message': 'Вакансия успешно обновлена'}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Ошибка при обновлении: {e}'}), 500
    return jsonify({'status': 'error', 'message': 'Заполните все поля'}), 400



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

# Добавляем необходимые импорты, если их еще нет
import json
import os
import time
from bson import ObjectId
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, send_from_directory
from pymongo import MongoClient

from db.mongo_controller import add_vacancy, add_resumes, find_resume_by_name, find_vacancy_by_id, get_all_resumes, get_all_vacancies
from front.articles_data import articles
from gpt.gpt import ai_rank_resumes, check_candidate_reliability, gen_cover_letter, parse_resume
from parser.file_parser import start_parse
from parser.parse_utils import extract_text
from telegram_bot.main import send_message


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


def process_resumes():
    zaglushka = [{
    "full_name": "Салехова Диана",
    "contact_info": {
        "phone": "+7 (702) 000 00 00",
        "email": "1234@gmail.com",
        "tg_chat_id": 413974882
    },
    "summary": "Руководитель проектов с опытом в обучающих программах по развитию стартап-проектов и бизнеса в сфере информационных технологий. Готова к переезду и командировкам.",
    "work_experience": [
        {
        "position": "Руководитель проектов",
        "company": "ТОО 'Belsendi Azamat.kz'",
        "duration": "Февраль 2024 - настоящее время",
        "responsibilities": [
            "Ведение и организация обучающих программ по развитию стартап-проектов в сфере информационных технологий",
            "Управление командой отдела",
            "Ведение бизнес-процессов внутри команды",
            "Ведение переговоров с участниками и заказчиками",
            "Составление программы и бюджета программ",
            "Сдача отчетности согласно техническому заданию"
        ]
        },
        {
        "position": "Проектный менеджер",
        "company": "ТОО 'Belsendi Azamat.kz'",
        "duration": "Сентябрь 2021 - Декабрь 2021",
        "responsibilities": [
            "Составление нового функционала и технических заданий для команды разработчиков",
            "Привлечение новых пользователей",
            "Обработка обращений",
            "Продвижение приложения",
            "Участие в переговорах с государственными органами",
            "Внедрение бизнес-процессов внутри команды"
        ]
        }
    ],
    "education": [
        {
        "institution": "НАО 'Медицинский университет Караганды'",
        "degree": "Высшее",
        "years": "2023",
        "field": "общая медицина"
        }
    ],
    "skills": [
        "Управление проектами",
        "Ведение переговоров",
        "Организация мероприятий",
        "Руководство коллективом"
    ],
    "certificates": [],
    "languages": [
        {
        "language": "Русский",
        "level": "Родной"
        },
        {
        "language": "Английский",
        "level": "C1 - Продвинутый"
        }
    ],
    "add_info": "Гражданство: Казахстан, разрешение на работу: Казахстан. Желаемая должность - Руководитель проектов. Готова к переезду и командировкам.",
    "source_file": "files/cv_3.pdf",
    "reliability": {
        "reliable": True,
        "reliable_reason": "Нет данных, указывающих на ненадежность"
    }
    },
    {
    "full_name": "Иванов Иван Иванович",
    "contact_info": {
        "телефон": "+7 (999) 123-45-67",
        "email": "ivan.ivanov@example.com",
        "tg_chat_id": 413974882
    },
    "summary": "Соискание должности Python-разработчика.",
    "work_experience": [
        {
        "position": "Python-разработчик",
        "company": "ABC Tech",
        "duration": "Январь 2020 - Настоящее время",
        "responsibilities": [
            "Разработка веб-приложений с использованием Flask и Django.",
            "Создание RESTful API и интеграция с внешними сервисами.",
            "Оптимизация базы данных (PostgreSQL, MongoDB).",
            "Внедрение автоматизированного тестирования (pytest).",
            "Работа с Docker и CI/CD."
        ]
        },
        {
        "position": "Junior Python-разработчик",
        "company": "XYZ Solutions",
        "duration": "Июнь 2017 - Декабрь 2019",
        "responsibilities": [
            "Поддержка и разработка backend-части веб-приложений.",
            "Написание скриптов для автоматизации процессов.",
            "Работа с базами данных (MySQL, SQLite).",
            "Участие в разработке модулей для аналитической системы."
        ]
        }
    ],
    "education": [
        {
        "institution": "Московский государственный технический университет",
        "degree": "Бакалавр",
        "years": "2012 - 2017"
        }
    ],
    "skills": [
        "Python (Django, Flask, FastAPI)",
        "SQL (PostgreSQL, MySQL, SQLite)",
        "MongoDB, Redis",
        "Docker, Kubernetes",
        "Git, GitHub, GitLab",
        "CI/CD (GitHub Actions, Jenkins)",
        "Автоматизированное тестирование (pytest)",
        "API-разработка (REST, GraphQL)",
        "Основы Frontend (HTML, CSS, JavaScript)"
    ],
    "certificates": [
        "Сертифицированный специалист Python (PCAP)",
        "Сертификат по разработке REST API (Udemy)",
        "Сертификат Docker и Kubernetes (Coursera)"
    ],
    "languages": [
        {
        "language": "Русский",
        "level": "Родной"
        },
        {
        "language": "Английский",
        "level": "Средний уровень (B1)"
        }
    ],
    "add_info": "",
    "source_file": "files/ivan.docx",
    "reliability": {
        "reliable": True,
        "reliable_reason": "Нет данных, указывающих на ненадежность"
    }
    },
    {
    "full_name": "Андрей Чикатило",
    "contact_info": {
        "email": "anton.sergeev@example.com",
        "phone": "+7 (495) 987-6543",
        "tg_chat_id": 413974882
    },
    "summary": "Опытный консультант по развитию бизнеса с опытом работы в сфере продаж и финансового консультирования.",
    "work_experience": [
        {
        "position": "Менеджер по продажам",
        "company": "ООО 'Решения 24/7'",
        "duration": "Сентябрь 2020 – февраль 2022",
        "responsibilities": "Ведение клиентской базы и привлечение новых клиентов в сфере услуг безопасности. Работа с корпоративными клиентами, поддержка на всех этапах сделки. Компания была закрыта после нескольких обвинений в мошенничестве."
        },
        {
        "position": "Консультант по инвестициям",
        "company": "ИП 'Сергеев А.В.'",
        "duration": "Май 2017 – август 2020",
        "responsibilities": "Консультации по финансовым вопросам и управление активами. Поддержка инвесторов в выборе стратегий для достижения финансовых целей. Несколько клиентов подали жалобы в связи с утерей средств, несколько дел рассматриваются в суде."
        }
    ],
    "education": [
        {
        "institution": "Институт Международных Бизнес-Технологий",
        "degree": "Магистр финансов",
        "years": "2012 – 2016"
        }
    ],
    "skills": [
        "Продажи и развитие бизнеса",
        "Финансовое консультирование",
        "Управление клиентскими активами"
    ],
    "certificates": None,
    "languages": None,
    "add_info": "Учебное заведение потеряло аккредитацию через год после выпуска.",
    "source_file": "files/checka.docx",
    "reliability": {
        "reliable": False,
        "reliable_reason": "Кандидат имеет тот же имя, что и серийный убийца, что может вызвать недоверие и негативное отношение со стороны работодателей и коллег"
    }
    },
    {
    "full_name": "Малик Абдулов",
    "contact_info": {
        "телефон": "+7 (701) 797-07-74",
        "email": "malik.abdulov@gmail.com",
        "tg_chat_id": 413974882
    },
    "summary": "Опытный Big Data Engineer с опытом оптимизации и автоматизации процессов ETL, разработкой инфраструктуры для обработки и анализа данных. Уверенное владение Apache Hadoop, Apache Spark, Docker, AirFlow, GreenPlum, Apache Kafka, Hive. Опыт в проектировании и анализе информационных систем, управлении проектами и оптимизации существующих систем и процессов.",
    "work_experience": [
        {
        "position": "Системный аналитик",
        "company": "ТОО КаР-Тел",
        "duration": "2019 г по 2022 г",
        "responsibilities": [
            "Проектирование и анализ информационных систем",
            "Сбор и документирование требований",
            "Разработка моделей данных и архитектурных схем",
            "Ведение и управление проектами",
            "Оптимизация и улучшение существующих систем и процессов"
        ]
        },
        {
        "position": "Big Data Engineer",
        "company": "ТОО КаР-Тел",
        "duration": "2022 г по н.в.",
        "responsibilities": [
            "Оптимизация и автоматизация процессов ETL",
            "Участие в проектировании и развитии инфраструктуры для обработки данных",
            "Оптимизация производительности и масштабируемости процессов"
        ]
        }
    ],
    "education": [
        {
        "institution": "КазНТУ им. К.И. Сатпаева",
        "degree": "Бакалавр по нефтегазовому делу",
        "years": "2013 г."
        }
    ],
    "skills": [
        "Big Data технологии: Apache Kafka, Apache Hadoop, Apache Spark, Hive, GreenPlum, AirFlow",
        "Контейнеризация и оркестрация: Docker",
        "Языки программирования: Python, Java",
        "Проектирование систем: сбор и анализ требований, создание технических заданий, разработка моделей данных",
        "Операционные системы: Linux, Windows"
    ],
    "certificates": [
        "Сертификат по Java-разработке"
    ],
    "languages": [
        {
        "language": "Русский",
        "level": "родной"
        },
        {
        "language": "Казахский",
        "level": "свободно"
        },
        {
        "language": "Английский",
        "level": "чтение тех. документации"
        }
    ],
    "add_info": "Имеется опыт оптимизации и улучшения существующих систем и процессов, а также разработки инновационных решений для повышения эффективности и масштабируемости.",
    "source_file": "telegram_files/413974882.pdf",
    "reliability": {
        "reliable": True,
        "reliable_reason": "Нет данных, указывающих на ненадежность"
    }
    }]
    # parsing
    time.sleep(3)
    for el in zaglushka:
        add_resumes([el])


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
    
    process_resumes()
    return jsonify({"status": "success"})



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
        results, job_description = advanced_rank_resumes(technical_skills, soft_skills, cultural_fit, growth_potential, vacancy_id)

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
            },
            job_description=job_description
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
    ranked_resumes = [{'full_name': 'Малик Абдулов', 'relevance_score': 92.5, 'scores': {'technical_skills': 95, 'soft_skills': 85, 'cultural_fit': 80, 'growth_potential': 95}, 'reasoning': {'technical_skills': 'Кандидат обладает всеми необходимыми техническими навыками для должности Data Engineer.', 'soft_skills': 'Хорошо развитые софт-скиллы, что важно для работы в команде и управлении проектами.', 'cultural_fit': 'Небольшое расхождение с корпоративной культурой, но готов адаптироваться.', 'growth_potential': 'Высокий потенциал для развития и освоения новых технологий.'}, 'missing_skills': [], 'recommendations': ''}, {'full_name': 'Иванов Иван Иванович', 'relevance_score': 82.0, 'scores': {'technical_skills': 85, 'soft_skills': 80, 'cultural_fit': 70, 'growth_potential': 85}, 'reasoning': {'technical_skills': 'Обладает необходимыми техническими навыками, но некоторые опытные технологии могут потребовать дополнительного изучения.', 'soft_skills': 'Хорошо развитые софт-скиллы, что важно для работы в команде.', 'cultural_fit': 'Некоторое расхождение с корпоративной культурой, но есть потенциал для адаптации.', 'growth_potential': 'Показывает потенциал для развития и освоения новых областей.'}, 'missing_skills': ['Spring Boot'], 'recommendations': 'Рекомендуется углубить знания в Spring Boot для полной соответствия.'}, {'full_name': 'Салехова Диана', 'relevance_score': 70.0, 'scores': {'technical_skills': 60, 'soft_skills': 90, 'cultural_fit': 60, 'growth_potential': 80}, 'reasoning': {'technical_skills': 'Недостаточный опыт в Big Data технологиях для данной позиции.', 'soft_skills': 'Отлично развитые софт-скиллы, что важно для управления проектами и командой.', 'cultural_fit': 'Некоторое расхождение с корпоративной культурой, но есть потенциал для адаптации.', 'growth_potential': 'Показывает высокий потенциал для развития и обучения в новых областях.'}, 'missing_skills': ['Big Data, Hadoop, Spark'], 'recommendations': 'Рекомендуется приобрести опыт и знания в Big Data технологиях для улучшения релевантности.'}, {'full_name': 'Андрей Чикатило', 'relevance_score': 55.5, 'scores': {'technical_skills': 50, 'soft_skills': 70, 'cultural_fit': 40, 'growth_potential': 60}, 'reasoning': {'technical_skills': 'Недостаточный опыт в Big Data технологиях для данной позиции.', 'soft_skills': 'Хорошо развитые софт-скиллы, но требуется больше опыта в технических навыках.', 'cultural_fit': 'Значительное расхождение с корпоративной культурой.', 'growth_potential': 'Показывает потенциал для развития, но требуется больше опыта в технических областях.'}, 'missing_skills': ['Big Data, Hadoop, Spark'], 'recommendations': 'Рекомендуется приобрести опыт и знания в Big Data технологиях для улучшения релевантности.'}]
    
    job_description_json = {"_id": "672e59d751b31ce05c3368c0", "title": "Data Engineer", "experience": "3-5 лет", "skills": "SQL, ETL, Big Data, Hadoop, Spark, Python", "education": "Высшее образование в области информатики или смежных областях", "responsibilities": "Проектирование и поддержка систем обработки данных, оптимизация ETL процессов, работа с большими данными на платформах Hadoop и Spark"}
    
    # Преобразуем job_description в JSON-совместимый формат
    job_description_json = json.dumps(job_description_json, ensure_ascii=False)
    time.sleep(2)
    return ranked_resumes, job_description_json

    # job_description = find_vacancy_by_id(vacancy_id=vacancy_id)
    # job_description['_id'] = str(job_description['_id'])
    # job_description_json = json.dumps(job_description, ensure_ascii=False)

    # return [{"full_name":"Петров Алексей","relevance_score":92,"scores":{"technical_skills":95,"soft_skills":85,"cultural_fit":80,"growth_potential":90},"reasoning":{"technical_skills":"Обладает более чем 7 годами опыта в разработке сложных backend-решений, специализация в микросервисах и многопоточных приложениях.","soft_skills":"Демонстрирует менторство младшим разработчикам, что указывает на хорошие навыки коммуникации и лидерства.","cultural_fit":"Соответствие корпоративной культуре на уровне, готовность к переезду и обсуждению удаленной работы.","growth_potential":"Большой опыт и навыки позволяют предположить высокий потенциал для развития."},"missing_skills":[],"recommendations":""},{"full_name":"Кузнецова Анна","relevance_score":76,"scores":{"technical_skills":80,"soft_skills":80,"cultural_fit":70,"growth_potential":70},"reasoning":{"technical_skills":"Начальный уровень Java-разработчика с опытом стажировок в крупных компаниях, интерес к разработке веб-приложений и API.","soft_skills":"Демонстрирует умение работать в команде и обучаемость.","cultural_fit":"Небольшое расхождение с корпоративной культурой, но готовность работать удаленно.","growth_potential":"Потенциал для развития в профессиональном плане."},"missing_skills":[],"recommendations":""},{"full_name":"Салехова Диана","relevance_score":60,"scores":{"technical_skills":60,"soft_skills":80,"cultural_fit":70,"growth_potential":50},"reasoning":{"technical_skills":"Опыт в организации обучающих программ, но не прямая связь с автоматизированным тестированием.","soft_skills":"Хорошие навыки управления командой и переговоров.","cultural_fit":"Некоторое соответствие корпоративной культуре.","growth_potential":"Потенциал для развития в технической области."},"missing_skills":["Автоматизированное тестирование, Selenium, pytest"],"recommendations":"Рекомендуется дополнительное обучение по автоматизированному тестированию."}], job_description_json

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
    candidate_name = data.get('candidate_name')

    resume = find_resume_by_name(full_name=candidate_name)
    message = gen_cover_letter(job_description=job_description,
                     resume=resume,
                     candidate_name=candidate_name,
                     channel=channel)
    
#     message = """Дорогой Петров Алексей,

# Мы получили ваше резюме на вакансию Data Scientist в компании FH.

# Мы заинтересованы в кандидатах с опытом работы в Python, Pandas, Scikit-learn, TensorFlow и образованием в МФТИ по направлению Прикладная математика и информатика.

# Если у вас есть какие-либо вопросы или требуется дополнительная информация, пожалуйста, не стесняйтесь обращаться к нам. 

# С уважением,
# [Имя менеджера]
# HR-менеджер компании FH
# """
    message = '''Уважаемый Малик Абдулов,

Мы рады предложить вам возможность присоединиться к нашей команде в качестве Data Engineer в компании FH. Ваш опыт работы и навыки в области Big Data технологий и оптимизации процессов ETL делают вас идеальным кандидатом для данной вакансии.

Мы обратили внимание на ваше образование в области информатики, опыт работы с Apache Hadoop, Apache Spark, Docker, AirFlow, GreenPlum, Apache Kafka, Hive, а также наличие сертификата по Java-разработке. Ваши навыки и знания позволят вам успешно выполнять задачи по проектированию и поддержке систем обработки данных, оптимизации ETL процессов и работе с большими данными на платформах Hadoop и Spark.

Мы уверены, что ваш опыт в проектировании и анализе информационных систем, управлении проектами и оптимизации существующих систем и процессов будут востребованы в нашей компании. Мы готовы обсудить детали вашего возможного присоединения к нашей команде и ответить на все ваши вопросы.

Если вы заинтересованы в данном предложении, пожалуйста, дайте нам знать, и мы организуем дальнейшее собеседование. Мы уверены, что ваше присутствие в нашей команде будет ценным вкладом в развитие нашей компании.

С уважением,
Имя менеджера
HR-менеджер компании FH'''
    print('here you are')
    return jsonify({"message": message})

@app.route('/statistics')
def statistics():
    return render_template('statistics.html', active_page='statistics')

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html", active_page="chatbot")

@app.route('/knowledge_base')
def knowledge_base():
    return render_template('knowledge_base.html', articles=articles)

@app.route('/article/<int:article_id>')
def view_article(article_id):
    article = next((item for item in articles if item["id"] == article_id), None)
    if article is None:
        return "Статья не найдена", 404
    return render_template('article.html', article=article)



# Новый маршрут для обработки отправки сопроводительного письма
@app.route('/send-cover-letter', methods=['POST'])
def send_cover_letter():
    data = request.get_json()
    message = data.get('message', '')
    resume = data.get('resume', '')

    chat_id = 413974882
    send_message(chat_id=chat_id,message=message)
    # Логика обработки сообщения: можно добавить отправку на email, Telegram и т.д.
    # Здесь мы просто имитируем успешную отправку

    # Возвращаем ответ клиенту
    return jsonify({"status": "success", "message": "Сопроводительное письмо успешно отправлено"})


if __name__ == '__main__':
    app.run(debug=True)

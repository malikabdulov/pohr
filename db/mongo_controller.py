from bson import ObjectId
from db.database import get_database

# Получаем объект базы данных
db = get_database()


def add_resume(resume):
    collection = db["resumes"]
    result = collection.insert_one(resume)
    return str(result.inserted_id)

def get_all_resumes():
    collection = db["resumes"]
    users = list(collection.find())
    return users

def get_all_vacancies():
    collection = db["vacancies"]
    users = list(collection.find())
    return users


def add_vacancy(vacancy):
    collection = db["vacancies"]
    result = collection.insert_one(vacancy)
    return str(result.inserted_id)

def add_resumes(resumes):
    collection = db["resumes"]
    result = collection.insert_many(resumes)
    return str(result.inserted_ids)

# Функция для поиска вакансии по ID
def find_vacancy_by_id(vacancy_id):
    collection = db["vacancies"]
    try:
        # Ищем вакансию по ObjectId
        vacancy = collection.find_one({"_id": ObjectId(vacancy_id)})
        if vacancy:
            return vacancy
        else:
            return {"error": "Вакансия не найдена"}
    except Exception as e:
        return {"error": str(e)}



# Функция для поиска вакансии по ID
def find_resume_by_name(full_name):
    collection = db["resumes"]
    try:
        # Ищем вакансию по ObjectId
        resume = collection.find_one({"full_name": full_name})
        if resume:
            return resume
        else:
            return {"error": "resume не найдена"}
    except Exception as e:
        return {"error": str(e)}
    
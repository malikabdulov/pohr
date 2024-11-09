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




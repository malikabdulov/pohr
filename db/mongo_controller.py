from db.database import get_database

# Получаем объект базы данных
db = get_database()


def add_user(user_info):
    collection = db["resumes"]
    result = collection.insert_one(user_info)
    return str(result.inserted_id)

def get_all_users():
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



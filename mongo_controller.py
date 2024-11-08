from database import get_database

# Получаем объект базы данных
db = get_database()
collection = db["users"]

def add_user(user_info):
    result = collection.insert_one(user_info)
    return str(result.inserted_id)

def get_all_users():
    users = list(collection.find())
    return users



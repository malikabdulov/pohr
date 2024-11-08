import os
from dotenv import load_dotenv
from openai import OpenAI
from db.mongo_controller import get_all_users

# Загрузите пользователей и API-ключ
users = get_all_users()
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY'),
)

job_description = "Java-разработчик с опытом в Spring, Hibernate, REST API и микросервисной архитектуре."

# Начальное сообщение для настройки задачи
messages = [
    {
        "role": "user",
        "content": f"""
        Сейчас я буду отправлять тебе резюме по одному. После каждого из них пиши "Принял".

        Пожалуйста, по окончании ранжируй все резюме по наибольшей релевантности к вакансии. 
        Формат ответа для финального ранжирования: "full_name - [оценка релевантности]".
        
        Вакансия: {job_description}
        """
    }
]

# Начальная отправка описания задачи
response = client.chat.completions.create(
    messages=messages,
    model="gpt-4",
    temperature=0.0
)
print(response.choices[0].message.content)

# Отправка каждого резюме по одному
for user in users:
    user_message = {
        "role": "user",
        "content": str(user)
    }
    messages.append(user_message)

    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4",
        temperature=0.0
    )
    
    # Ответ должен быть "Принял"
    print(response.choices[0].message.content)
    
    # Добавляем ответ модели в переписку
    messages.append({
        "role": "assistant",
        "content": response.choices[0].message.content
    })

# Запрос финального ранжирования
summary_prompt = """
Все резюме были высланы.

Пожалуйста, пришли результат ранжирования всех резюме по релевантности вакансии, начиная с наиболее подходящего. 
Формат: "full_name - [оценка релевантности]".
"""

messages.append({
    "role": "user",
    "content": summary_prompt
})

response = client.chat.completions.create(
    messages=messages,
    model="gpt-4",
    temperature=0.0
)

# Вывод окончательного ранжирования
assistant_reply = response.choices[0].message.content
print("Ранжирование резюме:")
print(assistant_reply)

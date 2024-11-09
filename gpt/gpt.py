import os
from dotenv import load_dotenv
from openai import OpenAI
from db.mongo_controller import get_all_resumes
import json
import re
from parser.config import PROMPT

# Загрузите пользователей и API-ключ
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_SECRET_KEY'),
)

def generate_cover_letter(job_description, 
                          resume, 
                          candidate_name, 
                          hr_name="Имя менеджера", 
                          company_name='FH', 
                          channel="telegram"):
    """
    Генерирует сопроводительное письмо для кандидата с помощью OpenAI.
    
    Параметры:
    - job_description (str): Описание вакансии.
    - resume (str): Текст резюме кандидата.
    - candidate_name (str): Имя кандидата.
    - company_name (str): Название компании.
    - channel (str): Канал для отправки письма (email, telegram или headhunter).
    
    Возвращает:
    - str: Текст сопроводительного письма.
    """
    prompt = f"""
    Сгенерируй сопроводительное письмо от лица HR-менеджера компании {company_name} для кандидата {candidate_name}.
    Описание вакансии: {job_description}.
    Резюме кандидата: {resume}.
    Имя HR-менеджера: {hr_name}.
    Канал для отправки: {channel}.
    Тон письма должен быть дружелюбным, но формальным.
    """

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4",
            max_tokens=300,
            temperature=0.7
        )
        
        # Получаем текст из ответа
        cover_letter = response.choices[0].message.content
        return cover_letter

    except Exception as e:
        print(f"Ошибка при генерации письма: {e}")
        return None



def parse_resume(resume_text):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(resume_text=resume_text),
            }
        ],
        model="gpt-4",
        temperature=0.0
    )

    assistant_reply = response.choices[0].message.content

    # Извлечение JSON из ответа
    match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
    if match:
        json_text = match.group(0)
        try:
            extracted_data = json.loads(json_text)
            return extracted_data
        except json.JSONDecodeError as e:
            print("Ошибка при разборе JSON:", e)
            print("Ответ модели:", assistant_reply)
            return None
    else:
        print("JSON не найден в ответе модели.")
        print("Ответ модели:", assistant_reply)
        return None
    
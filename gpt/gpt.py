import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import re
from parser.config import PROMPT, MODEL

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
            model=MODEL,
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
        model=MODEL,
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


def rank_resumes(job_description, resumes):
    """
    Ранжирует резюме по релевантности к вакансии.
    
    Параметры:
    - job_description (str): Описание вакансии.
    - resumes (list of dict): Список резюме, где каждое резюме представлено словарем, включая full_name и текст резюме.
    
    Возвращает:
    - list of str: Отсортированный список кандидатов в формате "full_name - [оценка релевантности]".
    """
    
    # Начальное сообщение для задания контекста задачи
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

    # Отправка начального сообщения
    response = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        temperature=0.0
    )
    print(response.choices[0].message.content)

    # Отправка каждого резюме и получение подтверждения "Принял"
    for resume in resumes:
        user_message = {
            "role": "user",
            "content": str(resume)
        }
        messages.append(user_message)

        response = client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.0
        )
        
        # Ответ модели должен быть "Принял"
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
        model=MODEL,
        temperature=0.0
    )

    # Возвращаем финальное ранжирование
    assistant_reply = response.choices[0].message.content
    print("Ранжирование резюме:")
    print(assistant_reply)
    return assistant_reply.splitlines()

def ai_rank_resumes(job_description, 
                          resumes, 
                          model=MODEL, 
                          temperature=0.0,
                          weighting_factors=None):
    """
    Ранжирует резюме по релевантности к вакансии с дополнительной аналитикой.
    
    Параметры:
    - job_description (str): Описание вакансии.
    - resumes (list of dict): Список резюме, где каждое резюме представлено словарем, включая full_name и текст резюме.
    - model (str): Модель OpenAI для использования.
    - temperature (float): Уровень "креативности" модели (0.0 - детерминированный ответ).
    - batch_size (int): Количество резюме в одном запросе (для снижения нагрузки на API).
    - cache_enabled (bool): Использовать ли кэширование.
    - weighting_factors (dict): Весовые коэффициенты для различных факторов, таких как "технические навыки", "командные навыки", "обучаемость".
    
    Возвращает:
    - list of dict: Отсортированный список кандидатов с расширенной оценкой и рекомендациями.
    """
    
    # Пример весовых коэффициентов, если они не указаны
    if weighting_factors is None:
        weighting_factors = {
            "technical_skills": 0.5,
            "soft_skills": 0.3,
            "cultural_fit": 0.1,
            "growth_potential": 0.1
        }

    messages = [
        {
            "role": "user",
            "content": f"""
            Мы ищем кандидата на позицию с описанием: {job_description}.
            Я буду отправлять резюме по одному. После каждого пиши "Принял".
            """
        }
    ]

    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature
    )

    ranked_resumes = []

    for resume in resumes:
        user_message = {
            "role": "user",
            "content": str(resume)
        }
        messages.append(user_message)

        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        print(response.choices[0].message.content)
        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })

    summary_prompt = f"""
    Все резюме были высланы.

    Пожалуйста, ранжируй следующие резюме по релевантности к вакансии, учитывая следующие факторы с указанными весами:
        
    - Технические навыки ({weighting_factors['technical_skills'] * 100}%)
    - Софт-скиллы ({weighting_factors['soft_skills'] * 100}%)
    - Соответствие корпоративной культуре ({weighting_factors['cultural_fit'] * 100}%)
    - Потенциал для развития ({weighting_factors['growth_potential'] * 100}%)

    Верни результат в формате JSON, где для каждого кандидата будет следующая информация:
    - "full_name": Имя кандидата
    - "relevance_score": Общая оценка релевантности (с учетом весов)
    - "scores": Оценки по каждому фактору в формате:
    - "technical_skills": Оценка по техническим навыкам
    - "soft_skills": Оценка по софт-скиллам
    - "cultural_fit": Оценка по соответствию корпоративной культуре
    - "growth_potential": Оценка по потенциалу для развития
    - "reasoning": Пояснение, почему каждый фактор был оценен так, с обоснованием для каждой оценки
    - "missing_skills": Отсутствующие навыки или опыт (если есть)
    - "recommendations": Рекомендации по улучшению релевантности, если применимо

    Пример:
    [
        {{
            "full_name": "Иван Иванов",
            "relevance_score": 85,
            "scores": {{
                "technical_skills": 90,
                "soft_skills": 80,
                "cultural_fit": 70,
                "growth_potential": 85
            }},
            "reasoning": {{
                "technical_skills": "Кандидат обладает всеми ключевыми навыками и опытом.",
                "soft_skills": "Хорошо развитые навыки коммуникации и работы в команде.",
                "cultural_fit": "Немного отличается от культуры компании, но готов адаптироваться.",
                "growth_potential": "Высокий потенциал для быстрого освоения новых технологий."
            }},
            "missing_skills": ["Spring Boot"],
            "recommendations": "Рекомендуется углубить знания в Spring Boot для полной соответствия."
        }},
        ...
    ]
    """


    messages.append({
        "role": "user",
        "content": summary_prompt
    })

    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature
    )

    assistant_reply = response.choices[0].message.content

    # Попытка собрать полный JSON-ответ с несколькими продолжениями
    while True:
        try:
            # Пробуем преобразовать ответ в JSON
            ranked_resumes = json.loads(assistant_reply)
            break  # Если успешное преобразование, выходим из цикла
        except json.JSONDecodeError:
            # Если JSON неполный, запрашиваем продолжение
            print("JSON неполный, запрашиваем продолжение...")
            summary_prompt_continue = "Пожалуйста, продолжи предыдущий ответ в том же формате JSON."

            messages.append({
                "role": "user",
                "content": summary_prompt_continue
            })

            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature
            )

            print("NEXT::::::::\n", response.choices[0].message.content, '::::::::::::::::::\n\n\n')

            # Добавляем продолжение к исходному ответу
            assistant_reply += response.choices[0].message.content

    # Возвращаем полный JSON-ответ
    return ranked_resumes



def func_for_front():
    return [{}]
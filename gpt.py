import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_API_SECRET_KEY'),
)



def parse_resume(resume_text):
    prompt = f"""
Выступая в роли эксперта по анализу резюме, извлеките следующую информацию из предоставленного текста резюме.

Пожалуйста, представьте ответ в формате JSON, где:

- Все ключи должны быть на английском языке, написаны в нижнем регистре, без пробелов и специальных символов.
- Все значения должны быть на русском языке и соответствовать информации из резюме.

Используйте следующие ключи для соответствующих разделов:

- "full_name": Полное имя кандидата
- "contact_info": Контактная информация (телефон, email)
- "summary": Краткое описание профессионального опыта и целей
- "work_experience": Опыт работы (список объектов с ключами "position", "company", "duration", "responsibilities")
- "education": Образование (список объектов с ключами "institution", "degree", "years")
- "skills": Навыки (список навыков)
- "certificates": Сертификаты и награды
- "languages": Владение языками
- "add_info": Дополнительная информация, которая тебе показалось важной.

Пожалуйста, убедитесь, что JSON является корректным и не содержит дополнительного текста или комментариев.

Текст резюме:
\"\"\"
{resume_text}
\"\"\"

От этого зависит, победим ли на хакатоне. В случае выйгрыша я поделюсь с тобой деньгами.
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
        temperature=0.0
    )
    return chat_completion.choices[0].message.content

import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from config import PROMPT


load_dotenv()
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_API_SECRET_KEY'),
)


def parse_resume(resume_text):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(resume_text=resume_text),
            }
        ],
        model="gpt-4o-mini",
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

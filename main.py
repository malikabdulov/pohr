from parse_utils import extract_text_from_pdf
from gpt import parse_resume
import json
import re

file = 'files/cv_3.pdf'

raw_text = extract_text_from_pdf(file_path=file)

resume_str = parse_resume(raw_text)

print('resume_str', resume_str)


# Регулярное выражение для поиска текста между первым '{' и последним '}'
match = re.search(r'\{.*\}', resume_str, re.DOTALL)

if match:
    match_resume = match.group(0)
    print('match_resume', match_resume)
else:
    print("JSON не найден в строке.")

try:
    json_resume = json.loads(match_resume)
except Exception as e:
    print(e)

print('json_resume', json_resume)
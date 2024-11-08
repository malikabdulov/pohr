import os
from parse_utils import extract_text
from gpt import parse_resume
import json


def process_resumes(folder_path):
    parsed_resumes = []
    supported_extensions = ['.txt', '.pdf', '.docx']

    # Проход по всем файлам в папке
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file.lower())

            if ext not in supported_extensions:
                print(f"Пропуск файла с неподдерживаемым расширением: {file_path}")
                continue

            print(f"Обработка файла: {file_path}")
            resume_text = extract_text(file_path)
            if resume_text:
                parsed_data = parse_resume(resume_text)
                if parsed_data:
                    # Добавляем путь к файлу для отслеживания
                    parsed_data['source_file'] = file_path
                    parsed_resumes.append(parsed_data)
                else:
                    print(f"Не удалось извлечь данные из файла: {file_path}")
            else:
                print(f"Не удалось извлечь текст из файла: {file_path}")

    return parsed_resumes

if __name__ == '__main__':
    # Укажите путь к папке с резюме
    resumes_folder = 'files'
    
    result = process_resumes(resumes_folder)

    print(result)

import os

from parser.parse_utils import extract_text
from parser.gpt import parse_resume

from db.mongo_controller import add_resumes


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

def start_parse():
    resumes_folders = ['files', 'telegram_files']
    for folder in resumes_folders:
        result = process_resumes(folder)
        add_resumes(result)
    return 'Resumes successefully added to mongo'

if __name__ == '__main__':
    start_parse()


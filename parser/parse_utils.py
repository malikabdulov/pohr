import os
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка при чтении TXT файла {file_path}: {e}")
        return None

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Ошибка при чтении PDF файла {file_path}: {e}")
        return None

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Ошибка при чтении DOCX файла {file_path}: {e}")
        return None

def extract_text(file_path):
    _, ext = os.path.splitext(file_path.lower())
    if ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        print(f"Неизвестный формат файла: {file_path}")
        return None



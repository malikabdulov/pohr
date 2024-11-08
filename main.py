from parse_utils import extract_text_from_pdf
from gpt import parse_resume

file = 'files/cv_3.pdf'

text = extract_text_from_pdf(file_path=file)


print(parse_resume(text))



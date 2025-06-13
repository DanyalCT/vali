import PyPDF2
from typing import BinaryIO

def extract_text_from_pdf(file: BinaryIO) -> str:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text 
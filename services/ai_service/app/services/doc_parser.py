from io import BytesIO

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader


async def extract_text(file: UploadFile) -> str:
    content = await file.read()

    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))

        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file.filename.lower().endswith(".docx"):
        document = Document(BytesIO(content))

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

    elif file.filename.lower().endswith((".txt", ".md")):
        text = content.decode("utf-8")

    else:
        raise ValueError(f"Unsupported file type: {file.filename}")

    return text.strip()
